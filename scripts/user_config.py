# ==========================================
# USER CONFIGURATION - SAFE FOR GIT COMMITS
# ==========================================

# This file is safe to commit - it contains no actual credentials
# Your actual API credentials are loaded from .env file or environment variables

import os
from datetime import datetime
import glob

# ==========================================
# SECURE CREDENTIAL LOADING
# ==========================================

def get_amplitude_credentials():
    """Get Amplitude API credentials from environment variables or .env file"""
    
    # Try to load from .env file first
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    # Get credentials from environment variables
    api_key = os.environ.get('AMPLITUDE_API_KEY')
    secret_key = os.environ.get('AMPLITUDE_SECRET_KEY')
    
    # Check if credentials are configured
    if not api_key or not secret_key or api_key == "your_api_key_here" or secret_key == "your_secret_key_here":
        raise ValueError(
            "🔒 AMPLITUDE API CREDENTIALS NOT CONFIGURED\n\n"
            "Please create a .env file in the project root with:\n"
            "AMPLITUDE_API_KEY=your_actual_api_key\n"
            "AMPLITUDE_SECRET_KEY=your_actual_secret_key\n\n"
            "Or set these as environment variables.\n"
            "Get your keys from: Amplitude → Settings → API Keys"
        )
    
    return api_key, secret_key

# ==========================================
# CONFIGURATION SETTINGS
# ==========================================

# STEP 2: User IDs folder configuration
USER_IDS_FOLDER = "user_ids/"

# STEP 3: Base output directory (dynamic subfolders will be created)
BASE_OUTPUT_DIR = "userData"

# ==========================================
# ADVANCED SETTINGS (optional)
# ==========================================

# Default date format for parsing
DEFAULT_DATE_FORMAT = "%B %d, %Y"  # e.g., "May 16, 2025"

# Safety buffer (days to subtract from start date)
DATE_SAFETY_BUFFER = 1

# Maximum events per user (0 = no limit)
MAX_EVENTS_PER_USER = 0

# Timeout for API requests (seconds)
REQUEST_TIMEOUT = 30

# ==========================================
# FILE MANAGEMENT FUNCTIONS
# ==========================================

def get_available_user_files():
    """Get list of available .txt files in user_ids folder and tests directory"""
    user_files = []
    
    # Check main user_ids folder
    pattern = os.path.join(USER_IDS_FOLDER, "*.txt")
    files = glob.glob(pattern)
    # Filter out template files and add with source info
    for f in files:
        if not f.endswith('.template'):
            user_files.append({
                'name': os.path.basename(f),
                'path': f,
                'source': 'user_ids'
            })
    
    # Check tests directory
    test_pattern = "tests/Test/*.txt"
    test_files = glob.glob(test_pattern)
    for f in test_files:
        if not f.endswith('.template'):
            user_files.append({
                'name': f"[TEST] {os.path.basename(f)}",
                'path': f,
                'source': 'tests'
            })
    
    return user_files

def select_user_file():
    """Interactive file selection from available user files"""
    available_files = get_available_user_files()
    
    if not available_files:
        raise ValueError(f"No .txt files found in {USER_IDS_FOLDER} folder or tests directory!")
    
    if len(available_files) == 1:
        selected_file = available_files[0]
        print(f"📁 Found 1 user file: {selected_file['name']}")
        print(f"✅ Using: {selected_file['name']}")
        return selected_file['path']
    
    print(f"\n📁 Found {len(available_files)} user files:")
    for i, file_info in enumerate(available_files, 1):
        source_label = "🧪 TEST" if file_info['source'] == 'tests' else "📁 MAIN"
        print(f"  {i}. {file_info['name']} ({source_label})")
    
    while True:
        try:
            choice = input(f"\nSelect file (1-{len(available_files)}): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(available_files):
                selected_file = available_files[index]
                print(f"✅ Selected: {selected_file['name']}")
                return selected_file['path']
            else:
                print(f"❌ Please enter a number between 1 and {len(available_files)}")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Operation cancelled or invalid input")
            return None

def get_user_ids_file():
    """Get path to selected user IDs file"""
    selected_file = select_user_file()
    if not selected_file:
        return None
    return selected_file  # select_user_file() already returns the complete path

def get_session_folder_name(user_file):
    """Interactive folder name selection for session data"""
    if not user_file:
        return None
    
    print(f"\n📁 FOLDER SELECTION")
    print("=" * 50)
    
    # Show existing folders in userData directory
    userData_dir = BASE_OUTPUT_DIR
    existing_folders = []
    if os.path.exists(userData_dir):
        existing_folders = [d for d in os.listdir(userData_dir) 
                          if os.path.isdir(os.path.join(userData_dir, d))]
    
    if existing_folders:
        print(f"📂 Existing folders in {userData_dir}:")
        for i, folder in enumerate(existing_folders, 1):
            print(f"  {i}. {folder}")
        print()
    
    while True:
        folder_name = input("Enter folder name for this session: ").strip()
        
        if not folder_name:
            print("❌ Folder name cannot be empty. Please try again.")
            continue
            
        # Remove any invalid characters
        import re
        folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
        
        if folder_name in existing_folders:
            print(f"⚠️  Folder '{folder_name}' already exists.")
            overwrite = input("Do you want to overwrite it? (y/n): ").strip().lower()
            if overwrite in ['y', 'yes']:
                print(f"🗑️  Will overwrite existing folder: {folder_name}")
                return folder_name
            else:
                print("Please choose a different name.")
                continue
        else:
            print(f"✅ Will create new folder: {folder_name}")
            return folder_name

def get_output_directories(user_file):
    """Get output directory paths based on selected user file"""
    session_name = get_session_folder_name(user_file)
    if not session_name:
        return None, None, None
    
    session_dir = os.path.join(BASE_OUTPUT_DIR, session_name)
    raw_dir = os.path.join(session_dir, "userData_raw")
    clean_dir = os.path.join(session_dir, "userData_clean")
    isolate_dir = os.path.join(session_dir, "userData_isolate")
    
    return raw_dir, clean_dir, isolate_dir

def ensure_output_directories(user_file):
    """Create output directories, clearing existing files if overwriting"""
    raw_dir, clean_dir, isolate_dir = get_output_directories(user_file)
    if raw_dir and clean_dir and isolate_dir:
        # Check if directories exist and clear them if they do
        import shutil
        
        for directory in [raw_dir, clean_dir, isolate_dir]:
            if os.path.exists(directory):
                print(f"🗑️  Clearing existing files in: {os.path.basename(directory)}")
                shutil.rmtree(directory)
            os.makedirs(directory, exist_ok=True)
        
        print(f"📁 Session directories ready in: {os.path.dirname(raw_dir)}")
        print(f"   📂 Raw data: {os.path.basename(raw_dir)}")
        print(f"   📂 Clean data: {os.path.basename(clean_dir)}")
        print(f"   📂 Isolated data: {os.path.basename(isolate_dir)}")
        return raw_dir, clean_dir, isolate_dir
    return None, None, None 