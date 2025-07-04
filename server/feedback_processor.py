import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from fpdf import FPDF
import os, zipfile, json, re, textwrap
from io import BytesIO

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


# === Utilities ===
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

def generate_summary_table(sub_df, category_cols):
    summary = {}
    for col in category_cols:
        if col in sub_df.columns:
            # Coerce to numeric, drop non-numeric, convert to int, then get value counts
            scores = pd.to_numeric(sub_df[col], errors='coerce').dropna()
            # Ensure scores are within a reasonable Likert range (e.g., 1-5)
            scores = scores[scores.between(1, 5)].astype(int).value_counts().to_dict()
            bracket_content = extract_bracket_content(col)
            summary[bracket_content] = {i: scores.get(i, 0) for i in range(1, 6)} # Range 1-5

    if not summary:
        return pd.DataFrame()

    score_df = pd.DataFrame(summary).T.fillna(0).astype(int)
    score_df["Total"] = score_df.sum(axis=1)
    
    # Calculate percentages for scores 1 through 5
    for i in range(5, 0, -1):
        if i in score_df.columns:
            score_df[f"% of {i}"] = score_df.apply(
                lambda row: round(row[i] * 100 / row["Total"], 2) if row["Total"] > 0 else 0, axis=1
            )
    
    # Define columns to return
    cols_to_return = ["Category", "Total"]
    for i in range(5, 0, -1):
        if i in score_df.columns:
            cols_to_return.extend([i, f"% of {i}"])
            
    return score_df.reset_index().rename(columns={"index": "Category"})[cols_to_return]


def plot_ratings(score_df, name, title_prefix):
    if score_df.empty: return None
    # Plot ratings for scores 1-5
    plot_cols = [col for col in [5, 4, 3, 2, 1] if col in score_df.columns]
    df_plot = score_df.set_index("Category")[plot_cols]
    
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

    # Sanitize filename
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', title_prefix)
    safe_filename = f"{safe_prefix}_{safe_name}.png"
    
    # Ensure directory exists
    output_dir = "feedback_catalyst"
    os.makedirs(output_dir, exist_ok=True)
    
    chart_path = os.path.join(output_dir, safe_filename)
    plt.savefig(chart_path)
    plt.close()
    return safe_filename # Return only the filename

def sanitize_text(text):
    if pd.isna(text): return ""
    # A more robust sanitization for various unicode characters
    return str(text).encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
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


    def insert_image_with_page_check(self, image_path, y_margin=10):
        full_path = os.path.join("feedback_catalyst", image_path)
        if os.path.exists(full_path):
            self.add_page()
            self.image(full_path, x=10, y=30, w=self.w - 20)
            self.set_y(self.get_y() + self.h * 0.4) # Move cursor down

    def add_summary(self, text):
        self.add_page()
        self.section_title("Suggestion Summary")
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 8, sanitize_text(text))

def generate_report(sub_df, name, value, category_groups):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, sanitize_text(f"{name} Feedback Report: {value}"), ln=1, align='C')
    pdf.ln(10)
    
    chart_files = []

    for category, cols in category_groups.items():
        valid_cols = [col for col in cols if col in sub_df.columns]
        if not valid_cols: continue
        
        summary_df = generate_summary_table(sub_df, valid_cols)
        if not summary_df.empty:
            pdf.section_title(f"{category} Feedback Summary")
            pdf.table(summary_df)
            pdf.ln(10)
            
            chart_file = plot_ratings(summary_df, category, f"{name}_{value}")
            if chart_file:
                chart_files.append(chart_file)

    for chart in chart_files:
        pdf.insert_image_with_page_check(chart)

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

def _get_data_and_groups(file_path):
    """Helper to read data and identify column groups."""
    try:
        df = pd.read_excel(file_path)
    except Exception:
        df = pd.read_csv(file_path)

    os.makedirs("feedback_catalyst", exist_ok=True)
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
    return df, category_groups

def process_feedback(file_path, choice):
    """Generates PDF reports and zips them."""
    df, category_groups = _get_data_and_groups(file_path)
    
    branch_col = next((col for col in df.columns if "branch" in col.lower()), None)
    generated_files = []

    if choice == "1":
        pdf_path = generate_report(df, "Overall", "All_Students", category_groups)
        generated_files.append(pdf_path)
    elif choice == "2" and branch_col:
        for branch in df[branch_col].dropna().unique():
            branch_df = df[df[branch_col] == branch]
            pdf_path = generate_report(branch_df, "Branch", branch, category_groups)
            generated_files.append(pdf_path)
    else: # Default/fallback case
        pdf_path = generate_report(df, "Overall", "All_Students", category_groups)
        generated_files.append(pdf_path)

    zip_path = "feedback_reports.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in generated_files:
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path

def process_for_charts(file_path, choice):
    """Generates only the chart images and returns their filenames."""
    df, category_groups = _get_data_and_groups(file_path)
    
    branch_col = next((col for col in df.columns if "branch" in col.lower()), None)
    chart_files = []

    def generate_and_collect_charts(sub_df, name, value):
        for category, cols in category_groups.items():
            valid_cols = [col for col in cols if col in sub_df.columns]
            if not valid_cols: continue
            
            summary_df = generate_summary_table(sub_df, valid_cols)
            if not summary_df.empty:
                chart_file = plot_ratings(summary_df, category, f"{name}_{value}")
                if chart_file:
                    chart_files.append(chart_file)

    if choice == "1":
        generate_and_collect_charts(df, "Overall", "All_Students")
    elif choice == "2" and branch_col:
        for branch in df[branch_col].dropna().unique():
            branch_df = df[df[branch_col] == branch]
            generate_and_collect_charts(branch_df, "Branch", branch)
    else: # Default/fallback case
        generate_and_collect_charts(df, "Overall", "All_Students")
        
    return chart_files
