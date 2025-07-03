from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os, pandas as pd
from feedback_processor import process_feedback

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    choice = request.form.get('choice')  # must match frontend's formData.append('choice', ...)
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

if __name__ == '__main__':
    app.run(port=5001, debug=True)
