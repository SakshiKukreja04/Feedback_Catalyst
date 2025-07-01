import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from fpdf import FPDF
import os, zipfile, json, re, textwrap
from io import BytesIO

# === Gemini setup ===
genai.configure(api_key="AIzaSyChRdH4CqkQF_4JC9IMBNptsXDw0JLMBrA")
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# === Utilities ===
def detect_likert_categories_with_gemini(df):
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
    suggestions = df[column_name].dropna().astype(str)
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
            scores = pd.to_numeric(sub_df[col], errors='coerce').dropna().astype(int).value_counts().to_dict()
            bracket_content = extract_bracket_content(col)
            summary[bracket_content] = {i: scores.get(i, 0) for i in range(1, 5)}

    score_df = pd.DataFrame(summary).T.fillna(0).astype(int)
    score_df["Total"] = score_df[[4, 3, 2, 1]].sum(axis=1)
    for i in range(4, 0, -1):
        score_df[f"% of {i}"] = round(score_df[i] * 100 / score_df["Total"], 2) if score_df["Total"].sum() > 0 else 0
    return score_df.reset_index().rename(columns={"index": "Category"})[["Category", "Total", 4, "% of 4", 3, "% of 3", 2, "% of 2", 1, "% of 1"]]

def plot_ratings(score_df, name, title_prefix):
    if score_df.empty: return None
    plot_cols = [col for col in [4, 3, 2, 1] if col in score_df.columns]
    df_plot = score_df.set_index("Category")[plot_cols]
    ax = df_plot.plot(kind='bar', figsize=(12, 5))
    for bars in ax.containers:
        ax.bar_label(bars, label_type='edge', fontsize=9)
    plt.title(f"{name} Ratings - {title_prefix}")
    plt.xlabel(name)
    plt.ylabel("No. of Responses")
    ax.set_xticklabels(['\n'.join(textwrap.wrap(label, width=15)) for label in df_plot.index], rotation=0, ha='center')
    plt.tight_layout()

    safe_filename = f"{title_prefix}_{name}.png"
    chart_path = os.path.join("feedback_catalyst", safe_filename)
    plt.savefig(chart_path)
    plt.close()
    return chart_path

def sanitize_text(text):
    if pd.isna(text): return ""
    replacements = {
        ''': "'", ''': "'", '"': '"', '–': '-', '—': '-',
        '\u00a0': ' ', '•': '-', '→': '->'
    }
    clean_text = str(text)
    for orig, repl in replacements.items():
        clean_text = clean_text.replace(orig, repl)
    return clean_text.encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Ratings Report', ln=1, align='C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, sanitize_text(title), ln=1)

    def table(self, df, y_start):
        self.set_xy(10, y_start)
        self.set_font('Arial', '', 9)
        first_col_width = 60
        other_col_width = (self.w - 20 - first_col_width) / (len(df.columns) - 1)
        row_height = 6
        self.set_font('Arial', 'B', 9)
        self.cell(first_col_width, row_height, str(df.columns[0]), border=1)
        for col in df.columns[1:]:
            self.cell(other_col_width, row_height, str(col), border=1, align='C')
        self.ln()
        self.set_font('Arial', '', 8)
        for i in range(len(df)):
            x_start = self.get_x()
            y_start = self.get_y()
            self.multi_cell(first_col_width, row_height, sanitize_text(df.iloc[i, 0]), border=1)
            y_end = self.get_y()
            row_height_used = y_end - y_start
            self.set_xy(x_start + first_col_width, y_start)
            for item in df.iloc[i, 1:]:
                self.cell(other_col_width, row_height_used, str(item), border=1, align='C')
            self.set_y(y_start + row_height_used)

    def insert_image_with_page_check(self, image_path, y_margin=10):
        if os.path.exists(image_path):
            self.add_page()
            self.image(image_path, x=10, y=30, w=self.w - 20)
            self.set_y(120)

    def add_summary(self, text):
        self.add_page()
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, "Suggestion Summary", ln=1)
        self.set_font('Arial', '', 10)
        for line in textwrap.wrap(text, width=120):
            self.cell(0, 8, line, ln=1)

def generate_report(sub_df, name, value, category_groups):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, sanitize_text(f"{name} Feedback Report: {value}"), ln=1)
    summary_tables, chart_paths = [], []

    for category, cols in category_groups.items():
        valid_cols = [col for col in cols if col in sub_df.columns]
        if not valid_cols: continue
        summary_df = generate_summary_table(sub_df, valid_cols)
        if not summary_df.empty:
            chart_path = plot_ratings(summary_df, category, f"{name}_{value}")
            summary_tables.append((category, summary_df))
            if chart_path: chart_paths.append((category, chart_path))

    for category, df_summary in summary_tables:
        pdf.section_title(f"{category} Feedback Summary")
        pdf.table(df_summary, pdf.get_y() + 5)
        pdf.ln(10)

    for _, chart in chart_paths:
        pdf.insert_image_with_page_check(chart)

    suggestion_col = next((col for col in sub_df.columns if 'suggestion' in col.lower()), None)
    if suggestion_col:
        suggestion_summary = summarize_suggestions_with_gemini(sub_df, suggestion_col)
        pdf.add_summary(suggestion_summary)

    os.makedirs("feedback_catalyst", exist_ok=True)
    safe_value = str(value).replace(" ", "_").replace("/", "-").replace(".", "_")
    pdf_path = os.path.join("feedback_catalyst", f"{name}_{safe_value}_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

def process_feedback(file_path, choice):
    df = pd.read_excel(file_path)
    os.makedirs("feedback_catalyst", exist_ok=True)

    category_groups_raw = group_columns_by_category(df)

    # Filter Likert columns
    category_groups = {}
    for category, cols in category_groups_raw.items():
        likert_cols = []
        for col in cols:
            if col in df.columns:
                numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                if not numeric_vals.empty and 1 <= numeric_vals.min() <= 5:
                    likert_cols.append(col)
        if likert_cols:
            category_groups[category] = likert_cols

    has_branch = any("branch" in col.lower() for col in df.columns)
    branch_col = next((col for col in df.columns if "branch" in col.lower()), None)
    generated_files = []

    if choice == "1":
        pdf_path = generate_report(df, "Overall", "All_Students", category_groups)
        generated_files.append(pdf_path)
    elif choice == "2" and has_branch:
        for branch in df[branch_col].dropna().unique():
            branch_df = df[df[branch_col] == branch]
            pdf_path = generate_report(branch_df, "Branch", branch, category_groups)
            generated_files.append(pdf_path)
    elif choice == "3" and has_branch:
        pdf_path = generate_report(df, "Overall", "All_Students", category_groups)
        generated_files.append(pdf_path)
        for branch in df[branch_col].dropna().unique():
            branch_df = df[df[branch_col] == branch]
            pdf_path = generate_report(branch_df, "Branch", branch, category_groups)
            generated_files.append(pdf_path)
    else:
        pdf_path = generate_report(df, "Overall", "All_Students", category_groups)
        generated_files.append(pdf_path)

    # ZIP all generated PDFs
    zip_path = "feedback_catalyst.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in generated_files:
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=os.path.basename(file_path))

    return zip_path
