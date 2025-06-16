#!/usr/bin/env python3
"""
Quick Start Setup Script for Amplitude Data Extraction Tool

This script automates the initial setup process for new users.
It creates the necessary configuration files and guides you through setup.

Usage: python quick_start.py
"""

import os
import sys
from pathlib import Path

def print_header():
    """Print welcome header"""
    print("🚀 Amplitude Data Extraction Tool - Quick Start Setup")
    print("=" * 60)
    print("This script will help you set up the tool in 3 simple steps.\n")

def setup_env_file():
    """Guide user through .env file setup"""
    print("📝 Step 1: API Credentials Setup")
    print("-" * 40)
    
    if Path('.env').exists():
        print("✅ .env file already exists!")
        return True
    
    if not Path('.env.template').exists():
        print("❌ .env.template not found!")
        return False
    
    print("Creating .env file from template...")
    
    # Copy template to .env
    with open('.env.template', 'r') as template:
        content = template.read()
    
    with open('.env', 'w') as env_file:
        env_file.write(content)
    
    print("✅ Created .env file")
    print("\n📋 Next steps:")
    print("1. Open .env file in your text editor")
    print("2. Replace 'your_api_key_here' with your actual Amplitude API key")
    print("3. Replace 'your_secret_key_here' with your actual Amplitude secret key")
    print("\n💡 Get your keys from: Amplitude → Settings → API Keys")
    
    return True

def setup_user_file():
    """Guide user through user_ids.txt setup"""
    print("\n👥 Step 2: User Data Setup")
    print("-" * 40)
    
    if Path('user_ids/user_ids.txt').exists():
        print("✅ user_ids/user_ids.txt file already exists!")
        return True
    
    if not Path('user_ids/user_ids.txt.template').exists():
        print("❌ user_ids/user_ids.txt.template not found!")
        return False
    
    print("Creating user_ids.txt file from template...")
    
    # Copy template to user_ids.txt  
    with open('user_ids/user_ids.txt.template', 'r') as template:
        content = template.read()
    
    with open('user_ids/user_ids.txt', 'w') as user_file:
        user_file.write(content)
    
    print("✅ Created user_ids.txt file")
    print("\n📋 Next steps:")
    print("1. Open user_ids.txt file in your text editor") 
    print("2. Replace 'your_user_id_here' with actual user IDs")
    print("3. Add date ranges in format: UserID|StartDate|EndDate")
    print("\n💡 Example: user123|May 1, 2025|June 15, 2025")
    
    return True

def run_validation():
    """Run setup validation"""
    print("\n🔍 Step 3: Validation")
    print("-" * 40)
    
    if not Path('setup_check.py').exists():
        print("⚠️  setup_check.py not found, skipping validation")
        return True
    
    print("Running setup validation...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'setup_check.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Setup validation passed!")
            return True
        else:
            print("⚠️  Setup validation found issues:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"⚠️  Could not run validation: {e}")
        return False

def main():
    """Main setup workflow"""
    print_header()
    
    # Step 1: Environment setup
    env_success = setup_env_file()
    
    # Step 2: User data setup  
    user_success = setup_user_file()
    
    # Step 3: Validation
    validation_success = run_validation()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Setup Summary")
    print("=" * 60)
    
    if env_success and user_success:
        print("✅ Configuration files created successfully!")
        print("\n📝 Manual steps required:")
        print("1. Edit .env with your Amplitude API credentials")
        print("2. Edit user_ids.txt with your user IDs and date ranges")
        
        if validation_success:
            print("\n🎉 Ready to run! Next steps:")
            print("   ▶️  python main.py")
        else:
            print("\n🔧 After editing the files, validate your setup:")
            print("   ▶️  python setup_check.py")
            print("   ▶️  python main.py")
    else:
        print("❌ Setup encountered issues. Please check the errors above.")
        return False
    
    print("\n📖 For detailed instructions, see README.md")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 