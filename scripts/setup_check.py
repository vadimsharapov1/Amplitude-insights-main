#!/usr/bin/env python3
"""
Setup Validation for Amplitude Data Extraction Tool
Validates configuration and security setup
"""

import os
import json
from pathlib import Path
import requests
from config import get_amplitude_credentials

def print_status(message, success=True):
    """Print a colored status message"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print an info message"""
    print(f"ℹ️  {message}")

def check_dependencies():
    """Check if required Python packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = ['requests', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_status(f"Package '{package}' is installed")
        except ImportError:
            missing_packages.append(package)
            print_status(f"Package '{package}' is missing", False)
    
    if missing_packages:
        print_info(f"Install missing packages with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Checking environment configuration...")
    
    # Check .env file exists
    if not os.path.exists('.env'):
        print_status(".env file not found", False)
        print_info("Create .env file from template: cp .env.template .env")
        return False
    
    print_status(".env file exists")
    
    # Check credentials are set
    try:
        api_key, secret_key = get_amplitude_credentials()
        if api_key and secret_key:
            print_status("API credentials are configured")
            return True
        else:
            print_status("API credentials are missing", False)
            print_info("Edit .env file and add your Amplitude API credentials")
            return False
    except Exception as e:
        print_status(f"Error loading configuration: {e}", False)
        return False

def check_user_data():
    """Check user data configuration"""
    print("\n👥 Checking user data configuration...")
    
    if not os.path.exists('user_ids/user_ids.txt'):
        print_status("user_ids/user_ids.txt not found", False)
        print_info("Create user file from template: cp user_ids/user_ids.txt.template user_ids/user_ids.txt")
        return False
    
    print_status("user_ids/user_ids.txt exists")
    
    # Read and validate format
    try:
        with open('user_ids/user_ids.txt', 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not lines:
            print_status("No user IDs found in user_ids/user_ids.txt", False)
            print_info("Add user IDs in format: UserID|StartDate|EndDate")
            return False
        
        valid_lines = 0
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 2:  # At least UserID and StartDate
                valid_lines += 1
        
        if valid_lines == 0:
            print_status("No valid user entries found", False)
            print_info("Use format: UserID|StartDate|EndDate")
            return False
        
        print_status(f"Found {valid_lines} valid user entries")
        return True
        
    except Exception as e:
        print_status(f"Error reading user_ids/user_ids.txt: {e}", False)
        return False

def check_folder_structure():
    """Check folder structure and .gitkeep files"""
    print("\n📁 Checking folder structure...")
    
    required_folders = [
        'userData',
        'userData/userData_raw',
        'userData/userData_clean', 
        'userData/userData_isolate',
        'Events',
        'Product_notes',
        'Test',
        'Test/test_userData'
    ]
    
    all_good = True
    for folder in required_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            print_status(f"Folder '{folder}' exists")
            
            # Check for .gitkeep in empty folders
            if folder in ['Events', '']:
                gitkeep_path = folder_path / '.gitkeep'
                if gitkeep_path.exists():
                    print_status(f"  .gitkeep file present in {folder}")
                else:
                    print_warning(f"  .gitkeep file missing in {folder}")
        else:
            print_status(f"Folder '{folder}' missing", False)
            folder_path.mkdir(parents=True, exist_ok=True)
            print_info(f"Created folder: {folder}")
    
    # Check Product_notes README exists
    product_readme = Path('Product_notes/README.md')
    if product_readme.exists():
        print_status("Product_notes/README.md exists (public)")
    else:
        print_status("Product_notes/README.md missing", False)
        print_info("The public guide for Product_notes is missing")
        all_good = False
    
    return all_good

def check_git_protection():
    """Check git ignore protection"""
    print("\n🛡️  Checking git protection...")
    
    if not os.path.exists('.gitignore'):
        print_status(".gitignore file missing", False)
        print_info("Git ignore protection not configured")
        return False
    
    print_status(".gitignore file exists")
    
    # Check protected files
    protected_patterns = [
        '.env',
        'user_ids.txt',
        'userData/**/*.json',
        'Events/*',
        'Product_notes/*'
    ]
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    protected_count = 0
    for pattern in protected_patterns:
        if pattern in gitignore_content:
            protected_count += 1
            print_status(f"  Protected: {pattern}")
        else:
            print_status(f"  Not protected: {pattern}", False)
    
    # Check Product_notes exception
    if '!Product_notes/README.md' in gitignore_content:
        print_status("  Exception: Product_notes/README.md (public)")
    else:
        print_status("  Missing exception for Product_notes/README.md", False)
    
    if protected_count == len(protected_patterns):
        print_status("All sensitive files are protected")
        return True
    else:
        print_status(f"Only {protected_count}/{len(protected_patterns)} patterns protected", False)
        return False

def test_api_connection():
    """Test Amplitude API connection"""
    print("\n🌐 Testing API connection...")
    
    try:
        api_key, secret_key = get_amplitude_credentials()
        if not (api_key and secret_key):
            print_status("Skipping API test - credentials not configured", False)
            return False
        
        # Test with a simple API call
        url = "https://amplitude.com/api/2/export"
        params = {
            'start': '20250101T00',
            'end': '20250101T01'
        }
        
        response = requests.get(
            url,
            params=params,
            auth=(api_key, secret_key),
            timeout=10
        )
        
        if response.status_code == 200:
            print_status("API connection successful")
            return True
        elif response.status_code == 401:
            print_status("API authentication failed - check credentials", False)
            return False
        else:
            print_status(f"API returned status {response.status_code}", False) 
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"API connection failed: {e}", False)
        return False
    except Exception as e:
        print_status(f"Error testing API: {e}", False)
        return False

def main():
    """Run all validation checks"""
    print("🚀 Amplitude Data Extraction Tool - Setup Validation\n")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment", check_environment), 
        ("User Data", check_user_data),
        ("Folder Structure", check_folder_structure),
        ("Git Protection", check_git_protection),
        ("API Connection", test_api_connection)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_status(f"Check '{check_name}' failed with error: {e}", False)
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📋 VALIDATION SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        print_status(f"{check_name}: {'PASS' if result else 'FAIL'}", result)
    
    print(f"\n🎯 Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! You're ready to run the data extraction.")
        print("🚀 Next step: python main.py")
    else:
        print(f"\n⚠️  {total - passed} issues need attention.")
        print("💡 Run 'python quick_start.py' for automated fixes")
        print("📚 Check the README.md for manual setup instructions")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 