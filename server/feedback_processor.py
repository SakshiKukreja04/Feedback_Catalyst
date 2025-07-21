import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from fpdf import FPDF
import os, zipfile, json, re, textwrap
from io import BytesIO
from pymongo import MongoClient
import gridfs
import matplotlib
matplotlib.use('Agg')

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
        genai.configure(api_key="AIzaSyCaCHAUd-8dkb4OtkH-tqOklwADUr7pbIY")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    print(f"Could not configure Gemini. AI features will fail. Error: {e}")
    model = None

# gemini
def detect_likert_categories_with_gemini(df):
    if not model: return {}
    sample = df.sample(min(5, len(df))).to_string(index=False)
    prompt = f"""

You are an expert in analyzing educational feedback forms.

From the sample below, detect which questions are Likert-scale based (i.e., answered on a 1 to 5 scale such as Strongly Disagree to Strongly Agree).

Your task is to assign a concise and meaningful label (1–3 *unique* keywords only) to each Likert-type question.

Instructions:
- Do not repeat generic terms (like "facilities", "support", "opportunity") unless essential.
- The labels should be short, intuitive, and unique to the question's core meaning.
- Avoid redundancy and keep each label 1–3 words max.
- These labels will be used on charts with limited space.

Return a valid Python dictionary in JSON format like:
{{ 
  "Full question column name": "Short label with main keywords",
  ...
}}

Here is the sample data:
{sample}
"""
    try:
        response = model.generate_content(prompt)
        result_text = re.sub(r"^```(?:json|python)?|```$", "", response.text.strip()).strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"Gemini failed: {e}")
        print(f"Raw output:\n{response.text}")
        return {}

import string

# Update extract_main_subject to focus on unique keywords
GENERIC_WORDS = set([
    'coverage', 'of', 'curriculum', 'for', 'to', 'the', 'and', 'support', 'in', 'on', 'with', 'a', 'an', 'is', 'are', 'by', 'as', 'at', 'from', 'if', 'this', 'that', 'it', 'be', 'provided', 'through', 'expert', 'sessions', 'workshops', 'projects', 'professional', 'society', 'etc', 'face', 'strengthen', 'opportunities', 'provided', 'designed', 'well', 'defined', 'sufficient', 'number', 'hours', 'credit', 'allocated', 'balance', 'between', 'practical', 'applications', 'scheme', 'designed', 'qualification', 'skill', 'development', 'programs', 'applicable', 'facility', 'facilities', 'activities', 'lab', 'administrative', 'academic', 'books', 'reference', 'text', 'library', 'canteen', 'cultural', 'sports', 'co-curricular', 'hostel', 'placements', 'higher', 'studies', 'industry', 'challenges', 'domain', 'soft', 'skills'
])

def extract_main_keywords(text, max_keywords=3):
    if pd.isna(text):
        return text
    s = str(text)
    # Remove punctuation and split
    words = s.translate(str.maketrans('', '', string.punctuation)).split()
    # Remove generic/common words
    keywords = [w for w in words if w.lower() not in GENERIC_WORDS]
    # If nothing left, fallback to first 1-2 words
    if not keywords:
        keywords = [w for w in words if w.lower() not in {'of', 'for', 'the', 'and', 'in', 'on', 'with', 'a', 'an'}]
    # Return up to max_keywords joined by space
    return ' '.join(keywords[:max_keywords]) if keywords else s

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
    import ast
    if not model: return {}
    sample = df.sample(min(5, len(df))).to_string(index=False)
    prompt = f"""
You are an expert in educational data visualization.

For each question below, generate a label that is:
- Only 1–2 core keywords (no full sentences, no generic words like 'the', 'curriculum', 'support', 'sufficient', etc.)
- Unique and meaningful for the question's main idea
- Suitable for use as a short x-axis label on a bar chart

Examples:
"Coverage of curriculum for core aspects of your domain" → "Core Domain"
"Support for ICT facilities" → "ICT"
"Number of theory hours and Credit allocated to the course are sufficient" → "Theory Hours"
"Administrative support" → "Administration"
"Library and availability of books" → "Library"
"Skill enhancement opportunities through expert sessions" → "Skill Development"

Return a Python dictionary:
{{ "Full question column name": "Short keyword label", ... }}

Sample:
{sample}
"""
    try:
        response = model.generate_content(prompt)
        result_text = re.sub(r"^```(?:json|python)?|```$", "", response.text.strip()).strip()
        # Extract only the dictionary portion from the output
        if '{' in result_text and '}' in result_text:
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            dict_str = result_text[start:end]
            try:
                label_mapping = ast.literal_eval(dict_str)
                # Fallback to summarize_label if label is empty or too long
                for k, v in label_mapping.items():
                    if not v or len(str(v).split()) > 3:
                        label_mapping[k] = summarize_label(k)
                return label_mapping
            except Exception as e:
                print("Failed to parse Gemini dictionary output.")
                print(f"Raw output:\n{response.text}")
                return {}
        else:
            print("No dictionary found in Gemini output.")
            print(f"Raw output:\n{response.text}")
            return {}
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

