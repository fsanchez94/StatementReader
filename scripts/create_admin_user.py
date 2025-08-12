#!/usr/bin/env python3

import os
import sys
import django
from pathlib import Path

# Setup Django
django_path = Path(__file__).parent.parent / 'backends' / 'django'
sys.path.insert(0, str(django_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    # Check if admin user already exists
    if User.objects.filter(username='admin').exists():
        print("Admin user already exists!")
        admin_user = User.objects.get(username='admin')
        print(f"Username: admin")
        print(f"Email: {admin_user.email}")
        print("Password: Use the existing password or reset if needed")
        return
    
    # Create new admin user
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'  # Simple password for development
    )
    
    print("Django admin user created successfully!")
    print("="*50)
    print("Username: admin")
    print("Password: admin123")
    print("Email: admin@example.com")
    print("="*50)
    print("Access Django Admin at: http://127.0.0.1:5000/admin/")

if __name__ == '__main__':
    create_admin_user()