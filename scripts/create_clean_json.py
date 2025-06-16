import json
import glob
import os
import re
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from session_context import get_session_directories

def load_events_filter_config():
    """
    Load events filter configuration from config/events_filter.txt
    Returns set of events to include (empty set means include all events)
    """
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'events_filter.txt')
    
    include_events = set()
    
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Add non-comment lines as events to include
                include_events.add(line)
        
        # Provide feedback
        if include_events:
            print(f"📋 Filter mode: INCLUDE only - keeping {len(include_events)} specified events")
            print(f"📥 Events to keep: {sorted(include_events)}")
        else:
            print(f"📋 Filter mode: Keep ALL events (no filtering applied)")
        
        return include_events
        
    except FileNotFoundError:
        print(f"⚠️  Config file not found: {config_file}")
        print("📋 Keeping ALL events (no filtering applied)")
        return set()
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        print("📋 Keeping ALL events (no filtering applied)")
        return set()

def extract_user_data(first_event, user_id):
    """Extract common user-level data from the first event"""
    user_data = {
        "user_id": user_id,
        "country": first_event.get('country'),
        "language": first_event.get('language'),
        "af_status": None,
        "cohort_data": {}
    }
    
    # Extract af_status and cohort data from user_properties
    if 'user_properties' in first_event and isinstance(first_event['user_properties'], dict):
        user_props = first_event['user_properties']
        if 'af_status' in user_props:
            user_data['af_status'] = user_props['af_status']
        
        # Extract cohort data
        cohort_fields = ['cohort_month', 'cohort_year', 'cohort_day', 'cohort_week']
        for field in cohort_fields:
            if field in user_props:
                user_data['cohort_data'][field] = user_props[field]
    
    return user_data

def process_event(event):
    """Process a single event to remove repetitive data"""
    processed_event = {
        "event_type": event.get('event_type'),
        "event_time": event.get('event_time'),
        "event_properties": event.get('event_properties', {})
    }
    
    # Include user_properties but remove the common fields we've grouped
    if 'user_properties' in event and isinstance(event['user_properties'], dict):
        user_props = event['user_properties'].copy()
        # Remove fields that are now grouped at top level
        fields_to_remove = ['af_status', 'cohort_month', 'cohort_year', 'cohort_day', 'cohort_week']
        for field in fields_to_remove:
            user_props.pop(field, None)
        
        # Only include user_properties if there are remaining properties
        if user_props:
            processed_event['user_properties'] = user_props
    
    return processed_event

def process_user_file(user_file, include_events):
    """Process a single user file and return the result"""
    print(f"\nProcessing: {user_file}")
    
    # Extract user ID from filename
    match = re.search(r'user_(.+?)_events_\d{8}_to_\d{8}\.json$', user_file)
    if not match:
        print(f"Could not extract user ID from {user_file}")
        return None
    
    user_id = match.group(1)
    print(f"User ID: {user_id}")
    
    # Read the user's data file
    try:
        with open(user_file, 'r') as f:
            events = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    if not events:
        print(f"No events found for user {user_id}")
        return None
    
    # Filter and process events in one pass
    processed_events = []
    total_events = len(events)
    
    for event in events:
        event_type = event.get('event_type')
        
        # Apply filtering
        if include_events and event_type not in include_events:
            continue  # Skip this event
        
        # Process the event
        processed_event = process_event(event)
        processed_events.append(processed_event)
    
    if not processed_events:
        print(f"No events remaining after filtering for user {user_id}")
        return None
    
    # Extract user data from first raw event (before processing removes user fields)
    user_data = extract_user_data(events[0], user_id)
    
    # Create final structure
    final_data = {
        "user_data": user_data,
        "events": processed_events,
        "total_events": len(processed_events)
    }
    
    # Determine filter description
    if include_events:
        filter_description = f"kept only {len(include_events)} specified event types"
    else:
        filter_description = "kept all events (no filtering applied)"
    
    print(f'Processed {len(processed_events)} events from {total_events} total ({filter_description})')
    
    return final_data, user_id

def main():
    """Main processing function"""
    # Get session directories
    raw_dir, clean_dir, isolate_dir = get_session_directories()

    if not raw_dir or not clean_dir:
        print("❌ No active session found. Please run main.py first.")
        exit(1)

    # Load events filter configuration
    include_events = load_events_filter_config()

    # Find all user event files in session raw folder
    user_files = glob.glob(os.path.join(raw_dir, 'user_*.json'))
    if not user_files:
        print(f"No user event files found in {raw_dir} folder!")
        exit()

    print(f"Found {len(user_files)} user files to process")

    # Create clean folder if it doesn't exist
    os.makedirs(clean_dir, exist_ok=True)

    # Process each user file
    processed_count = 0
    for i, user_file in enumerate(user_files):
        result = process_user_file(user_file, include_events)
        
        if result is None:
            continue
        
        final_data, user_id = result
        
        # Save the clean filtered file for this user
        output_file = os.path.join(clean_dir, f'userClean_{user_id}.json')
        try:
            with open(output_file, 'w') as f:
                json.dump(final_data, f, indent=2)
            
            print(f'✅ Created {output_file}')
            processed_count += 1
            
            # Show sample for first user only
            if i == 0:
                print('Sample structure:')
                sample_structure = {
                    "user_data": final_data["user_data"],
                    "events": final_data["events"][:2] if final_data["events"] else [],
                    "total_events": final_data["total_events"]
                }
                print(json.dumps(sample_structure, indent=2))
                
        except Exception as e:
            print(f"❌ Error saving file: {e}")

    print(f"\n🎉 Processing complete! Created filtered files for {processed_count} users.")

if __name__ == "__main__":
    main() 