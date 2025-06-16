import os
import json
import re
from datetime import datetime
import sys
sys.path.append('.')
from session_context import ensure_session_context, get_user_file, get_raw_dir

def parse_date(date_str):
    """Parse date in format 'May 16, 2025'"""
    try:
        return datetime.strptime(date_str.strip(), '%B %d, %Y')
    except ValueError:
        return None

def get_expected_users():
    """Read selected user file and return expected users with their date ranges"""
    expected_users = {}
    
    if not ensure_session_context():
        print("❌ No session context found. Please run through main.py")
        return expected_users
    
    user_file = get_user_file()
    if not user_file:
        print("❌ No user file in session context")
        return expected_users
    
    try:
        with open(user_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('# Not Valid'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            user_id = parts[0].strip()
                            first_seen_str = parts[1].strip()
                            last_seen_str = parts[2].strip()
                            first_seen = parse_date(first_seen_str)
                            last_seen = parse_date(last_seen_str)
                            expected_users[user_id] = {
                                'first_seen': first_seen,
                                'last_seen': last_seen,
                                'first_seen_str': first_seen_str,
                                'last_seen_str': last_seen_str
                            }
    except FileNotFoundError:
        print(f"User file not found: {user_file}")
    
    return expected_users

def get_actual_files():
    """Get list of actual user files in current session's raw folder"""
    actual_files = {}
    
    if not ensure_session_context():
        return actual_files
    
    userData_dir = get_raw_dir()
    
    if os.path.exists(userData_dir):
        for filename in os.listdir(userData_dir):
            if filename.startswith('user_') and filename.endswith('.json'):
                # Extract user ID from filename: user_{userID}_events_{start}_to_{end}.json
                match = re.match(r'user_(.+)_events_(\d{8})_to_(\d{8})\.json', filename)
                if match:
                    user_id = match.group(1)
                    start_date = match.group(2)
                    end_date = match.group(3)
                    actual_files[user_id] = {
                        'filename': filename,
                        'start_date': start_date,
                        'end_date': end_date
                    }
    
    return actual_files

def check_file_date_range(filename):
    """Check the actual first and last event dates in a JSON file"""
    try:
        raw_dir = get_raw_dir()
        with open(f'{raw_dir}/{filename}', 'r') as f:
            data = json.load(f)
            
        if not data:
            return None, None
            
        # Get first and last event times
        first_event_time = data[0].get('event_time', '')
        last_event_time = data[-1].get('event_time', '')
        
        # Parse dates
        first_date = None
        last_date = None
        
        if first_event_time:
            try:
                first_date = datetime.strptime(first_event_time[:10], '%Y-%m-%d')
            except:
                pass
                
        if last_event_time:
            try:
                last_date = datetime.strptime(last_event_time[:10], '%Y-%m-%d')
            except:
                pass
                
        return first_date, last_date
        
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None, None

def main():
    expected_users = get_expected_users()
    actual_files = get_actual_files()
    
    print("=== COMPARISON REPORT ===")
    print(f"Expected users: {len(expected_users)}")
    print(f"Actual files: {len(actual_files)}")
    print()
    
    missing_users = []
    incorrect_date_ranges = []
    correct_users = []
    
    # Check each expected user
    for user_id, expected in expected_users.items():
        if user_id not in actual_files:
            missing_users.append(user_id)
            print(f"❌ MISSING: {user_id}")
        else:
            actual = actual_files[user_id]
            
            # Check actual date range in the file
            first_actual, last_actual = check_file_date_range(actual['filename'])
            
            expected_start = expected['first_seen']
            expected_end = expected['last_seen']
            
            # Expected actual start should be expected_start - 1 day
            expected_actual_start = None
            if expected_start:
                from datetime import timedelta
                expected_actual_start = expected_start - timedelta(days=1)
            
            date_range_ok = True
            issues = []
            
            # Check if end date matches (should be exactly the expected end date)
            if expected_end and last_actual:
                if last_actual.date() != expected_end.date():
                    date_range_ok = False
                    issues.append(f"End date mismatch: expected {expected_end.date()}, got {last_actual.date()}")
            
            # Check if start date is reasonable (should be around expected_start - 1)
            if expected_actual_start and first_actual:
                if abs((first_actual.date() - expected_actual_start.date()).days) > 1:
                    date_range_ok = False
                    issues.append(f"Start date unexpected: expected around {expected_actual_start.date()}, got {first_actual.date()}")
            
            if not date_range_ok:
                incorrect_date_ranges.append({
                    'user_id': user_id,
                    'issues': issues,
                    'expected': expected,
                    'actual_file': actual,
                    'actual_dates': (first_actual, last_actual)
                })
                print(f"❌ INCORRECT DATE RANGE: {user_id}")
                for issue in issues:
                    print(f"   {issue}")
            else:
                correct_users.append(user_id)
                print(f"✅ CORRECT: {user_id}")
    
    print("\n=== SUMMARY ===")
    print(f"✅ Correct users: {len(correct_users)}")
    print(f"❌ Missing users: {len(missing_users)}")
    print(f"❌ Incorrect date ranges: {len(incorrect_date_ranges)}")
    
    if missing_users:
        print(f"\nMissing users: {missing_users}")
    
    if incorrect_date_ranges:
        print(f"\nUsers with incorrect date ranges:")
        for item in incorrect_date_ranges:
            print(f"  - {item['user_id']}: {item['issues']}")
    
    return missing_users, incorrect_date_ranges

if __name__ == "__main__":
    missing_users, incorrect_date_ranges = main() 