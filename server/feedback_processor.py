import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from fpdf import FPDF
import os, zipfile, json, re, textwrap
from io import BytesIO
from pymongo import MongoClient
import gridfs

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # Update with your MongoDB connection string
db = client['feedback_db']
charts_collection = db['charts']
fs_charts = gridfs.GridFS(db, collection='charts')

try:
    # Attempt to configure from environment variable first
    if 'GEMINI_API_KEY' in os.environ:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    else:
        # Fallback for local testing - replace with your key
        genai.configure(api_key="AIzaSyChRdH4CqkQF_4JC9IMBNptsXDw0JLMBrA")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    print(f"Could not configure Gemini. AI features will fail. Error: {e}")
    model = None

# gemini
def detect_likert_categories_with_gemini(df):
    if not model: return {}
    sample = df.sample(min(5, len(df))).to_string(index=False)
    prompt = f"""
You are a helpful assistant.
Given this sample from a feedback form, identify Likert-scale (1 to 5) rating questions.
Group them into logical categories like 'Curriculum', 'Faculty', 'Facilities', etc.
Return a valid Python dictionary in JSON format like:
{{ "Question column name": "Category name" }}
Sample data:
{sample}
"""
    try:
        response = model.generate_content(prompt)
        result_text = re.sub(r"^```(?:json|python)?|```$", "", response.text.strip())
        return json.loads(result_text)
    except Exception as e:
        print(f"Gemini failed: {e}")
        return {}

def extract_bracket_content(text):
    if pd.isna(text): return text
    match = re.search(r'\[([^\]]+)\]', str(text))
    return match.group(1) if match else str(text)

def extract_category_name(text):
    if pd.isna(text): return text
    match = re.search(r'^([^\[]+)', str(text).strip())
    return match.group(1).strip() if match else str(text)

def group_columns_by_category(df):
    category_groups = {}
    for col in df.columns:
        if '[' in str(col) and ']' in str(col):
            category = extract_category_name(col)
            category_groups.setdefault(category, []).append(col)
        else:
            category_groups[str(col)] = [col]
    return category_groups

def summarize_suggestions_with_gemini(df, column_name):
    if not model: return "Summary could not be generated (AI model not configured)."
    suggestions = df[column_name].dropna().astype(str)
    if suggestions.empty:
        return "No suggestions provided."
    combined_text = "\n".join(suggestions.tolist()[:50])
    prompt = f"""
You are a helpful assistant.
Given the following feedback suggestions from a student feedback form, write a grammatically correct, concise, and insightful summary.
Feedback suggestions:
{combined_text}
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
        return "Summary could not be generated."

def detect_likert_categories_with_gemini_subject(df):
    if not model: return {}
    sample = df.sample(min(5, len(df))).to_string(index=False)
    prompt = f"""
You are an expert in analyzing educational feedback forms.

From the sample below, detect which questions are Likert-scale based (i.e., answered on a 1 to 5 scale such as Strongly Disagree to Strongly Agree).

Your task is to group these Likert-type questions into a **small number of logically meaningful and broad categories** based on their semantic content.

 **Important Instructions**:
- Do not create too many categories.
- Avoid overly specific or repetitive categories.
- Combine semantically similar questions into the same category.
- Category names should be **intuitive**, **concise**, and **context-aware** (e.g., "Teaching Quality", "Learning Resources", "Skill Development").

Return a **valid Python dictionary** in JSON format as:
{{ 
  "Question column name": "Detected Category Name", 
  ...
}}

 Output only the JSON dictionary and nothing else.

