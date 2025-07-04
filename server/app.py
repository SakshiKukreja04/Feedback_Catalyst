from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import os, pandas as pd
from feedback_processor import process_feedback
import matplotlib.pyplot as plt
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[^A-Za-z0-9_]+', '_', name)

# 1) Upload an Excel/CSV and return filename for frontend
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)
    return jsonify({"filename": file.filename})

# 2) Given a filename, return its column headers
@app.route('/headers/<filename>', methods=['GET'])
def get_headers(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
        return jsonify({"headers": list(df.columns)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3) Generate the report ZIP using the previously uploaded file + choice
@app.route('/generate-report', methods=['POST'])
def generate_report():
    file = request.files.get('file')
    choice = request.form.get('choice')
    show_charts = request.form.get('showCharts') == 'true'
    if not file or not choice:
        return jsonify({"error": "Missing file or choice"}), 400

    # Save (or overwrite) the same file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        zip_path = process_feedback(file_path, choice)
        return send_file(zip_path, as_attachment=True, mimetype='application/zip')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-charts', methods=['POST'])
def generate_charts():
    file = request.files.get('file')
    choice = request.form.get('choice')
    if not file or not choice:
        return jsonify({"error": "Missing file or choice"}), 400

    # Save the uploaded file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Read the file into a DataFrame
    if file.filename.lower().endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # Create charts directory if it doesn't exist
    charts_dir = os.path.join(os.getcwd(), "charts")
    os.makedirs(charts_dir, exist_ok=True)

    chart_files = []
    # For each numeric column, generate a bar chart of value counts
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            plt.figure()
            df[col].value_counts().sort_index().plot(kind='bar')
            plt.title(f'Distribution for {col}')
            plt.xlabel(col)
            plt.ylabel('Count')
            chart_filename = f"{sanitize_filename(col)}_chart.png"
            chart_path = os.path.join(charts_dir, chart_filename)
            plt.savefig(chart_path)
            plt.close()
            chart_files.append(chart_filename)

    return jsonify({"chart_files": chart_files})

@app.route('/charts/<filename>')
def get_chart(filename):
    charts_dir = os.path.join(os.getcwd(), "charts")
    return send_from_directory(charts_dir, filename)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
