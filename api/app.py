from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
import tempfile
import uuid
from datetime import datetime
import sys
import traceback

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from parsers.parser_factory import ParserFactory
from utils.pdf_processor import PDFProcessor

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store processing jobs in memory (in production, use Redis or database)
processing_jobs = {}

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
OUTPUT_FOLDER = 'temp_outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/debug/files', methods=['GET'])
def debug_files():
    """Debug endpoint to check generated files"""
    output_files = []
    if os.path.exists(OUTPUT_FOLDER):
        for file in os.listdir(OUTPUT_FOLDER):
            if file.endswith('.csv'):
                file_path = os.path.join(OUTPUT_FOLDER, file)
                output_files.append({
                    "filename": file,
                    "path": file_path,
                    "exists": os.path.exists(file_path),
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                })
    return jsonify({"output_folder": OUTPUT_FOLDER, "files": output_files})

@app.route('/api/download-direct/<filename>', methods=['GET'])
def download_direct(filename):
    """Direct download of CSV files from temp_outputs"""
    try:
        # Security check - only allow CSV files
        if not filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files allowed"}), 400
        
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Use absolute path and proper headers
        abs_file_path = os.path.abspath(file_path)
        return send_file(abs_file_path, as_attachment=True, download_name=filename, mimetype='text/csv')
    
    except Exception as e:
        print(f"Direct download error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/parser-types', methods=['GET'])
def get_parser_types():
    """Get available parser types"""
    parser_types = [
        {"id": "industrial_checking", "label": "BI Checking GTQ", "bank": "industrial", "account": "checking"},
        {"id": "industrial_usd_checking", "label": "BI Checking USD", "bank": "industrial", "account": "usd_checking"},
        {"id": "industrial_credit", "label": "BI Credit GTQ", "bank": "industrial", "account": "credit"},
        {"id": "industrial_credit_usd", "label": "BI Credit USD", "bank": "industrial", "account": "credit_usd"},
        {"id": "gyt_credit", "label": "GyT Credit", "bank": "gyt", "account": "credit"},
        {"id": "bam_credit", "label": "BAM Credit", "bank": "bam", "account": "credit"}
    ]
    return jsonify(parser_types)

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and parser selection"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files')
        parser_selections = json.loads(request.form.get('parsers', '{}'))
        account_holders = json.loads(request.form.get('account_holders', '{}'))
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No files selected"}), 400
        
        # Create job ID
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "status": "uploaded",
            "files": [],
            "created_at": datetime.now().isoformat(),
            "total_files": len(files),
            "processed_files": 0,
            "results": []
        }
        
        # Save uploaded files
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                filename = file.filename
                filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
                file.save(filepath)
                
                job_data["files"].append({
                    "filename": filename,
                    "filepath": filepath,
                    "parser": parser_selections.get(filename, {}),
                    "account_holder": account_holders.get(filename, "husband")
                })
        
        processing_jobs[job_id] = job_data
        
        return jsonify({"job_id": job_id, "status": "uploaded", "files_count": len(job_data["files"])})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process/<job_id>', methods=['POST'])
def process_job(job_id):
    """Process uploaded files"""
    try:
        if job_id not in processing_jobs:
            return jsonify({"error": "Job not found"}), 404
        
        job = processing_jobs[job_id]
        job["status"] = "processing"
        
        # Emit status update
        socketio.emit('job_status', {"job_id": job_id, "status": "processing", "progress": 0})
        
        all_transactions = []
        processed_files = []
        
        for i, file_data in enumerate(job["files"]):
            try:
                # Emit progress update
                progress = int((i / len(job["files"])) * 100)
                socketio.emit('job_progress', {
                    "job_id": job_id, 
                    "progress": progress,
                    "current_file": file_data["filename"]
                })
                
                # Get parser configuration
                parser_config = file_data["parser"]
                bank_type = parser_config.get("bank")
                account_type = parser_config.get("account")
                is_spouse = file_data["account_holder"] == "spouse"
                
                # Create parser
                parser = ParserFactory.get_parser(
                    bank_type=bank_type,
                    account_type=account_type,
                    pdf_path=file_data["filepath"],
                    is_spouse=is_spouse
                )
                
                # Extract transactions
                transactions = parser.extract_data()
                
                if transactions:
                    # Set account name to filename without extension
                    document_name = os.path.splitext(file_data["filename"])[0]
                    for t in transactions:
                        t['Account Name'] = document_name
                    
                    all_transactions.extend(transactions)
                    processed_files.append({
                        "filename": file_data["filename"],
                        "transactions_count": len(transactions),
                        "account_holder": file_data["account_holder"]
                    })
                
                job["processed_files"] += 1
                
            except Exception as e:
                print(f"Error processing file {file_data['filename']}: {str(e)}")
                traceback.print_exc()
                processed_files.append({
                    "filename": file_data["filename"],
                    "error": str(e),
                    "transactions_count": 0,
                    "account_holder": file_data["account_holder"]
                })
        
        # Generate output files
        output_files = []
        if all_transactions:
            # Create combined CSV
            combined_filename = f"all_transactions_{job_id}_{datetime.now().strftime('%Y%m%d')}.csv"
            combined_filepath = os.path.join(OUTPUT_FOLDER, combined_filename)
            
            import pandas as pd
            df = pd.DataFrame(all_transactions)
            df = df.sort_values(['Date', 'Account Name'])
            df.to_csv(combined_filepath, index=False)
            
            output_files.append({
                "filename": combined_filename,
                "filepath": combined_filepath,
                "type": "combined",
                "transactions_count": len(all_transactions)
            })
        
        # Update job status
        job["status"] = "completed"
        job["results"] = processed_files
        job["output_files"] = output_files
        job["total_transactions"] = len(all_transactions)
        job["completed_at"] = datetime.now().isoformat()
        
        # Emit completion
        socketio.emit('job_completed', {
            "job_id": job_id,
            "results": processed_files,
            "total_transactions": len(all_transactions),
            "output_files": output_files
        })
        
        return jsonify({"status": "completed", "results": processed_files, "output_files": output_files})
    
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        socketio.emit('job_error', {"job_id": job_id, "error": str(e)})
        return jsonify({"error": str(e)}), 500

@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and results"""
    if job_id not in processing_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(processing_jobs[job_id])

@app.route('/api/download/<job_id>/<filename>', methods=['GET'])
def download_file(job_id, filename):
    """Download generated CSV file"""
    try:
        if job_id not in processing_jobs:
            return jsonify({"error": "Job not found"}), 404
        
        job = processing_jobs[job_id]
        
        # Find the file in output_files
        file_path = None
        for output_file in job.get("output_files", []):
            if output_file["filename"] == filename:
                file_path = output_file["filepath"]
                break
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Use absolute path and proper headers
        abs_file_path = os.path.abspath(file_path)
        return send_file(abs_file_path, as_attachment=True, download_name=filename, mimetype='text/csv')
    
    except Exception as e:
        print(f"Download error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)