import re

def strip_category_prefix(text):
    # Remove 'Category [' and trailing ']' or similar patterns
    match = re.match(r"^[^\[]*\[(.*)\]$", str(text).strip())
    if match:
        return match.group(1).strip()
    # Remove leading category name and keep only the question if possible
    match2 = re.match(r"^[^\[]*\[(.*)", str(text).strip())
    if match2:
        return match2.group(1).strip()
    return str(text).strip()

#table and chart
def generate_summary_table(sub_df, category_cols, short_labels, feedback_type='stakeholder', use_short_labels=True):
    summary = {}
    for col in category_cols:
        if col in sub_df.columns:
            label = short_labels.get(col, col) if use_short_labels else col
            if feedback_type == 'stakeholder':
                scores = pd.to_numeric(sub_df[col], errors='coerce').dropna()
                scores = scores[scores.between(1, 5)].astype(int).value_counts().to_dict()
                summary[label] = {i: scores.get(i, 0) for i in range(1, 6)}
            else:
                cleaned = pd.to_numeric(sub_df[col], errors='coerce').dropna().astype(int)
                if cleaned.empty:
                    continue
                score_counts = cleaned.value_counts().to_dict()
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


def summarize_label(label, max_keywords=2):
    import string
    # Only remove extremely generic stop words
    GENERIC_STOP_WORDS = {
        'the', 'is', 'are', 'for', 'of', 'to', 'and', 'has', 'with', 'a', 'an', 'on', 'in', 'by', 'at', 'from', 'as',
        'this', 'that', 'it', 'be', 'etc', 'your', 'yours'
    }
    # Clean and split label
    label_cleaned = label.translate(str.maketrans('', '', string.punctuation.replace('&', ''))).strip()
    words = label_cleaned.split()
    # Remove generic stop words, keep domain-specific/meaningful terms
    keywords = [w.capitalize() for w in words if w.lower() not in GENERIC_STOP_WORDS]
    # Special handling for common patterns (examples)
    if 'Skill' in keywords and 'Enhancement' in keywords:
        return 'Skill Enhancement'
    if 'Social' in keywords and 'Engagement' in keywords:
        return 'Social Engagement'
    if 'Ict' in keywords and 'Support' in keywords:
        return 'ICT Support'
    # Remove duplicates, keep order
    seen = set()
    filtered = []
    for w in keywords:
        if w not in seen:
            filtered.append(w)
            seen.add(w)
    # Only keep 1 or 2 key informative words
    if len(filtered) > 2:
        filtered = filtered[:2]
    if not filtered:
        return 'General'
    return ' '.join(filtered)

# In plot_ratings, apply summarize_label only to df_plot.index for x-axis labels

