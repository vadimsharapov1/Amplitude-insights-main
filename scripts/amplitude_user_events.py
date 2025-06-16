import requests
import json
import zipfile
import gzip
from datetime import datetime, timedelta
from io import BytesIO
import base64
import os
import re

class AmplitudeAPI:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://amplitude.com/api/2/export"
        
        # Create base64 encoded credentials for Basic Auth
        credentials = f"{api_key}:{secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}'
        }

    def filter_event_fields(self, event, fields_to_keep=None, fields_to_exclude=None):
        """Filter event fields based on inclusion/exclusion lists"""
        if fields_to_keep:
            # Only keep specified fields
            filtered_event = {field: event.get(field) for field in fields_to_keep if field in event}
            
            # Special handling for af_status - extract from user_properties if needed
            if 'af_status' in fields_to_keep and 'af_status' not in filtered_event:
                user_props = event.get('user_properties', {})
                if isinstance(user_props, dict) and 'af_status' in user_props:
                    filtered_event['af_status'] = user_props['af_status']
            
            return filtered_event
        elif fields_to_exclude:
            # Exclude specified fields
            return {field: value for field, value in event.items() if field not in fields_to_exclude}
        else:
            # Return all fields if no filtering specified
            return event

    def download_export_for_hour(self, date_str, hour):
        """Download export for a specific hour"""
        start_time = f"{date_str}T{hour:02d}"
        end_time = f"{date_str}T{hour:02d}"
        
        url = f"{self.base_url}?start={start_time}&end={end_time}"
        print(f"Requesting: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"Successfully downloaded data for {start_time} (Size: {len(response.content)} bytes)")
                return BytesIO(response.content)
            elif response.status_code == 404:
                print(f"No data available for {start_time}")
                return None
            else:
                print(f"Error downloading {start_time}: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {start_time}: {e}")
            return None

    def download_exports_for_date(self, date_str):
        """Download all hourly exports for a given date"""
        zip_files = []
        
        # Try each hour of the day
        for hour in range(24):
            zip_data = self.download_export_for_hour(date_str, hour)
            if zip_data:
                zip_files.append(zip_data)
        
        return zip_files

    def extract_events_from_zip(self, zip_data, fields_to_keep=None, fields_to_exclude=None):
        """Extract events from a single ZIP file with optional field filtering"""
        events = []
        
        try:
            with zipfile.ZipFile(zip_data) as z:
                print(f"ZIP contains files: {z.namelist()}")
                
                for filename in z.namelist():
                    print(f"Processing file: {filename}")
                    
                    with z.open(filename) as f:
                        # Check if file is gzipped
                        if filename.endswith('.gz'):
                            content = gzip.decompress(f.read()).decode('utf-8')
                        else:
                            content = f.read().decode('utf-8')
                        
                        # Parse JSON lines
                        for line_num, line in enumerate(content.strip().split('\n'), 1):
                            if line.strip():
                                try:
                                    event = json.loads(line)
                                    # Apply field filtering
                                    filtered_event = self.filter_event_fields(event, fields_to_keep, fields_to_exclude)
                                    events.append(filtered_event)
                                except json.JSONDecodeError as e:
                                    print(f"JSON decode error in {filename} line {line_num}: {e}")
                                    continue
                        
                        lines = [l for l in content.strip().split('\n') if l.strip()]
                        print(f"Extracted {len(lines)} events from {filename}")
                        
        except zipfile.BadZipFile:
            print("Invalid ZIP file received")
        except Exception as e:
            print(f"Error extracting ZIP: {e}")
            
        return events

    def filter_events_by_user(self, events, user_id):
        """Filter events for a specific user ID"""
        user_events = []
        
        for event in events:
            # Check multiple possible user identifier fields
            if (event.get('user_id') == user_id or 
                str(event.get('amplitude_id')) == str(user_id) or
                event.get('device_id') == user_id or
                event.get('uuid') == user_id):
                user_events.append(event)
        
        return user_events

    def get_all_events_for_date_range(self, start_date, end_date, fields_to_keep=None, fields_to_exclude=None, user_id_for_filtering=None):
        """Get all events for a date range with optional field filtering"""
        all_events = []
        
        # If we're filtering by user and using fields_to_keep, temporarily add user ID fields for filtering
        temp_fields_to_keep = fields_to_keep
        if user_id_for_filtering and fields_to_keep:
            temp_fields_to_keep = list(fields_to_keep) + ['user_id', 'amplitude_id', 'device_id', 'uuid']
            # Remove duplicates
            temp_fields_to_keep = list(set(temp_fields_to_keep))
        
        current = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        while current <= end:
            date_str = current.strftime('%Y%m%d')
            print(f"\n=== Processing date: {date_str} ===")
            
            zip_files = self.download_exports_for_date(date_str)
            
            for zip_data in zip_files:
                events = self.extract_events_from_zip(zip_data, temp_fields_to_keep, fields_to_exclude)
                all_events.extend(events)
                print(f"Total events so far: {len(all_events)}")
            
            current += timedelta(days=1)
        
        # If we added temporary fields for user filtering, filter by user first, then remove the temp fields
        if user_id_for_filtering and fields_to_keep and temp_fields_to_keep != fields_to_keep:
            # Filter by user first
            user_events = self.filter_events_by_user(all_events, user_id_for_filtering)
            
            # Then remove the temporary user ID fields from each event
            final_events = []
            for event in user_events:
                final_event = {field: event.get(field) for field in fields_to_keep if field in event}
                final_events.append(final_event)
            
            return final_events
        
        return all_events

def parse_date(date_str):
    """Parse date in format 'May 16, 2025' or 'June 11, 2025 1:32:45.275 PM GMT+2'"""
    try:
        # First try simple format: 'May 16, 2025'
        try:
            parsed_date = datetime.strptime(date_str.strip(), '%B %d, %Y')
            return parsed_date
        except ValueError:
            pass
        
        # If simple format fails, try detailed format with timezone
        # Remove timezone info for parsing (we'll assume it's close enough)
        date_part = re.sub(r'\s+GMT[+-]\d+$', '', date_str)
        
        # Parse the detailed date format
        parsed_date = datetime.strptime(date_part, '%B %d, %Y %I:%M:%S.%f %p')
        return parsed_date
    except ValueError as e:
        print(f"Error parsing date '{date_str}': {e}")
        print("Supported formats: 'May 16, 2025' or 'June 11, 2025 1:32:45.275 PM GMT+2'")
        return None

def calculate_days_back(creation_date, current_date):
    """Calculate days back from creation date to current date + 1 extra day for safety"""
    if not creation_date:
        return 3  # Default fallback
    
    days_diff = (current_date - creation_date).days
    # Add 1 extra day for safety as requested
    days_back = max(1, days_diff + 1)
    return days_back

def main():
    # Import config for secure credential loading
    import sys
    import os
    sys.path.append('.')
    from scripts.user_config import get_amplitude_credentials
    from session_context import ensure_session_context, get_user_file, get_raw_dir
    
    try:
        API_KEY, SECRET_KEY = get_amplitude_credentials()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return
    
    # Get session context (set by main.py)
    if not ensure_session_context():
        print("❌ No session context found. Please run through main.py")
        return
    
    user_file = get_user_file()
    raw_dir = get_raw_dir()
    
    if not user_file or not raw_dir:
        print("❌ Invalid session context")
        return
    
    amplitude = AmplitudeAPI(API_KEY, SECRET_KEY)
    
    print("=== Amplitude Export API Test ===")
    print(f"📁 Using user file: {os.path.basename(user_file)}")
    print(f"📁 Output directory: {raw_dir}")
    
    # Configuration – edit these constants if you need to customise behaviour
    DEFAULT_DAYS_BACK = 3  # default fallback if no creation date provided

    fields_to_keep = None  # keep all fields; create_clean_json.py will do final filtering
    fields_to_exclude = None
    
    # Read user IDs and date ranges from selected file
    user_data = []
    try:
        with open(user_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Check format: UserID|FirstSeen|LastSeen or UserID|FirstSeen or UserID
                    if '|' in line:
                        parts = line.split('|')
                        user_id = parts[0].strip()
                        
                        if len(parts) == 3:
                            # New format: UserID|FirstSeen|LastSeen
                            first_seen_str = parts[1].strip()
                            last_seen_str = parts[2].strip()
                            first_seen = parse_date(first_seen_str)
                            last_seen = parse_date(last_seen_str)
                            user_data.append((user_id, first_seen, last_seen, first_seen_str, last_seen_str))
                        elif len(parts) == 2:
                            # Legacy format: UserID|CreationDate (treat as FirstSeen only)
                            creation_date_str = parts[1].strip()
                            creation_date = parse_date(creation_date_str)
                            user_data.append((user_id, creation_date, None, creation_date_str, None))
                    else:
                        # Old format - just user ID
                        user_data.append((line, None, None, None, None))
    except FileNotFoundError:
        print("user_ids.txt not found. Will download all events.")
    
    if not user_data:
        print("No user IDs specified. Downloading all events.")
        user_data = [("", None, None, None, None)]  # Empty string means all users
    else:
        print(f"Found {len(user_data)} users to process")
    
    current_date = datetime.now()
    
    # Process each user with individual date ranges
    for user_id, first_seen, last_seen, first_seen_str, last_seen_str in user_data:
        print(f"\n{'='*50}")
        if user_id:
            print(f"Processing user: {user_id}")
            if first_seen_str:
                print(f"First seen: {first_seen_str}")
            if last_seen_str:
                print(f"Last seen: {last_seen_str}")
        else:
            print("Processing all events")
        print(f"{'='*50}")
        
        # Calculate date range for this user
        if first_seen and last_seen:
            # Use provided date range: Start Day minus 1, End Day (inclusive)
            start_date = first_seen - timedelta(days=1)  # Start 1 day before for safety
            end_date = last_seen  # End date is inclusive
            print(f"Original range: {first_seen.strftime('%Y-%m-%d')} to {last_seen.strftime('%Y-%m-%d')}")
            print(f"Actual scraping: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (start minus 1 day for safety)")
        elif first_seen:
            # Use first_seen minus 1 day as start date, current date as end date
            start_date = first_seen - timedelta(days=1)  # Start 1 day before for safety
            end_date = current_date
            print(f"Original start: {first_seen.strftime('%Y-%m-%d')}")
            print(f"Actual scraping: {start_date.strftime('%Y-%m-%d')} to current: {current_date.strftime('%Y-%m-%d')} (start minus 1 day for safety)")
        else:
            # Use default behavior
            days_back = DEFAULT_DAYS_BACK
            print(f"Using default DAYS_BACK: {days_back} (no dates provided)")
            end_date = current_date
            start_date = end_date - timedelta(days=days_back)
        
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        print(f"Fetching events for date range {start_date_str} to {end_date_str}")
        
        # Get all events
        all_events = amplitude.get_all_events_for_date_range(
            start_date_str, end_date_str, fields_to_keep, fields_to_exclude, user_id
        )
        
        if not all_events:
            print(f"No events found for {'user ' + user_id if user_id else 'any users'}")
            continue
        
        print(f"Total events retrieved: {len(all_events)}")
        
        # Save events
        if user_id:
            # Filter by user if specified
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
        else:
            # Save all events
            filename = f"{raw_dir}/all_events_{start_date_str}_to_{end_date_str}.json"
            with open(filename, 'w') as f:
                json.dump(all_events, f, indent=2)
            print(f"All events saved to {filename}")
            
            # Show sample event
            if all_events:
                print(f"Sample event:")
                print(json.dumps(all_events[0], indent=2)[:500] + "...")

if __name__ == "__main__":
    main() 