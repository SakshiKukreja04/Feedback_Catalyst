import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from fpdf import FPDF
import os, zipfile, json, re, textwrap
from io import BytesIO
import gridfs
import matplotlib

matplotlib.use('Agg')

# MongoDB setup - Use the same connection as the rest of the application
from database import client, db, charts_collection, fs_charts

try:
    # Attempt to configure from environment variable first
    if 'GEMINI_API_KEY' in os.environ:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    else:
        # Fallback for local testing - replace with your key
        genai.configure(api_key="AIzaSyCaCHAUd-8dkb4OtkH-tqOklwADUr7pbIY")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    print(f"Could not configure Gemini. AI features will fail. Error: {e}")
    model = None

# Removed detect_likert_categories_with_gemini_subject function as we're now using original column names

import string

# Removed GENERIC_WORDS set as we're now using original column names

# Removed extract_main_keywords function as we're now using original column names

def extract_category_name(text):
    if pd.isna(text): return text
    match = re.search(r'^([^\[]+)', str(text).strip())
    return match.group(1).strip() if match else str(text)



def group_columns_by_category(df):
    category_groups = {}
    for col in df.columns:
        # Check if column has brackets for category grouping
        if '[' in str(col) and ']' in str(col):
            category = extract_category_name(col)
            category_groups.setdefault(category, []).append(col)
        else:
            # For columns without brackets, check if they should be grouped by common prefix
            col_str = str(col)
            if any(prefix in col_str.lower() for prefix in ['curriculum', 'facilities', 'skill', 'social', 'ict', 'administrative', 'library', 'canteen', 'cultural', 'hostel']):
                # Extract the main category from the column name
                if 'curriculum' in col_str.lower():
                    category = 'Curriculum'
                elif 'facilities' in col_str.lower():
                    category = 'Facilities'
                elif 'skill' in col_str.lower():
                    category = 'Skill Enhancement'
                elif 'social' in col_str.lower():
                    category = 'Social Engagement'
                elif 'ict' in col_str.lower():
                    category = 'ICT Support'
                elif 'administrative' in col_str.lower():
                    category = 'Administrative'
                elif 'library' in col_str.lower():
                    category = 'Library'
                elif 'canteen' in col_str.lower():
                    category = 'Canteen'
                elif 'cultural' in col_str.lower():
                    category = 'Cultural'
                elif 'hostel' in col_str.lower():
                    category = 'Hostel'
                else:
                    category = col_str
                category_groups.setdefault(category, []).append(col)
            else:
                # For other columns, treat as individual categories
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

import re

# Removed strip_category_prefix function as we're now using original column names

def generate_summary_table(sub_df, category_cols, short_labels, feedback_type='stakeholder'):
    """
    Generate summary table for BOTH charts and tables.
    This ensures consistency between chart x-axis and table categories.
    """
    summary = {}
    for col in category_cols:
        if col in sub_df.columns:
            if feedback_type == 'stakeholder':
                # For stakeholder feedback, extract bracket content for cleaner labels
                label = extract_bracket_content(col)
                scores = pd.to_numeric(sub_df[col], errors='coerce').dropna()
                # Filter to only include values between 1-5
                scores = scores[scores.between(1, 5)]
                if not scores.empty:
                    scores = scores.astype(int).value_counts().to_dict()
                    summary[label] = {i: scores.get(i, 0) for i in range(1, 6)}
            else:
                # For subject feedback, use original column names
                label = col
                cleaned = pd.to_numeric(sub_df[col], errors='coerce').dropna()
                # Filter to only include values between 1-5
                cleaned = cleaned[cleaned.between(1, 5)]
                if not cleaned.empty:
                    score_counts = cleaned.astype(int).value_counts().to_dict()
                    summary[label] = {i: score_counts.get(i, 0) for i in range(1, 6)}
    
    if not summary:
        return pd.DataFrame()
    
    score_df = pd.DataFrame(summary).T.fillna(0).astype(int)
    score_df["Total"] = score_df[[5, 4, 3, 2, 1]].sum(axis=1)
    for i in range(5, 0, -1):
        if i in score_df.columns:
            score_df[f"% of {i}"] = score_df.apply(
                lambda row: round(row[i] * 100 / row["Total"], 2) if row["Total"] > 0 else 0, axis=1
            )
    
    if feedback_type == 'stakeholder':
        cols_to_return = ["Category", "Total"]
        for i in range(5, 0, -1):
            if i in score_df.columns:
                cols_to_return.extend([i, f"% of {i}"])
        return score_df.reset_index().rename(columns={"index": "Category"})[cols_to_return]
    else:
        score_df = score_df.reset_index().rename(columns={"index": "Category"})
        return score_df[["Category", "Total", 5, "% of 5", 4, "% of 4", 3, "% of 3", 2, "% of 2", 1, "% of 1"]]

