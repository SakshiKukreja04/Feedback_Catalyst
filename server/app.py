from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import os, pandas as pd
from feedback_processor import process_feedback, process_for_charts
import matplotlib.pyplot as plt
import re
from pymongo import MongoClient
import gridfs
from io import BytesIO
import tempfile
from flask import url_for  


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  
db = client['feedback_db']  
files_collection = db['files'] 
charts_collection = db['charts']
fs_files = gridfs.GridFS(db, collection='files')  
fs_charts = gridfs.GridFS(db, collection='charts')

def sanitize_filename(name):
    return re.sub(r'[^A-Za-z0-9_]+', '_', name)

# 1) Upload an Excel/CSV and store in MongoDB GridFS
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
        
    try:
        # Read file content
        file_content = file.read()
        
        # Store file in GridFS
        file_id = fs_files.put(
            file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # Store metadata in files collection
        files_collection.insert_one({
            'file_id': file_id,
            'filename': file.filename,
            'content_type': file.content_type,
            'size': len(file_content)
        })
        
        return jsonify({"filename": file.filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2) Given a filename, return its column headers
@app.route('/headers/<filename>', methods=['GET'])
def get_headers(filename):
    try:
        # Find file in GridFS
        file_doc = fs_files.find_one({"filename": filename})
        if not file_doc:
            return jsonify({"error": "File not found"}), 404
            
        # Read file content
        file_content = file_doc.read()
        
        # Create pandas DataFrame
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(BytesIO(file_content))
        else:
            df = pd.read_excel(BytesIO(file_content))
            
        return jsonify({"headers": list(df.columns)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3) Generate the report ZIP using the file from MongoDB + choice + feedback type
@app.route('/generate-report', methods=['POST'])
def generate_report():
    file = request.files.get('file')
    choice = request.form.get('choice')
    feedback_type = request.form.get('feedbackType', 'stakeholder')

    if not file or not choice:
        return jsonify({"error": "Missing file or choice"}), 400

    if choice not in ['1', '2']:
        return jsonify({"error": "Invalid choice parameter"}), 400

    if feedback_type not in ['stakeholder', 'subject']:
        return jsonify({"error": "Invalid feedback type"}), 400

    try:
        # Use filename for extension and pass file.stream as file-like object
        zip_buffer = process_feedback(
            file_bytes=file.stream,
            filename=file.filename,
            choice=choice,
            feedback_type=feedback_type
        )

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name='feedback_reports.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-charts', methods=['POST'])
def generate_charts():
    file = request.files.get('file')
    choice = request.form.get('choice')
    feedback_type = request.form.get('feedbackType', 'stakeholder')

    if not file or not choice:
        return jsonify({"error": "Missing file or choice"}), 400

    if choice not in ['1', '2']:
        return jsonify({"error": "Invalid choice parameter"}), 400

    if feedback_type not in ['stakeholder', 'subject']:
        return jsonify({"error": "Invalid feedback type"}), 400

    tmp_file_path = None
    try:
        # Save file to a temporary path
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file_path = tmp_file.name
            file.save(tmp_file_path)

        # Generate chart files (filenames already stored in GridFS by plot_ratings)
        chart_filenames = process_for_charts(tmp_file_path, choice, feedback_type)
        print(f"Chart filenames returned: {chart_filenames}")

        # Generate URLs to retrieve charts via /charts/<filename>
        chart_urls = [
            url_for('get_chart', filename=filename, _external=True)
            for filename in chart_filenames
        ]

        return jsonify({
            "chart_urls": chart_urls,
            "total_charts": len(chart_urls)
        })

    except Exception as e:
        print(f"Error in generate_charts: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@app.route('/charts/<filename>')
def get_chart(filename):
    try:
        print(f"Looking for chart with filename: {filename}")  # Add logging
        
        # Find chart in GridFS by filename
        chart_doc = fs_charts.find_one({"filename": filename})
        if not chart_doc:
            print(f"Chart not found for filename: {filename}")  # Add logging
            return jsonify({"error": "Chart not found"}), 404
            
        print(f"Found chart for filename: {filename}")  # Add logging
        
        # Return chart content
        return send_file(
            BytesIO(chart_doc.read()),
            mimetype='image/png',
            as_attachment=False
        )
    except Exception as e:
        print(f"Error in get_chart: {str(e)}")  # Add logging
        return jsonify({"error": str(e)}), 500
        
if __name__ == '__main__':
    app.run(port=5001, debug=True)