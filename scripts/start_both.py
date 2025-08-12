#!/usr/bin/env python3
"""
Start both the API server and React frontend
"""

import os
import subprocess
import sys
import threading
import time

def start_api():
    """Start the Flask API server"""
    print("Starting API server...")
    try:
        subprocess.run([sys.executable, 'run_api.py'], cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        pass

def start_frontend():
    """Start the React frontend"""
    time.sleep(3)  # Give API server time to start
    print("Starting frontend server...")
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
        print("Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError:
            print("Error: Failed to install dependencies")
            return
    
    try:
        subprocess.run(['npm', 'start'], cwd=frontend_dir)
    except KeyboardInterrupt:
        pass

def main():
    print("Starting PDF Bank Parser Web Application")
    print("="*50)
    print("API Server: http://localhost:5000")
    print("Frontend: http://localhost:3000")
    print("="*50)
    print("Press Ctrl+C to stop both servers")
    print()
    
    # Start API server in a separate thread
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    
    try:
        # Start frontend in main thread
        start_frontend()
    except KeyboardInterrupt:
        print("\nStopping servers...")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())