# Removed summarize_label function as we're now using original column names

# MODIFIED plot_ratings to use consistent labels
def wrap_text(text, max_length=30):
    """Wrap text to multiple lines if it's too long"""
    if len(text) <= max_length:
        return text
    
    # Try to break at spaces or common separators
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_length:
            current_line += (" " + word) if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return "\n".join(lines)

def extract_bracket_content(text):
    """Extract content inside brackets for cleaner display"""
    if not text:
        return text
    
    text_str = str(text)
    
    # First, try to extract content from square brackets
    if '[' in text_str and ']' in text_str:
        start_idx = text_str.find('[')
        end_idx = text_str.find(']')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            bracket_content = text_str[start_idx + 1:end_idx].strip()
            
            # Remove common prefixes like "Curriculum" from the bracket content
            prefixes_to_remove = ['Curriculum', 'Facilities', 'Infrastructure', 'Faculty', 'Administration']
            for prefix in prefixes_to_remove:
                if bracket_content.startswith(prefix + ' '):
                    bracket_content = bracket_content[len(prefix + ' '):].strip()
            
            return bracket_content
    
    # If no brackets found, try to remove common prefixes from the original text
    prefixes_to_remove = ['Curriculum', 'Facilities', 'Infrastructure', 'Faculty', 'Administration']
    for prefix in prefixes_to_remove:
        if text_str.startswith(prefix + ' '):
            return text_str[len(prefix + ' '):].strip()
    
    # If no patterns match, return the original text
    return text_str

def wrap_chart_labels(text, words_per_line=4):
    """Wrap chart labels with line breaks after every ~4 words, limiting to 2-3 lines"""
    if not text or len(text) <= 40:
        return text
    
    words = text.split()
    if len(words) <= words_per_line:
        return text
    
    lines = []
    for i in range(0, len(words), words_per_line):
        line_words = words[i:i + words_per_line]
        lines.append(" ".join(line_words))
    
    # Limit to maximum 3 lines to prevent excessive height
    if len(lines) > 3:
        lines = lines[:3]
        # Add ellipsis to indicate truncation
        if len(lines[-1]) > 50:
            lines[-1] = lines[-1][:47] + "..."
    
    return "\n".join(lines)

