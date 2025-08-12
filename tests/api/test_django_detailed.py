#!/usr/bin/env python3

import requests
import json
from pathlib import Path

API_BASE = "http://127.0.0.1:5000/api"

def test_detailed_processing():
    # Upload a file
    pdf_files = list(Path("data/input/husband").glob("*.pdf"))
    if not pdf_files:
        print("No test files found")
        return
    
    test_file = pdf_files[0]
    print(f"Testing with: {test_file.name}")
    
    # Upload with parser selection
    with open(test_file, 'rb') as f:
        files = {'files': (test_file.name, f, 'application/pdf')}
        data = {
            'parsers': json.dumps({
                test_file.name: {"bank": "industrial", "account": "checking"}
            }),
            'account_holders': json.dumps({
                test_file.name: "husband"
            })
        }
        response = requests.post(f"{API_BASE}/upload/", files=files, data=data)
        if response.status_code != 201:
            print(f"Upload failed: {response.text}")
            return
        
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"Session ID: {session_id}")
        print(f"Upload response: {json.dumps(session_data, indent=2)}")
    
    # Process
    response = requests.post(f"{API_BASE}/process/{session_id}/")
    print(f"\nProcess response status: {response.status_code}")
    if response.status_code == 200:
        process_data = response.json()
        print(f"Process response: {json.dumps(process_data, indent=2)}")
        
        # Check individual file errors
        if 'files' in process_data:
            for file_info in process_data['files']:
                if file_info.get('status') == 'error':
                    print(f"\nFile error: {file_info.get('filename')}")
                    print(f"Error message: {file_info.get('error_message')}")
    else:
        print(f"Process failed: {response.text}")

if __name__ == "__main__":
    test_detailed_processing()