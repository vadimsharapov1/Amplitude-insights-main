import json
import glob
import os
from collections import Counter

# Find all user event files in userData folder
user_files = glob.glob('userData/userData_raw/user_*.json')

if not user_files:
    print("No user event files found in userData folder!")
    exit()

print(f"Found {len(user_files)} user event file(s) to analyze:")
for file in user_files:
    print(f"  - {file}")

# Process each user file
for user_file in user_files:
    print(f"\n{'='*80}")
    print(f"ANALYZING: {user_file}")
    print(f"{'='*80}")
    
    # Read the user events file
    try:
        with open(user_file, 'r') as f:
            events = json.load(f)
    except Exception as e:
        print(f"Error reading {user_file}: {e}")
        continue
    
    if not events:
        print(f"No events found in {user_file}")
        continue
    
    print(f"Total events for user: {len(events)}")
    print("\n=== Event Types Analysis ===")
    
    # Count event types
    event_types = [event.get('event_type', 'UNKNOWN') for event in events]
    event_counts = Counter(event_types)
    
    # Sort by count (descending)
    sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(sorted_events)} unique event types:")
    for event_type, count in sorted_events:
        print(f"  {event_type}: {count}")
    
    # Check for specific events you mentioned
    target_events = ['Start Session', 'launch_first_time', 'start_session', 'session_start']
    print(f"\n=== Checking for specific events ===")
    for target in target_events:
        if target in event_counts:
            print(f"✅ Found '{target}': {event_counts[target]} events")
        else:
            print(f"❌ Missing '{target}'")
    
    # Check for any events containing 'session' or 'launch' or 'start'
    print(f"\n=== Events containing 'session', 'launch', or 'start' ===")
    session_events = [et for et in event_types if 'session' in et.lower() or 'launch' in et.lower() or 'start' in et.lower()]
    if session_events:
        session_counts = Counter(session_events)
        for event_type, count in session_counts.items():
            print(f"  {event_type}: {count}")
    else:
        print("  No events found containing 'session', 'launch', or 'start'")
    
    # Show first few events chronologically
    print(f"\n=== First 5 events chronologically ===")
    # Sort by event_time
    sorted_events_by_time = sorted(events, key=lambda x: x.get('event_time', ''))
    for i, event in enumerate(sorted_events_by_time[:5]):
        print(f"{i+1}. {event.get('event_time')} - {event.get('event_type')}")
    
    print(f"\n=== Last 5 events chronologically ===")
    for i, event in enumerate(sorted_events_by_time[-5:]):
        print(f"{len(sorted_events_by_time)-4+i}. {event.get('event_time')} - {event.get('event_type')}")

print(f"\n{'='*80}")
print(f"ANALYSIS COMPLETE - Processed {len(user_files)} user file(s)")
print(f"{'='*80}") 