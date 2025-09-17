#!/usr/bin/env python3
"""
Test runner script for MyCandidate API tests.
Run this script to execute all tests.
"""

import os
import sys
import subprocess

def run_tests():
    """Run all tests using pytest."""
    # Set environment variables
    os.environ['PYTHONPATH'] = os.getcwd()
    os.environ['FLASK_ENV'] = 'testing'
    
    # Run pytest
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_api_routes.py', 
            '-v', 
            '--tb=short'
        ], check=True)
        print("All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("pytest not found. Please install pytest: pip install pytest")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
