#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line
from pathlib import Path

def setup_django():
    django_path = Path(__file__).parent / 'django_backend'
    sys.path.insert(0, str(django_path))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')
    django.setup()

def run_migrations():
    print("Running Django migrations...")
    os.chdir(Path(__file__).parent / 'django_backend')
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])

def run_server():
    print("Starting Django development server...")
    os.chdir(Path(__file__).parent / 'django_backend')
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:5000'])

if __name__ == '__main__':
    setup_django()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        run_migrations()
    else:
        run_migrations()
        run_server()