Here is the sample data:
{sample}
"""
    try:
        response = model.generate_content(prompt)
        result_text = re.sub(r"^```(?:json|python)?|```$", "", response.text.strip())
        return json.loads(result_text)
    except Exception as e:
        print("Gemini failed. Raw output:")
        print(response.text)
        print(f"Error: {e}")
        return {}

def sanitize_text(text):
    if pd.isna(text):
        return ""

    replacements = {
        ''': "'", ''': "'", '"': '"', '"': '"', '–': '-', '—': '-',
        '\u00a0': ' ', '•': '-', '→': '->'
    }
    clean_text = str(text)
    for orig, repl in replacements.items():
        clean_text = clean_text.replace(orig, repl)
    return clean_text.encode('latin-1', 'replace').decode('latin-1')

#table and chart
def generate_summary_table(sub_df, category_cols, feedback_type='stakeholder'):
    summary = {}
    for col in category_cols:
        if col in sub_df.columns:
            if feedback_type == 'stakeholder':
                # Coerce to numeric, drop non-numeric, convert to int, then get value counts
                scores = pd.to_numeric(sub_df[col], errors='coerce').dropna()
                # Ensure scores are within a reasonable Likert range (e.g., 1-5)
                scores = scores[scores.between(1, 5)].astype(int).value_counts().to_dict()
                bracket_content = extract_bracket_content(col)
                summary[bracket_content] = {i: scores.get(i, 0) for i in range(1, 6)} # Range 1-5
            else:  # subject feedback
                cleaned = pd.to_numeric(sub_df[col], errors='coerce').dropna().astype(int)
                if cleaned.empty:
                    continue
                score_counts = cleaned.value_counts().to_dict()
                summary[col] = {i: score_counts.get(i, 0) for i in range(1, 6)}

    if not summary:
        return pd.DataFrame()

    score_df = pd.DataFrame(summary).T.fillna(0).astype(int)
    score_df["Total"] = score_df[[5, 4, 3, 2, 1]].sum(axis=1)
    
    # Calculate percentages for scores 1 through 5
    for i in range(5, 0, -1):
        if i in score_df.columns:
            score_df[f"% of {i}"] = score_df.apply(
                lambda row: round(row[i] * 100 / row["Total"], 2) if row["Total"] > 0 else 0, axis=1
            )
    
    # Define columns to return
    if feedback_type == 'stakeholder':
        cols_to_return = ["Category", "Total"]
        for i in range(5, 0, -1):
            if i in score_df.columns:
                cols_to_return.extend([i, f"% of {i}"])
        return score_df.reset_index().rename(columns={"index": "Category"})[cols_to_return]
    else:  # subject feedback
        score_df = score_df.reset_index().rename(columns={"index": "Category"})
        return score_df[["Category", "Total", 5, "% of 5", 4, "% of 4", 3, "% of 3", 2, "% of 2", 1, "% of 1"]]

def plot_ratings(score_df, name, title_prefix, feedback_type='stakeholder'):
    if score_df.empty: return None
    # Plot ratings for scores 1-5
    plot_cols = [col for col in [5, 4, 3, 2, 1] if col in score_df.columns]
    df_plot = score_df.set_index("Category")[plot_cols]
    
    if feedback_type == 'stakeholder':
        ax = df_plot.plot(kind='bar', figsize=(12, 6), colormap='viridis')
        for bars in ax.containers:
            ax.bar_label(bars, label_type='edge', fontsize=9, padding=3)
        plt.title(f"{name} Ratings - {title_prefix}", fontsize=14, weight='bold')
        plt.xlabel(name, fontsize=12)
        plt.ylabel("Number of Responses", fontsize=12)
        ax.set_xticklabels(['\n'.join(textwrap.wrap(label, width=20)) for label in df_plot.index], rotation=0, ha='center')
        plt.legend(title='Rating')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout(pad=2.0)
    else:  # subject feedback
        ax = df_plot.plot(kind='bar', figsize=(12, 5))
        for bars in ax.containers:
            ax.bar_label(bars, label_type='edge', fontsize=9)
        plt.title(f"{name} Ratings - {title_prefix}")
        plt.xlabel(name)
        plt.ylabel("No. of Responses")
        wrapped_labels = ['\n'.join(textwrap.wrap(label, width=15)) for label in df_plot.index]
        ax.set_xticklabels(wrapped_labels, rotation=0, ha='center')
        plt.tight_layout()

    # Sanitize filename
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', title_prefix)
    safe_filename = f"{safe_prefix}_{safe_name}.png"
    
    # Save to BytesIO instead of file
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Store in MongoDB GridFS
    chart_id = fs_charts.put(
        buffer.getvalue(),
        filename=safe_filename,
        content_type='image/png'
    )
    
    # Store metadata
    charts_collection.insert_one({
        'chart_id': chart_id,
        'filename': safe_filename,
        'content_type': 'image/png',
        'size': len(buffer.getvalue())
    })
    
    plt.close()
    buffer.close()
    
    return safe_filename # Return only the filename

# pdf
class StakeholderPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Feedback Analysis Report', ln=1, align='C')
        self.ln(5)

    def section_title(self, title):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, sanitize_text(title), ln=1)
        self.ln(2)

    def table(self, df):
        if df.empty:
            self.cell(0, 10, "No data available for this section.", ln=1)
            return
        
        self.set_font('Arial', '', 9)
        # Dynamic column widths
        first_col_width = 55
        num_other_cols = len(df.columns) - 1
        other_col_width = (self.w - 20 - first_col_width) / num_other_cols if num_other_cols > 0 else 0
        
        row_height = 8
        self.set_font('Arial', 'B', 9)
        
        # Header
        self.cell(first_col_width, row_height, str(df.columns[0]), border=1)
        for col in df.columns[1:]:
            self.cell(other_col_width, row_height, str(col), border=1, align='C')
        self.ln()

        # Rows
        self.set_font('Arial', '', 8)
        for _, row in df.iterrows():
            y_before = self.get_y()
            self.multi_cell(first_col_width, row_height, sanitize_text(row.iloc[0]), border=1)
            y_after = self.get_y()
            x_after = self.get_x()
            
            # Reset position to draw other cells in the same row
            self.set_xy(x_after + first_col_width, y_before)
            
            height_of_row = y_after - y_before
            for item in row.iloc[1:]:
                self.cell(other_col_width, height_of_row, str(item), border=1, align='C')
            self.ln(height_of_row)

    def insert_image_from_mongodb(self, filename, y_margin=10):
        try:
            # Find chart in GridFS
            chart_doc = fs_charts.find_one({"filename": filename})
            if chart_doc:
                self.add_page()
                # Save chart to temporary file for PDF insertion
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(chart_doc.read())
                    tmp_path = tmp.name
                
                self.image(tmp_path, x=10, y=30, w=self.w - 20)
                self.set_y(self.get_y() + self.h * 0.4)
                
                # Clean up temporary file
                os.unlink(tmp_path)
        except Exception as e:
            print(f"Error inserting image from MongoDB: {e}")

    def add_summary(self, text):
        self.add_page()
        self.section_title("Suggestion Summary")
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 8, sanitize_text(text))

class SubjectPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Ratings Report', ln=1, align='C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, sanitize_text(title), ln=1)

    def table(self, df, y_start):
        if df.empty:
            self.cell(0, 10, "No data available for this section.", ln=1)
            return

        self.set_font('Arial', '', 9)
        first_col_width = 55
        num_other_cols = len(df.columns) - 1
        other_col_width = (self.w - 20 - first_col_width) / num_other_cols if num_other_cols > 0 else 0
        row_height = 8

        # Header
        self.set_font('Arial', 'B', 9)
        self.cell(first_col_width, row_height, str(df.columns[0]), border=1)
        for col in df.columns[1:]:
            self.cell(other_col_width, row_height, str(col), border=1, align='C')
        self.ln()

        # Data rows
        self.set_font('Arial', '', 8)
        for _, row in df.iterrows():
            x_start = self.get_x()
            y_start = self.get_y()

            text = sanitize_text(row.iloc[0])
            lines = self.multi_cell(first_col_width, row_height, text, split_only=True)
            height_needed = row_height * len(lines)

            # Check if this row will overflow page
            if y_start + height_needed > self.h - self.b_margin:
                self.add_page()
                self.set_font('Arial', 'B', 9)
                self.cell(first_col_width, row_height, str(df.columns[0]), border=1)
                for col in df.columns[1:]:
                    self.cell(other_col_width, row_height, str(col), border=1, align='C')
                self.ln()
                self.set_font('Arial', '', 8)
                x_start = self.get_x()
                y_start = self.get_y()

            # Draw first cell (multi-cell)
            self.set_xy(x_start, y_start)
            self.multi_cell(first_col_width, row_height, text, border=1, align='L')

            # Draw remaining cells
            self.set_xy(x_start + first_col_width, y_start)
            for item in row.iloc[1:]:
                self.cell(other_col_width, height_needed, str(item), border=1, align='C')
            self.ln(height_needed)

    def insert_image_from_mongodb(self, filename, y_margin=10):
        try:
            # Find chart in GridFS
            chart_doc = fs_charts.find_one({"filename": filename})
            if chart_doc:
                self.add_page()
                # Save chart to temporary file for PDF insertion
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(chart_doc.read())
                    tmp_path = tmp.name
                
                self.image(tmp_path, x=10, y=30, w=self.w - 20)
                self.set_y(120)
                
                # Clean up temporary file
                os.unlink(tmp_path)
        except Exception as e:
            print(f"Error inserting image from MongoDB: {e}")

# report generation
def generate_stakeholder_report(sub_df, name, value, category_groups):
    pdf = StakeholderPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, sanitize_text(f"{name} Feedback Report: {value}"), ln=1, align='C')
    pdf.ln(10)
    
    chart_files = []

    for category, cols in category_groups.items():
        valid_cols = [col for col in cols if col in sub_df.columns]
        if not valid_cols: continue
        
        summary_df = generate_summary_table(sub_df, valid_cols, 'stakeholder')
        if not summary_df.empty:
            pdf.section_title(f"{category} Feedback Summary")
            pdf.table(summary_df)
            pdf.ln(10)
            
            chart_file = plot_ratings(summary_df, category, f"{name}_{value}", 'stakeholder')
            if chart_file:
                chart_files.append(chart_file)

    for chart in chart_files:
        pdf.insert_image_from_mongodb(chart)

    suggestion_col = next((col for col in sub_df.columns if 'suggestion' in col.lower()), None)
    if suggestion_col:
        suggestion_summary = summarize_suggestions_with_gemini(sub_df, suggestion_col)
        pdf.add_summary(suggestion_summary)

    output_dir = "feedback_catalyst"
    os.makedirs(output_dir, exist_ok=True)
    safe_value = re.sub(r'[^a-zA-Z0-9_-]', '_', str(value))
    pdf_path = os.path.join(output_dir, f"{name}_{safe_value}_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

def generate_subject_report(sub_df, name, value, category_groups):
    pdf = SubjectPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, sanitize_text(f"{name} Feedback Report: {value}"), ln=1)

    summary_tables, chart_paths = [], []

    for category, cols in category_groups.items():
        valid_cols = [col for col in cols if col in sub_df.columns]
        if not valid_cols:
            continue
        summary_df = generate_summary_table(sub_df, valid_cols, 'subject')
        if not summary_df.empty:
            chart_path = plot_ratings(summary_df, category, f"{name}_{value}", 'subject')
            summary_tables.append((category, summary_df))
            if chart_path:
                chart_paths.append((category, chart_path))

    for category, df_summary in summary_tables:
        pdf.section_title(f"{category} Feedback Summary")
        pdf.table(df_summary, pdf.get_y() + 5)
        pdf.ln(10)

    for _, chart in chart_paths:
        pdf.insert_image_from_mongodb(chart)

    safe_value = str(value).replace(" ", "_").replace("/", "-").replace(".", "_")
    output_dir = "feedback_catalyst"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{name}_{safe_value}_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

def _get_data_and_groups(file_path, feedback_type='stakeholder'):
    """Helper to read data and identify column groups."""
    try:
        df = pd.read_excel(file_path)
    except Exception:
        df = pd.read_csv(file_path)

    os.makedirs("feedback_catalyst", exist_ok=True)
    
    if feedback_type == 'stakeholder':
        category_groups_raw = group_columns_by_category(df)
        category_groups = {}
        for category, cols in category_groups_raw.items():
            likert_cols = []
            for col in cols:
                if col in df.columns:
                    numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                    if not numeric_vals.empty and numeric_vals.between(1, 5, inclusive='both').all():
                        likert_cols.append(col)
            if likert_cols:
                category_groups[category] = likert_cols
    else:  # subject feedback
        category_map = detect_likert_categories_with_gemini_subject(df)
        category_groups = {}
        for question, category in category_map.items():
            if question in df.columns:
                if df[question].dropna().apply(lambda x: str(x).strip().isdigit()).all():
                    category_groups.setdefault(category.strip(), []).append(question)
    
    return df, category_groups

import pandas as pd
import zipfile
from io import BytesIO
import os

def process_feedback(file_bytes, filename, choice, feedback_type='stakeholder', save_to_disk=False, save_chart_fn=None):
    try:
        # Read Excel or CSV from BytesIO
        try:
            df = pd.read_excel(file_bytes)
        except Exception:
            file_bytes.seek(0)
            df = pd.read_csv(file_bytes)
    except Exception as e:
        raise ValueError(f"Error reading uploaded file: {e}")

    # Detect Likert categories based on feedback type
    if feedback_type == 'stakeholder':
        category_groups_raw = group_columns_by_category(df)
        category_groups = {}
        for category, cols in category_groups_raw.items():
            likert_cols = []
            for col in cols:
                if col in df.columns:
                    numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                    if not numeric_vals.empty and numeric_vals.between(1, 5).all():
                        likert_cols.append(col)
            if likert_cols:
                category_groups[category] = likert_cols
    else:  # subject feedback
        category_map = detect_likert_categories_with_gemini_subject(df)
        category_groups = {}
        for question, category in category_map.items():
            if question in df.columns:
                if df[question].dropna().apply(lambda x: str(x).strip().isdigit()).all():
                    category_groups.setdefault(category.strip(), []).append(question)

    output_pdfs = []

    # Interpret choice
    if choice == '1':
        # No grouping – overall report
        if feedback_type == 'stakeholder':
            pdf_path = generate_stakeholder_report(df, 'Overall', 'All Students', category_groups)
        else:
            pdf_path = generate_subject_report(df, 'Overall', 'All Students', category_groups)
        output_pdfs.append(pdf_path)

    elif choice == '2':
        # Group by branch/department
        possible_group_cols = ['Branch', 'Department', 'Subject', 'Faculty', 'Class']  # customize as per your sheet
        group_col = next((col for col in df.columns if col.strip().lower() in [x.lower() for x in possible_group_cols]), None)

        if not group_col:
            raise ValueError("No valid grouping column (e.g., 'Branch', 'Department') found in the file.")

        for value, group_df in df.groupby(group_col):
            if feedback_type == 'stakeholder':
                pdf_path = generate_stakeholder_report(group_df, group_col, value, category_groups)
            else:
                pdf_path = generate_subject_report(group_df, group_col, value, category_groups)
            output_pdfs.append(pdf_path)

    else:
        raise ValueError("Invalid choice. Must be '1' or '2'.")

    # Create ZIP archive in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_path in output_pdfs:
            arcname = os.path.basename(pdf_path)
            with open(pdf_path, 'rb') as f:
                zipf.writestr(arcname, f.read())

    zip_buffer.seek(0)

    # Clean up
    if not save_to_disk:
        for pdf_path in output_pdfs:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    return zip_buffer



def process_for_charts(file_path, choice, feedback_type='stakeholder', save_chart_fn=None):
    """
    Generates charts for feedback analysis and returns a list of chart filenames.
    Works with a file path (Excel or CSV).
    """

    # Try reading Excel or fallback to CSV
    try:
        df = pd.read_excel(file_path)
    except Exception:
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Error reading uploaded file: {e}")

    # Group questions by categories
    if feedback_type == 'stakeholder':
        category_groups_raw = group_columns_by_category(df)
        category_groups = {}
        for category, cols in category_groups_raw.items():
            likert_cols = []
            for col in cols:
                if col in df.columns:
                    numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                    if not numeric_vals.empty and numeric_vals.between(1, 5).all():
                        likert_cols.append(col)
            if likert_cols:
                category_groups[category] = likert_cols
    else:  # subject feedback
        category_map = detect_likert_categories_with_gemini_subject(df)
        category_groups = {}
        for question, category in category_map.items():
            if question in df.columns:
                if df[question].dropna().apply(lambda x: str(x).strip().isdigit()).all():
                    category_groups.setdefault(category.strip(), []).append(question)

    # Detect grouping column like 'Branch'
    branch_col = next((col for col in df.columns if "branch" in col.lower()), None)
    chart_files = []

    # Helper to generate and collect charts
    def generate_and_collect_charts(sub_df, name, value):
        for category, cols in category_groups.items():
            valid_cols = [col for col in cols if col in sub_df.columns]
            if not valid_cols:
                continue
            summary_df = generate_summary_table(sub_df, valid_cols, feedback_type)
            if not summary_df.empty:
                chart_file = plot_ratings(summary_df, category, f"{name}_{value}", feedback_type)
                if chart_file:
                    chart_files.append(chart_file)

    # Chart generation based on choice
    if choice == "1":
        generate_and_collect_charts(df, "Overall", "All_Students")
    elif choice == "2" and branch_col:
        for branch in df[branch_col].dropna().unique():
            branch_df = df[df[branch_col] == branch]
            generate_and_collect_charts(branch_df, "Branch", branch)
    else:
        generate_and_collect_charts(df, "Overall", "All_Students")

    return chart_files
