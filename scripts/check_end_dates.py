import os
import json
import re
from datetime import datetime, timedelta

def parse_date(date_str):
    """Parse date in format 'May 16, 2025', 'Jun 16, 2025', or detailed format"""
    try:
        # First try abbreviated month format: 'Jun 16, 2025'
        try:
            parsed_date = datetime.strptime(date_str.strip(), '%b %d, %Y')
            return parsed_date
        except ValueError:
            pass
        
        # Then try full month format: 'May 16, 2025'
        try:
            parsed_date = datetime.strptime(date_str.strip(), '%B %d, %Y')
            return parsed_date
        except ValueError:
            pass
        
        # If simple formats fail, try detailed format with timezone
        # Remove timezone info for parsing (we'll assume it's close enough)
        date_part = re.sub(r'\s+GMT[+-]\d+$', '', date_str)
        
        # Parse the detailed date format
        parsed_date = datetime.strptime(date_part, '%B %d, %Y %I:%M:%S.%f %p')
        return parsed_date
    except ValueError as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def get_expected_end_dates():
    """Read user_ids.txt and return expected end dates for each user"""
    expected_end_dates = {}
    
    try:
        with open('user_ids/user_ids.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('# Not Valid'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            user_id = parts[0].strip()
                            last_seen_str = parts[2].strip()
                            last_seen = parse_date(last_seen_str)
                            expected_end_dates[user_id] = {
                                'expected_end': last_seen,
                                'expected_end_str': last_seen_str
                            }
    except FileNotFoundError:
        print("user_ids/user_ids.txt not found")
    
    return expected_end_dates

def get_actual_last_event_dates():
    """Get the last event date from each user file in userData_raw folder"""
    actual_last_dates = {}
    userData_dir = 'userData/userData_raw'
    
    if not os.path.exists(userData_dir):
        return actual_last_dates
        
    for filename in os.listdir(userData_dir):
        if filename.startswith('user_') and filename.endswith('.json'):
            # Extract user ID from filename: user_{userID}_events_{start}_to_{end}.json
            match = re.match(r'user_(.+)_events_(\d{8})_to_(\d{8})\.json', filename)
            if match:
                user_id = match.group(1)
                
                try:
                    with open(f'{userData_dir}/{filename}', 'r') as f:
                        data = json.load(f)
                        
                    if data:
                        # Get last event time
                        last_event_time = data[-1].get('event_time', '')
                        
                        # Parse date from event_time
                        if last_event_time:
                            try:
                                last_date = datetime.strptime(last_event_time[:10], '%Y-%m-%d')
                                actual_last_dates[user_id] = {
                                    'actual_last': last_date,
                                    'filename': filename,
                                    'total_events': len(data)
                                }
                            except:
                                print(f"Error parsing event time '{last_event_time}' in {filename}")
                        
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    
    return actual_last_dates

def main():
    expected_end_dates = get_expected_end_dates()
    actual_last_dates = get_actual_last_event_dates()
    
    print("=== END DATE VERIFICATION REPORT ===")
    print(f"Expected users: {len(expected_end_dates)}")
    print(f"Actual files: {len(actual_last_dates)}")
    print()
    
    correct_end_dates = []
    incorrect_end_dates = []
    missing_files = []
    
    # Check each expected user
    for user_id, expected in expected_end_dates.items():
        if user_id not in actual_last_dates:
            missing_files.append(user_id)
            print(f"❌ MISSING FILE: {user_id}")
            continue
            
        actual = actual_last_dates[user_id]
        expected_end = expected['expected_end']
        actual_last = actual['actual_last']
        
        if expected_end and actual_last:
            # Calculate difference in days
            days_diff = (actual_last.date() - expected_end.date()).days
            
            # Check if within ±2 days
            if abs(days_diff) <= 2:
                correct_end_dates.append(user_id)
                status = "✅"
                if days_diff == 0:
                    diff_str = "exact match"
                elif days_diff > 0:
                    diff_str = f"+{days_diff} day{'s' if days_diff != 1 else ''}"
                else:
                    diff_str = f"{days_diff} day{'s' if abs(days_diff) != 1 else ''}"
                    
                print(f"{status} CORRECT: {user_id}")
                print(f"   Expected: {expected_end.strftime('%Y-%m-%d')}, Actual: {actual_last.strftime('%Y-%m-%d')} ({diff_str})")
                print(f"   File: {actual['filename']} ({actual['total_events']} events)")
            else:
                incorrect_end_dates.append({
                    'user_id': user_id,
                    'expected_end': expected_end,
                    'actual_last': actual_last,
                    'days_diff': days_diff,
                    'expected_str': expected['expected_end_str'],
                    'filename': actual['filename']
                })
                print(f"❌ INCORRECT END DATE: {user_id}")
                print(f"   Expected: {expected_end.strftime('%Y-%m-%d')}, Actual: {actual_last.strftime('%Y-%m-%d')}")
                print(f"   Difference: {days_diff} days (outside ±2 day tolerance)")
                print(f"   File: {actual['filename']} ({actual['total_events']} events)")
        else:
            print(f"⚠️  PARSE ERROR: {user_id} (could not parse dates)")
        
        print()
    
    print("=== SUMMARY ===")
    print(f"✅ Correct end dates (within ±2 days): {len(correct_end_dates)}")
    print(f"❌ Incorrect end dates (outside ±2 days): {len(incorrect_end_dates)}")
    print(f"❌ Missing files: {len(missing_files)}")
    
    if incorrect_end_dates:
        print(f"\nUsers with incorrect end dates:")
        for item in incorrect_end_dates:
            print(f"  - {item['user_id']}: expected {item['expected_end'].strftime('%Y-%m-%d')}, got {item['actual_last'].strftime('%Y-%m-%d')} ({item['days_diff']} days diff)")
    
    if missing_files:
        print(f"\nMissing files: {missing_files}")
    
    return correct_end_dates, incorrect_end_dates, missing_files

if __name__ == "__main__":
    correct, incorrect, missing = main() 