def plot_ratings(score_df, report_type, report_name, feedback_type='stakeholder'):
    print(f"Plotting ratings for {report_type} - {report_name} with feedback type: {feedback_type}")
    if score_df.empty:
        return None

    plot_cols = [col for col in [5, 4, 3, 2, 1] if col in score_df.columns]

    # Use the Category column as-is (which now contains original column names)
    df_plot = score_df.set_index('Category')[plot_cols]

    # Chart title
    chart_title = f"{report_type} - {report_name}"

    if feedback_type == 'stakeholder':
        ax = df_plot.plot(kind='barh', figsize=(30, 60), colormap='viridis')
        plt.ylabel(report_type, fontsize=28)
        plt.xlabel("Number of Responses", fontsize=28)
        plt.yticks(fontsize=18)

        # Wrap long category labels for cleaner display with ~4 words per line
        wrapped_labels = [wrap_chart_labels(label, words_per_line=3) for label in df_plot.index]
        plt.xticks(range(len(wrapped_labels)), wrapped_labels, rotation=45, ha='right', fontsize=14)
        plt.yticks(fontsize=32)
        plt.legend(title='Rating', fontsize=24, title_fontsize=26)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout(pad=3.0)
        plt.subplots_adjust(bottom=0.75)  # Increased bottom margin for better multiline label display
    else:
        ax = df_plot.plot(kind='bar', figsize=(40, 18), width=0.4)
        # for bars in ax.containers:
        #     ax.bar_label(bars, label_type='edge', fontsize=28)
        plt.title(chart_title, fontsize=28, weight='bold')
        plt.xlabel(report_type, fontsize=28)
        plt.ylabel("No. of Responses", fontsize=28)
        
        # For subject feedback, use original labels with wrapping
        wrapped_labels = [wrap_chart_labels(label, words_per_line=3) for label in df_plot.index]
        plt.xticks(range(len(wrapped_labels)), wrapped_labels, rotation=45, ha='right', fontsize=16)
        plt.yticks(fontsize=32)
        plt.legend(fontsize=24)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.7)  # Significantly increased bottom margin for multi-line labels

    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', report_type)
    safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', report_name)
    safe_filename = f"{safe_prefix}_{safe_name}.png"

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    chart_id = fs_charts.put(
        buffer.getvalue(),
        filename=safe_filename,
        content_type='image/png'
    )

    charts_collection.insert_one({
        'chart_id': chart_id,
        'filename': safe_filename,
        'content_type': 'image/png',
        'size': len(buffer.getvalue())
    })

    plt.close()
    buffer.close()

    return safe_filename

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
        first_col_width = 79  # Increased width for longer column names
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
            # Use the category name as-is (now contains original column names)
            category_text = str(row.iloc[0])
            # For stakeholder feedback, extract bracket content for cleaner display
            cleaned_text = extract_bracket_content(category_text)
            # Wrap long category names with better formatting for readability
            wrapped_text = wrap_chart_labels(cleaned_text, words_per_line=6)
            self.multi_cell(first_col_width, row_height, sanitize_text(wrapped_text), border=1)
            y_after = self.get_y()
            x_after = self.get_x()
            self.set_xy(x_after + first_col_width, y_before)
            height_of_row = y_after - y_before
            for item in row.iloc[1:]:
                self.cell(other_col_width, height_of_row, str(item), border=1, align='C')
            self.ln(height_of_row)

    def insert_image_from_mongodb(self, filename, y_margin=10):
        try:
            chart_doc = fs_charts.find_one({"filename": filename})
            if chart_doc:
                self.add_page()
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(chart_doc.read())
                    tmp_path = tmp.name
                # Make chart as large as possible in PDF
                self.image(tmp_path, x=1, y=5, w=self.w-2)
                self.set_y(self.get_y() + self.h * 0.4)
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
        first_col_width = 79  # Increased width for longer column names
        num_other_cols = len(df.columns) - 1
        other_col_width = (self.w - 20 - first_col_width) / num_other_cols if num_other_cols > 0 else 0
        row_height = 8
        self.set_font('Arial', 'B', 9)
        self.cell(first_col_width, row_height, str(df.columns[0]), border=1)
        for col in df.columns[1:]:
            self.cell(other_col_width, row_height, str(col), border=1, align='C')
        self.ln()
        self.set_font('Arial', '', 8)
        for _, row in df.iterrows():
            x_start = self.get_x()
            y_start = self.get_y()
            # Use the category name as-is (now contains original column names)
            category_text = str(row.iloc[0])
            # For subject feedback, use original labels with wrapping
            wrapped_text = wrap_chart_labels(category_text, words_per_line=6)
            lines = self.multi_cell(first_col_width, row_height, sanitize_text(wrapped_text), split_only=True, border=1, align='L')
            height_needed = row_height * len(lines)
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
            self.set_xy(x_start, y_start)
            self.multi_cell(first_col_width, row_height, sanitize_text(wrapped_text), border=1, align='L')
            self.set_xy(x_start + first_col_width, y_start)
            for item in row.iloc[1:]:
                self.cell(other_col_width, height_needed, str(item), border=1, align='C')
            self.ln(height_needed)

    def insert_image_from_mongodb(self, filename, y_margin=10):
        try:
            chart_doc = fs_charts.find_one({"filename": filename})
            if chart_doc:
                self.add_page()
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(chart_doc.read())
                    tmp_path = tmp.name
                # Make chart as large as possible in PDF
                self.image(tmp_path, x=1, y=5, w=self.w-2)
                self.set_y(120)
                os.unlink(tmp_path)
        except Exception as e:
            print(f"Error inserting image from MongoDB: {e}")