def plot_ratings(score_df, report_type, report_name, feedback_type='stakeholder'):
    if score_df.empty: return None
    plot_cols = [col for col in [5, 4, 3, 2, 1] if col in score_df.columns]
    concise_labels = [summarize_label(cat) for cat in score_df['Category']]
    df_plot = score_df.set_index('Category')[plot_cols]
    df_plot.index = concise_labels
    # Chart title: Only report type and report name
    chart_title = f"{report_type} - {report_name}"
    if feedback_type == 'stakeholder':
        ax = df_plot.plot(kind='bar', figsize=(36, 14), colormap='viridis', width=0.4)
        for bars in ax.containers:
            ax.bar_label(bars, label_type='edge', fontsize=28, padding=3)
        plt.title(chart_title, fontsize=28, weight='bold')
        plt.xlabel(report_type, fontsize=28)
        plt.ylabel("Number of Responses", fontsize=28)
        plt.xticks(rotation=30, ha='right', fontsize=32)
        plt.yticks(fontsize=32)
        plt.legend(title='Rating', fontsize=24, title_fontsize=26)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout(pad=3.0)
        plt.subplots_adjust(bottom=0.28)
    else:
        ax = df_plot.plot(kind='bar', figsize=(36, 14), width=0.4)
        for bars in ax.containers:
            ax.bar_label(bars, label_type='edge', fontsize=28)
        plt.title(chart_title, fontsize=28, weight='bold')
        plt.xlabel(report_type, fontsize=28)
        plt.ylabel("No. of Responses", fontsize=28)
        plt.xticks(rotation=30, ha='right', fontsize=32)
        plt.yticks(fontsize=32)
        plt.legend(fontsize=24)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.28)
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
            # Only show the question text, not the repeated category
            question_text = strip_category_prefix(row.iloc[0])
            self.multi_cell(first_col_width, row_height, sanitize_text(question_text), border=1)
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
        first_col_width = 55
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
            # Only show the question text, not the repeated category
            question_text = strip_category_prefix(row.iloc[0])
            lines = self.multi_cell(first_col_width, row_height, sanitize_text(question_text), split_only=True, border=1, align='L')
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
            self.multi_cell(first_col_width, row_height, sanitize_text(question_text), border=1, align='L')
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

# report generation
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
        # Table: use original headers
        summary_df = generate_summary_table(sub_df, valid_cols, short_labels, 'stakeholder', use_short_labels=False)
        if not summary_df.empty:
            pdf.section_title(f"{category} Feedback Summary")
            pdf.table(summary_df)
            pdf.ln(10)
            # Chart: use concise labels
            chart_df = generate_summary_table(sub_df, valid_cols, short_labels, 'stakeholder', use_short_labels=True)
            # Make chart filename unique per group, category, and value
            if value:
                unique_report_name = f"{report_name}__{name}__{value}__{category}"
            else:
                unique_report_name = f"{report_name}__{category}"
            chart_file = plot_ratings(chart_df, report_type, unique_report_name, 'stakeholder')
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
        # Table: use original headers
        summary_df = generate_summary_table(sub_df, valid_cols, short_labels, 'subject', use_short_labels=False)
        if not summary_df.empty:
            # Chart: use concise labels
            chart_df = generate_summary_table(sub_df, valid_cols, short_labels, 'subject', use_short_labels=True)
            # Make chart filename unique per group and category
            if value:
                unique_report_name = f"{report_name}__{value}__{category}"
            else:
                unique_report_name = f"{report_name}__{category}"
            chart_path = plot_ratings(chart_df, report_type_str, unique_report_name, 'subject')
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
                    if not numeric_vals.empty and numeric_vals.between(1, 5, inclusive='both').all():
                        likert_cols.append(col)
                        short_labels[col] = summarize_label(col)
            if likert_cols:
                category_groups[category] = likert_cols
    else:  # subject feedback
        label_mapping = detect_likert_categories_with_gemini_subject(df)
        category_groups = {}
        short_labels = {}
        for long_col, short_label in label_mapping.items():
            if long_col in df.columns:
                numeric_vals = pd.to_numeric(df[long_col], errors='coerce').dropna()
                if not numeric_vals.empty and numeric_vals.between(1, 5).all():
                    category_groups.setdefault(short_label.strip(), []).append(long_col)
                    short_labels[long_col] = short_label.strip()

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
            # For charts, always use concise labels
            chart_df = generate_summary_table(sub_df, valid_cols, short_labels, feedback_type, use_short_labels=True)
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