# ==========================================
# SESSION CONTEXT MANAGER
# ==========================================
# This module manages the current session context
# (selected user file and corresponding directory paths)

import os
import json
from datetime import datetime

# Global session context
_current_session = None

def set_session_context(user_file, raw_dir, clean_dir, isolate_dir):
    """Set the current session context"""
    global _current_session
    _current_session = {
        'user_file': user_file,
        'raw_dir': raw_dir,
        'clean_dir': clean_dir,
        'isolate_dir': isolate_dir,
        'session_name': os.path.splitext(os.path.basename(user_file))[0] + '_' + datetime.now().strftime("%Y-%m-%d")
    }

def get_session_context():
    """Get the current session context"""
    return _current_session

def get_user_file():
    """Get the current user file path"""
    if _current_session:
        return _current_session['user_file']
    return None

def get_raw_dir():
    """Get the current raw data directory"""
    if _current_session:
        return _current_session['raw_dir']
    return 'userData/userData_raw'  # fallback

def get_clean_dir():
    """Get the current clean data directory"""
    if _current_session:
        return _current_session['clean_dir']
    return 'userData/userData_clean'  # fallback

def get_isolate_dir():
    """Get the current isolate data directory"""
    if _current_session:
        return _current_session['isolate_dir']
    return 'userData/userData_isolate'  # fallback

def get_session_name():
    """Get the current session name"""
    if _current_session:
        return _current_session['session_name']
    return 'default_session'

def save_session_context():
    """Save session context to file for script communication"""
    if _current_session:
        with open('.session_context.json', 'w') as f:
            json.dump(_current_session, f)

def load_session_context():
    """Load session context from file"""
    global _current_session
    try:
        if os.path.exists('.session_context.json'):
            with open('.session_context.json', 'r') as f:
                _current_session = json.load(f)
                return True
    except Exception:
        pass
    return False

def clear_session_context():
    """Clear session context and temporary files"""
    global _current_session
    _current_session = None
    if os.path.exists('.session_context.json'):
        os.remove('.session_context.json')

def get_session_directories():
    """Get all session directories (raw, clean, isolate)"""
    if ensure_session_context():
        return get_raw_dir(), get_clean_dir(), get_isolate_dir()
    return None, None, None

def ensure_session_context():
    """Ensure session context is available, try to load if not set"""
    if not _current_session:
        return load_session_context()
    return True 