def generate_stakeholder_report(sub_df, name, value, category_groups, short_labels, uploaded_filename=None, report_type=None):
    pdf = StakeholderPDF()
    pdf.add_page()
    # Compose heading to match view charts
    title_parts = [uploaded_filename or name]
    if report_type:
        title_parts.append(report_type.capitalize())
    if str(value) and str(value).lower() not in ['all_students', 'all students']:
        title_parts.append(f"{name}: {value}")
    heading = " | ".join(title_parts)
    report_name = uploaded_filename or name
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, sanitize_text(heading), ln=1, align='C')
    pdf.ln(10)

    chart_files = []
    for category, cols in category_groups.items():
        valid_cols = [col for col in cols if col in sub_df.columns]
        if not valid_cols: continue

        # Generate summary using original column names - same for both table and chart
        summary_df = generate_summary_table(sub_df, valid_cols, short_labels, 'stakeholder')
        if not summary_df.empty:
            pdf.section_title(f"{category} Feedback Summary")
            pdf.table(summary_df)
            pdf.ln(10)

            # Chart uses the SAME summary_df, ensuring consistency
            # Use the same logic as view charts: compose title and use category as report_type
            title_parts = [uploaded_filename or name]
            if report_type:
                title_parts.append(report_type.capitalize())
            if str(value) and str(value).lower() not in ['all_students', 'all students']:
                title_parts.append(str(value))
            title = " | ".join(title_parts)
            chart_file = plot_ratings(summary_df, category, title, 'stakeholder')
            if chart_file:
                chart_files.append(chart_file)
        else:
            print(f"Empty summary table for category: {category}")

    for chart in chart_files:
        pdf.insert_image_from_mongodb(chart)

    suggestion_col = next((col for col in sub_df.columns if 'suggestion' in col.lower()), None)
    if suggestion_col:
        suggestion_summary = summarize_suggestions_with_gemini(sub_df, suggestion_col)
        pdf.add_summary(suggestion_summary)

    output_dir = "feedback_catalyst"
    os.makedirs(output_dir, exist_ok=True)
    # Make output filename unique per field
    if value:
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{report_type}_{report_name}_{name}_{value}")
    else:
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{report_type}_{report_name}")
    pdf_path = os.path.join(output_dir, f"{safe_title}_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

def generate_subject_report(sub_df, name, value, category_groups, short_labels, uploaded_filename=None, report_type=None):
    pdf = SubjectPDF()
    pdf.add_page()
    # Use only report type and report name for the main heading
    report_type_str = report_type.capitalize() if report_type else 'Ratings'
    report_name = uploaded_filename or name
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, sanitize_text(f"{report_type_str} - {report_name}"), ln=1)

    summary_tables, chart_paths = [], []
    for category, cols in category_groups.items():
        valid_cols = [col for col in cols if col in sub_df.columns]
        if not valid_cols:
            continue

        # Generate summary using original column names - same for both table and chart
        summary_df = generate_summary_table(sub_df, valid_cols, short_labels, 'subject')
        if not summary_df.empty:
            # Chart uses the SAME summary_df, ensuring consistency
            # Use the same logic as view charts: compose title and use category as report_type
            title_parts = [uploaded_filename or name]
            if report_type:
                title_parts.append(report_type.capitalize())
            if str(value) and str(value).lower() not in ['all_students', 'all students']:
                title_parts.append(str(value))
            title = " | ".join(title_parts)
            chart_path = plot_ratings(summary_df, category, title, 'subject')
            summary_tables.append((category, summary_df))
            if chart_path:
                chart_paths.append((category, chart_path))

    for category, df_summary in summary_tables:
        pdf.section_title(f"{category} Feedback Summary")
        pdf.table(df_summary, pdf.get_y() + 5)
        pdf.ln(10)

    for _, chart in chart_paths:
        pdf.insert_image_from_mongodb(chart)

    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{report_type_str}_{report_name}")
    output_dir = "feedback_catalyst"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{safe_title}_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

