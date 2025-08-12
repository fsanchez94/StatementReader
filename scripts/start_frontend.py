#!/usr/bin/env python3
"""
Start the React frontend development server
"""

import os
import subprocess
import sys

def main():
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    if not os.path.exists(frontend_dir):
        print("Error: Frontend directory not found")
        return 1
    
    if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
        print("Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError:
            print("Error: Failed to install dependencies. Make sure Node.js and npm are installed.")
            return 1
    
    print("Starting React development server...")
    print("Frontend will be available at: http://localhost:3000")
    print("Make sure the API server is running at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run(['npm', 'start'], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\nFrontend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"Error starting frontend: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())