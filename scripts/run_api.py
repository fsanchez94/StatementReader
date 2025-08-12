#!/usr/bin/env python3
"""
Flask API server for PDF Bank Statement Parser
Run this to start the web API backend
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from api.app import socketio, app

if __name__ == '__main__':
    print("Starting PDF Bank Parser API Server...")
    print("Access the API at: http://localhost:5000")
    print("API Documentation:")
    print("  - Health Check: GET /api/health")
    print("  - Parser Types: GET /api/parser-types")
    print("  - Upload Files: POST /api/upload")
    print("  - Process Job: POST /api/process/<job_id>")
    print("  - Job Status: GET /api/job/<job_id>")
    print("  - Download: GET /api/download/<job_id>/<filename>")
    print("\nPress Ctrl+C to stop the server")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)