def _get_data_and_groups(file_path, feedback_type='stakeholder'):
    """Helper to read data and identify column groups."""
    # Handle both file paths and DataFrame objects
    if isinstance(file_path, pd.DataFrame):
        df = file_path
    else:
        try:
            df = pd.read_excel(file_path)
        except Exception:
            df = pd.read_csv(file_path)

    os.makedirs("feedback_catalyst", exist_ok=True)
    
    if feedback_type == 'stakeholder':
        category_groups_raw = group_columns_by_category(df)
        category_groups = {}
        short_labels = {}
        for category, cols in category_groups_raw.items():
            likert_cols = []
            for col in cols:
                if col in df.columns:
                    numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                    # Include columns that have mostly values between 1-5 (at least 80% of values)
                    if not numeric_vals.empty:
                        valid_vals = numeric_vals[numeric_vals.between(1, 5, inclusive='both')]
                        if len(valid_vals) >= 0.8 * len(numeric_vals):  # At least 80% of values are 1-5
                            likert_cols.append(col)
                            short_labels[col] = col  # Use original column name
            if likert_cols:
                category_groups[category] = likert_cols
    else:  # subject feedback
        # For subject feedback, use original column names instead of AI-generated labels
        category_groups = {}
        short_labels = {}
        for col in df.columns:
            if col in df.columns:
                numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                if not numeric_vals.empty:
                    valid_vals = numeric_vals[numeric_vals.between(1, 5)]
                    if len(valid_vals) >= 0.8 * len(numeric_vals):  # At least 80% of values are 1-5
                        # Use original column name as category
                        category_groups.setdefault(col, []).append(col)
                        short_labels[col] = col  # Use original column name

    return df, category_groups, short_labels

import pandas as pd
import zipfile
from io import BytesIO
import os

def process_feedback(file_bytes, filename, choice, feedback_type='stakeholder', save_to_disk=False, save_chart_fn=None, uploaded_filename=None, report_type=None):
    try:
        try:
            df = pd.read_excel(file_bytes)
        except Exception:
            file_bytes.seek(0)
            df = pd.read_csv(file_bytes)
    except Exception as e:
        raise ValueError(f"Error reading uploaded file: {e}")
    df, category_groups, short_labels = _get_data_and_groups(file_bytes, feedback_type)
    output_pdfs = []
    if choice == '1':
        if feedback_type == 'stakeholder':
            pdf_path = generate_stakeholder_report(df, 'Overall', 'All Students', category_groups, short_labels, uploaded_filename, report_type)
        else:
            pdf_path = generate_subject_report(df, 'Overall', 'All Students', category_groups, short_labels, uploaded_filename, report_type)
        print(f"PDF generated at: {pdf_path}, exists: {os.path.exists(pdf_path)}")
        output_pdfs.append(pdf_path)
    elif choice == '2':
        possible_group_cols = ['Branch', 'Department', 'Subject', 'Faculty', 'Class']
        group_col = next((col for col in df.columns if col.strip().lower() in [x.lower() for x in possible_group_cols]), None)
        if not group_col:
            raise ValueError("No valid grouping column (e.g., 'Branch', 'Department') found in the file.")
        for value, group_df in df.groupby(group_col):
            if feedback_type == 'stakeholder':
                pdf_path = generate_stakeholder_report(group_df, group_col, value, category_groups, short_labels, uploaded_filename, report_type)
            else:
                pdf_path = generate_subject_report(group_df, group_col, value, category_groups, short_labels, uploaded_filename, report_type)
            print(f"PDF generated at: {pdf_path}, exists: {os.path.exists(pdf_path)}")
            output_pdfs.append(pdf_path)
    else:
        raise ValueError("Invalid choice. Must be '1' or '2'.")

    output_dir = "feedback_catalyst"
    os.makedirs(output_dir, exist_ok=True)
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_path in output_pdfs:
            arcname = os.path.basename(pdf_path)
            print(f"Trying to zip: {pdf_path}, exists: {os.path.exists(pdf_path)}")
            if not os.path.exists(pdf_path):
                print(f"ERROR: PDF file not found, skipping: {pdf_path}")
                continue
            try:
                with open(pdf_path, 'rb') as f:
                    zipf.writestr(arcname, f.read())
            except Exception as e:
                print(f"ERROR: Failed to add {pdf_path} to zip: {e}")
    zip_buffer.seek(0)
    if not save_to_disk:
        for pdf_path in output_pdfs:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    return zip_buffer

