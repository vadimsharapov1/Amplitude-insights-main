import sys
import os

# Add the current directory to Python path to import the main amplitude module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amplitude_user_events import AmplitudeAPI
import re
from datetime import datetime, timedelta
import json

def parse_date(date_str):
    """Parse date in format 'May 16, 2025', 'Jun 16, 2025', or 'June 11, 2025 1:32:45.275 PM GMT+2'"""
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
        print("Supported formats: 'May 16, 2025', 'Jun 16, 2025', or 'June 11, 2025 1:32:45.275 PM GMT+2'")
        return None

def scrape_specific_users(user_ids_to_scrape):
    """Scrape specific users that are missing"""
    # Import config for secure credential loading
    import sys
    sys.path.append('.')
    from scripts.user_config import get_amplitude_credentials
    from session_context import ensure_session_context, get_raw_dir
    
    try:
        API_KEY, SECRET_KEY = get_amplitude_credentials()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return
    
    # Get session context
    if not ensure_session_context():
        print("❌ No session context found. Using default path.")
        raw_dir = 'userData/userData_raw'
    else:
        raw_dir = get_raw_dir()
    
    amplitude = AmplitudeAPI(API_KEY, SECRET_KEY)
    
    print("=== Scraping Missing Users ===")
    print(f"📁 Output directory: {raw_dir}")
    
    # Configuration
    fields_to_keep = None  # keep all fields
    fields_to_exclude = None
    
    # Ensure raw folder exists
    os.makedirs(raw_dir, exist_ok=True)
    
    # Read user IDs and date ranges from file for the specific users
    user_data = []
    try:
        with open('user_ids/user_ids.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('# Not Valid'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            user_id = parts[0].strip()
                            if user_id in user_ids_to_scrape:
                                first_seen_str = parts[1].strip()
                                last_seen_str = parts[2].strip()
                                first_seen = parse_date(first_seen_str)
                                last_seen = parse_date(last_seen_str)
                                user_data.append((user_id, first_seen, last_seen, first_seen_str, last_seen_str))
    except FileNotFoundError:
        print("user_ids/user_ids.txt not found.")
        return
    
    if not user_data:
        print("No missing users found in user_ids/user_ids.txt")
        return
    
    print(f"Found {len(user_data)} missing users to scrape")
    
    # Process each missing user
    for user_id, first_seen, last_seen, first_seen_str, last_seen_str in user_data:
        print(f"\n{'='*50}")
        print(f"Processing missing user: {user_id}")
        if first_seen_str:
            print(f"First seen: {first_seen_str}")
        if last_seen_str:
            print(f"Last seen: {last_seen_str}")
        print(f"{'='*50}")
        
        # Calculate date range for this user (start date minus 1 day for safety)
        if first_seen and last_seen:
            start_date = first_seen - timedelta(days=1)  # Start 1 day before for safety
            end_date = last_seen  # End date is inclusive
            print(f"Original range: {first_seen.strftime('%Y-%m-%d')} to {last_seen.strftime('%Y-%m-%d')}")
            print(f"Actual scraping: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (start minus 1 day for safety)")
        else:
            print(f"Error: Could not parse dates for user {user_id}")
            continue
        
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        print(f"Fetching events for date range {start_date_str} to {end_date_str}")
        
        # Get all events
        all_events = amplitude.get_all_events_for_date_range(
            start_date_str, end_date_str, fields_to_keep, fields_to_exclude, user_id
        )
        
        if not all_events:
            print(f"No events found for user {user_id}")
            continue
        
        print(f"Total events retrieved: {len(all_events)}")
        
        # Filter by user
        user_events = amplitude.filter_events_by_user(all_events, user_id)
        
        # Always create a user file, even if empty
        filename = f"{raw_dir}/user_{user_id}_events_{start_date_str}_to_{end_date_str}.json"
        with open(filename, 'w') as f:
            json.dump(user_events, f, indent=2)
        
        if user_events:
            print(f"Found {len(user_events)} events for user {user_id}")
            print(f"Events saved to {filename}")
            
            # Show sample event
            print(f"Sample event:")
            print(json.dumps(user_events[0], indent=2)[:500] + "...")
        else:
            print(f"No events found for user ID: {user_id}")
            print(f"Created empty file: {filename}")

if __name__ == "__main__":
    # Example users - replace with your actual missing user IDs
    # These are placeholder values for demonstration
    missing_users = [
        'example_user_id_1',
        'example_user_id_2', 
        'example_user_id_3',
        'example_user_id_4',
        'example_user_id_5',
        'example_user_id_6'
    ]
    
    print("⚠️  TEMPLATE MODE: Replace the example user IDs above with your actual missing user IDs")
    print("This script is currently using placeholder values.")
    print("Edit this file and replace 'example_user_id_X' with real user IDs from your analysis.")
    
    # Uncomment the line below after replacing with real user IDs
    # scrape_specific_users(missing_users) 