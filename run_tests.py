#!/usr/bin/env python3
"""
Test runner script for the PDF Bank Statement Parser

This script provides a convenient way to run different types of tests
with proper configuration and reporting.
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_command(command, description):
    """Run a command and handle the output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        print("Error: pytest not found. Please install test dependencies:")
        print("pip install -r requirements.txt")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run PDF Bank Parser tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        base_cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage or args.html:
        base_cmd.extend(["--cov=src", "--cov-report=term-missing"])
        if args.html:
            base_cmd.append("--cov-report=html:tests/htmlcov")
    
    # Skip slow tests if requested
    if args.fast:
        base_cmd.extend(["-m", "not slow"])
    
    success = True
    
    if args.unit:
        cmd = base_cmd + ["tests/unit/"]
        success = run_command(cmd, "Unit Tests") and success
    elif args.integration:
        cmd = base_cmd + ["tests/integration/"]
        success = run_command(cmd, "Integration Tests") and success
    else:
        # Run all tests
        cmd = base_cmd + ["tests/"]
        success = run_command(cmd, "All Tests") and success
    
    if args.html and (args.coverage or not args.unit and not args.integration):
        html_path = Path("tests/htmlcov/index.html")
        if html_path.exists():
            print(f"\nHTML coverage report generated: {html_path.absolute()}")
            print("Open in browser to view detailed coverage information")
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("✓ All tests completed successfully!")
    else:
        print("✗ Some tests failed. Check the output above.")
        sys.exit(1)
    
    print(f"{'='*60}")

if __name__ == "__main__":
    main()