def process_for_charts(file_path, choice, feedback_type='stakeholder', uploaded_filename=None, report_type=None, save_chart_fn=None):
    df, category_groups, short_labels = _get_data_and_groups(file_path, feedback_type)
    # Use the same group column logic as process_feedback
    possible_group_cols = ['Branch', 'Department', 'Subject', 'Faculty', 'Class']
    group_col = next((col for col in df.columns if col.strip().lower() in [x.lower() for x in possible_group_cols]), None)
    chart_files = []

    def generate_and_collect_charts(sub_df, name, value):
        title_parts = [uploaded_filename or name]
        if report_type:
            title_parts.append(report_type.capitalize())
        if str(value) and str(value).lower() not in ['all_students', 'all students']:
            title_parts.append(str(value))
        title = " | ".join(title_parts)
        for category, cols in category_groups.items():
            valid_cols = [col for col in cols if col in sub_df.columns]
            if not valid_cols:
                continue
            # Use same summary generation approach for consistency with original column names
            chart_df = generate_summary_table(sub_df, valid_cols, short_labels, feedback_type)
            if not chart_df.empty:
                chart_file = plot_ratings(chart_df, category, title, feedback_type)
                if chart_file:
                    chart_files.append(chart_file)

    if choice == "1":
        generate_and_collect_charts(df, "Overall", "All_Students")
    elif choice == "2" and group_col:
        for value, group_df in df.groupby(group_col):
            generate_and_collect_charts(group_df, group_col, value)
    else:
        generate_and_collect_charts(df, "Overall", "All_Students")

    return chart_files   

def summarize_suggestions(df, column_name):
    if not model:
        # Fallback: join all suggestions and return first 10 lines
        suggestions = df[column_name].dropna().astype(str)
        return "\n".join(suggestions.tolist()[:10])
    suggestions = df[column_name].dropna().astype(str)
    if suggestions.empty:
        return "No suggestions found."
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
        print(f"Gemini failed: {e}")
        return "Could not summarize suggestions due to an error."

# Function to find common parts/themes using Gemini
def find_common_themes_gemini(summaries):
    if not model:
        return "Gemini model not available to extract common themes."

    combined = "\n\n".join(summaries)
    prompt = f"""
You are an expert in feedback analysis.

Below are summaries of feedback collected from multiple stakeholders. Analyze them and identify common themes or recurring suggestions. 
List the themes in bullet points or as a concise comma-separated list.

Feedback Summaries:
{combined}
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini failed while extracting themes: {e}")
        return "Could not extract common themes due to an error."

# Function to generate implementation suggestions using Gemini
def generate_implementation_plan_gemini(themes):
    if not model:
        return f"Model unavailable. Use these themes for implementation: {themes}"

    prompt = f"""
You are a strategy advisor for educational institutions.

Based on the following recurring feedback themes: {themes}, suggest a brief and highly practical implementation plan.

Requirements:
- Maximum 5 bullet points
- Each point must be 1–2 short sentences
- Focus on actionable steps that are easy to understand and execute
- Align with typical stakeholder expectations (students, faculty, admin)
- Do not include long explanations or background information
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini failed while generating implementation plan: {e}")
        return "Could not generate implementation plan due to an error."
        