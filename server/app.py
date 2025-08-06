from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import os, pandas as pd
from dotenv import load_dotenv
import logging
import psutil

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Updated imports to match the actual function names in feedback_processor.py
from feedback_processor import process_feedback, process_for_charts, summarize_suggestions, generate_implementation_plan_gemini, find_common_themes_gemini, clear_chart_cache
import matplotlib.pyplot as plt
import re
from database import client, db, files_collection, charts_collection, fs_files, fs_charts
from io import BytesIO
import tempfile
from flask import url_for  
import zipfile
from feedback_processor import sanitize_text


app = Flask(__name__)

# Get frontend URL from environment variable with fallback for development
frontend_url = os.environ.get("VITE_FRONTEND_BASE_URL")
if frontend_url:
    print(f"🔧 CORS configured for frontend URL: {frontend_url}")
    CORS(app, resources={r"/*": {"origins": [frontend_url]}})
else:
    # Fallback to "*" only in development mode
    print("🔧 CORS configured for all origins (development mode)")
    CORS(app, resources={r"/*": {"origins": "*"}})

# Health check endpoint for Render
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

def sanitize_filename(name):
    return re.sub(r'[^A-Za-z0-9_]+', '_', name)

def log_memory_usage(stage=""):
    """Log current memory usage for debugging"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    print(f"🧠 Memory usage {stage}: {memory_mb:.2f} MB")
    return memory_mb

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
@app.route('/headers/<path:filename>', methods=['GET'])
def get_headers(filename):
    try:
        # URL decode the filename
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        print(f"🔍 Looking for file: '{decoded_filename}'")
        
        # Find file in GridFS - try exact match first, then search for files ending with the filename
        file_doc = fs_files.find_one({"filename": decoded_filename})
        
        if not file_doc:
            # Search for files that end with the requested filename
            all_files = list(fs_files.find())
            matching_files = [f for f in all_files if f.filename.endswith(decoded_filename)]
            
            if matching_files:
                file_doc = matching_files[0]
                print(f"✅ Found file with path: {file_doc.filename}")
            else:
                print(f"❌ File not found. Available files: {[f.filename for f in all_files]}")
                return jsonify({"error": "File not found"}), 404
        else:
            print(f"✅ File found: {decoded_filename}")
        
        # Read file content
        file_content = file_doc.read()
        
        # Create pandas DataFrame
        if decoded_filename.lower().endswith('.csv'):
            df = pd.read_csv(BytesIO(file_content))
        else:
            df = pd.read_excel(BytesIO(file_content))
            
        return jsonify({"headers": list(df.columns)})
    except Exception as e:
        print(f"❌ Error in get_headers: {e}")
        return jsonify({"error": str(e)}), 500

# 3) Generate the report ZIP using the file from MongoDB + choice + feedback type
@app.route('/generate-report', methods=['POST'])
def generate_report():
    feedback_type = request.form.get('feedbackType', 'stakeholder')
    choice = request.form.get('choice')
    report_type = request.form.get('reportType', None)
    uploaded_filenames = request.form.get('uploadedFilenames', None)
    uploaded_filename = request.form.get('uploadedFilename', None)

    if not choice:
        return jsonify({"error": "Missing choice"}), 400

    if choice not in ['1', '2']:
        return jsonify({"error": "Invalid choice parameter"}), 400

    if feedback_type not in ['stakeholder', 'subject']:
        return jsonify({"error": "Invalid feedback type"}), 400

    try:
        if feedback_type == 'stakeholder' and 'files[]' in request.files:
            files = request.files.getlist('files[]')
            filenames = []
            if uploaded_filenames:
                try:
                    filenames = list(eval(uploaded_filenames))
                except Exception:
                    filenames = []
            
            # Memory optimization: Process files one by one and stream to final zip
            final_zip = BytesIO()
            with zipfile.ZipFile(final_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for idx, file in enumerate(files):
                    fname = filenames[idx] if idx < len(filenames) else file.filename
                    try:
                        pdf_zip = process_feedback(
                            file_bytes=file.stream,
                            filename=file.filename,
                            choice=choice,
                            feedback_type=feedback_type,
                            uploaded_filename=fname,
                            report_type=report_type
                        )
                        # Extract PDFs from this zip and add to final zip immediately
                        with zipfile.ZipFile(pdf_zip, 'r') as zf:
                            for name in zf.namelist():
                                pdf_data = zf.read(name)
                                zipf.writestr(name, pdf_data)
                                del pdf_data  # Free memory immediately
                        
                        # Clear the pdf_zip from memory
                        pdf_zip.close()
                        del pdf_zip
                        
                    except Exception as file_error:
                        print(f"Error processing file {file.filename}: {file_error}")
                        # Continue with other files instead of failing completely
                        continue
            
            final_zip.seek(0)
            return send_file(
                final_zip,
                as_attachment=True,
                download_name='feedback_reports.zip',
                mimetype='application/zip'
            )
        else:
            # subject feedback or fallback to single file
            file = request.files.get('file')
            if not file:
                return jsonify({"error": "Missing file"}), 400
            zip_buffer = process_feedback(
                file_bytes=file.stream,
                filename=file.filename,
                choice=choice,
                feedback_type=feedback_type,
                uploaded_filename=uploaded_filename,
                report_type=report_type
            )
            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name='feedback_reports.zip',
                mimetype='application/zip'
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-stakeholder-report', methods=['POST'])
def generate_stakeholder_report():
    print("Starting stakeholder report generation...")
    log_memory_usage("at start")
    files = request.files.getlist('file')  # Accept multiple files
    print(f"Received files for report generation: {len(files)} files")
    choice = request.form.get('choice')
    report_type = request.form.get('reportType', None)
    uploaded_filenames = request.form.get('uploadedFilenames', None)
    feedback_type = 'stakeholder'

    if not choice:
        return jsonify({"error": "Missing choice"}), 400
    if choice not in ['1', '2']:
        return jsonify({"error": "Invalid choice parameter"}), 400

    try:
        if 'files[]' in request.files or 'files' in request.files:
            files = request.files.getlist('files[]') or request.files.getlist('files')
            filenames = []
            if uploaded_filenames:
                try:
                    filenames = list(eval(uploaded_filenames))
                except Exception:
                    filenames = []
            
            # Memory optimization: Process files one by one and stream to final zip
            print(f"Processing {len(files)} files...")
            final_zip = BytesIO()
            
            with zipfile.ZipFile(final_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for idx, file in enumerate(files):
                    print(f"Processing file {idx + 1}/{len(files)}: {file.filename}")
                    log_memory_usage(f"before file {idx + 1}")
                    fname = filenames[idx] if idx < len(filenames) else file.filename
                    
                    try:
                        pdf_zip = process_feedback(
                            file_bytes=file.stream,
                            filename=file.filename,
                            choice=choice,
                            feedback_type=feedback_type,
                            uploaded_filename=fname,
                            report_type=report_type
                        )
                        print(f"File {idx + 1} processed successfully")
                        
                        # Extract and add PDFs to final zip immediately to save memory
                        with zipfile.ZipFile(pdf_zip, 'r') as zf:
                            for name in zf.namelist():
                                pdf_data = zf.read(name)
                                zipf.writestr(name, pdf_data)
                                del pdf_data  # Free memory immediately
                        
                        # Clear the pdf_zip from memory
                        pdf_zip.close()
                        del pdf_zip
                        log_memory_usage(f"after file {idx + 1}")
                        
                    except Exception as file_error:
                        print(f"Error processing file {file.filename}: {file_error}")
                        # Continue with other files instead of failing completely
                        continue
            
            final_zip.seek(0)
            log_memory_usage("at completion")
            print("Report generation completed successfully")
            return send_file(
                final_zip,
                as_attachment=True,
                download_name='feedback_reports.zip',
                mimetype='application/zip'
            )
        else:
            return jsonify({"error": "No files uploaded"}), 400
    except Exception as e:
        print(f"Error in stakeholder report generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate-charts', methods=['POST'])
def generate_charts():
    files = request.files.getlist('file')  # Accept multiple files
    print(f"Received files for chart generation", files)  # Add logging
    choice = request.form.get('choice')
    feedback_type = request.form.get('feedbackType', 'stakeholder')
    uploaded_filename = request.form.get('uploadedFilename', None)
    report_type = request.form.get('reportType', None)

    if not files or not choice:
        return jsonify({"error": "Missing file(s) or choice"}), 400

    if choice not in ['1', '2']:
        return jsonify({"error": "Invalid choice parameter"}), 400

    if feedback_type not in ['stakeholder', 'subject']:
        return jsonify({"error": "Invalid feedback type"}), 400

    chart_urls = []
    tmp_paths = []

    try:
        if feedback_type == 'stakeholder':
            for file in files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                    tmp_path = tmp_file.name
                    file.save(tmp_path)
                    tmp_paths.append(tmp_path)

                chart_filenames = process_for_charts(
                    tmp_path, choice, feedback_type, file.filename, report_type
                )

                chart_urls.extend([
                    url_for('get_chart', filename=filename, _external=True)
                    for filename in chart_filenames
                ])
        else:  # subject feedback supports only one file
            if len(files) > 1:
                return jsonify({"error": "Only one file allowed for 'subject' feedback"}), 400

            file = files[0]
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                tmp_path = tmp_file.name
                file.save(tmp_path)
                tmp_paths.append(tmp_path)

            chart_filenames = process_for_charts(
                tmp_path, choice, feedback_type, uploaded_filename, report_type
            )

            chart_urls.extend([
                url_for('get_chart', filename=filename, _external=True)
                for filename in chart_filenames
            ])

        return jsonify({
            "chart_urls": chart_urls,
            "total_charts": len(chart_urls)
        })

    except Exception as e:
        print(f"Error in generate_charts: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        for path in tmp_paths:
            if os.path.exists(path):
                os.unlink(path)


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

from fpdf import FPDF
import pandas as pd
from io import BytesIO

@app.route('/get-suggestions', methods=['POST'])
def get_suggestions():
    feedback_type = request.form.get('feedbackType', 'stakeholder')
    suggestions = []

    try:
        if feedback_type == 'stakeholder' and 'files[]' in request.files:
            # Stakeholder: Multiple files
            files = request.files.getlist('files[]')
            filenames = request.form.get('uploadedFilenames')
            filenames = eval(filenames) if filenames else [f.filename for f in files]

            for idx, file in enumerate(files):
                df = pd.read_excel(file) if file.filename.lower().endswith('.xlsx') else pd.read_csv(file)
                suggestion_col = next((col for col in df.columns if 'suggestion' in col.lower()), None)
                if suggestion_col:
                    summary = summarize_suggestions(df, suggestion_col)
                    suggestions.append((filenames[idx], summary))

            # Get common themes and implementation plan using Mistral (updated function names)
            all_summary_texts = [summary for _, summary in suggestions]
            common_themes = find_common_themes_gemini(all_summary_texts)
            implementation_plan = generate_implementation_plan_gemini(common_themes)

        else:
            # Single file upload (non-stakeholder or fallback)
            file = request.files.get('file')
            filename = request.form.get('uploadedFilename', file.filename)
            df = pd.read_excel(file) if file.filename.lower().endswith('.xlsx') else pd.read_csv(file)
            suggestion_col = next((col for col in df.columns if 'suggestion' in col.lower()), None)
            if suggestion_col:
                summary = summarize_suggestions(df, suggestion_col)
                suggestions.append((filename, summary))

                # Generate implementation plan even for single summary (updated function name)
                implementation_plan = generate_implementation_plan_gemini(summary)
            else:
                implementation_plan = None

            # No common themes for single file
            common_themes = None

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(0, 10, sanitize_text("Suggestions Summary"), ln=True, align='C')
        pdf.ln(10)

        for fname, summary in suggestions:
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(0, 10, sanitize_text(f"File: {fname}"), ln=True)
            pdf.set_font("Arial", size=11)
            for line in summary.split('\n'):
                pdf.multi_cell(0, 8, sanitize_text(line))
            pdf.ln(5)

        # Stakeholder common themes
        if common_themes:
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(0, 10, sanitize_text("Common Themes Across All Files:"), ln=True)
            pdf.set_font("Arial", size=11)
            for line in common_themes.split('\n'):
                pdf.multi_cell(0, 8, sanitize_text(line))
            pdf.ln(5)

        # Implementation plan (always included if generated)
        if implementation_plan:
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(0, 10, sanitize_text("Suggested Implementation Plan:"), ln=True)
            pdf.set_font("Arial", size=11)
            for line in implementation_plan.split('\n'):
                pdf.multi_cell(0, 8, sanitize_text(line))
            pdf.ln(10)

        # Output to buffer with proper encoding
        try:
            pdf_bytes = pdf.output(dest='S').encode('latin1')
        except UnicodeEncodeError:
            # Fallback: try with replacement
            pdf_bytes = pdf.output(dest='S').encode('latin1', 'replace')
        
        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name="Suggestions_Summary.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear-chart-cache', methods=['POST'])
def clear_cache():
    """Clear the chart cache to force regeneration of charts"""
    try:
        success = clear_chart_cache()
        if success:
            return jsonify({"message": "Chart cache cleared successfully"}), 200
        else:
            return jsonify({"error": "Failed to clear chart cache"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

        
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)