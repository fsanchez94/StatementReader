#!/usr/bin/env python3

import requests
import os
import time
from pathlib import Path

API_BASE = "http://127.0.0.1:5000/api"

def test_upload_endpoint():
    """Test file upload endpoint"""
    print("Testing upload endpoint...")
    
    # Use an existing PDF file
    pdf_files = list(Path("data/input/husband").glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in data/input/husband for testing")
        return None
    
    test_file = pdf_files[0]
    print(f"Using test file: {test_file.name}")
    
    with open(test_file, 'rb') as f:
        files = {'files': (test_file.name, f, 'application/pdf')}
        
        try:
            response = requests.post(f"{API_BASE}/upload/", files=files, timeout=30)
            if response.status_code == 201:
                data = response.json()
                session_id = data.get('session_id')
                print(f"Upload successful! Session ID: {session_id}")
                return session_id
            else:
                print(f"Upload failed: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Upload request failed: {e}")
            return None

def test_status_endpoint(session_id):
    """Test session status endpoint"""
    print(f"Testing status endpoint for session {session_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/status/{session_id}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Status check successful! Status: {data.get('status')}")
            return True
        else:
            print(f"Status check failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Status request failed: {e}")
        return False

def test_process_endpoint(session_id):
    """Test file processing endpoint"""
    print(f"Testing process endpoint for session {session_id}...")
    
    try:
        response = requests.post(f"{API_BASE}/process/{session_id}/", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"Processing successful! Status: {data.get('status')}")
            return data.get('status') == 'completed'
        else:
            print(f"Processing failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Process request failed: {e}")
        return False

def main():
    print("Starting Django API Tests")
    print("=" * 50)
    
    # Test 1: Upload
    session_id = test_upload_endpoint()
    if not session_id:
        print("Upload test failed, stopping tests")
        return
    
    time.sleep(1)
    
    # Test 2: Status check
    if not test_status_endpoint(session_id):
        print("Status test failed")
        return
    
    time.sleep(1)
    
    # Test 3: Process files
    if test_process_endpoint(session_id):
        print("All tests passed!")
        
        # Test 4: Download (optional)
        print(f"Download URL: {API_BASE}/download/{session_id}/")
    else:
        print("Processing test failed")
    
    print("=" * 50)
    print("Django API Tests Complete")

if __name__ == "__main__":
    main()