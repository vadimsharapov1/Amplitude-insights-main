#!/usr/bin/env python3
"""
Event Isolation Script

This script takes clean user data from userData_clean/ and creates isolated versions
that contain only events from a specified isolation event onwards.

The isolated data is saved to userData/userData_isolate/
"""

import json
import glob
import os
import re
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from session_context import get_session_directories

# Get session directories
raw_dir, clean_dir, isolate_dir = get_session_directories()

def get_available_event_types():
    """Scan clean files to get a list of all available event types"""
    event_types = set()
    
    # Sample a few files to get event types
    clean_files = glob.glob(os.path.join(clean_dir, 'userClean_*.json'))
    sample_files = clean_files[:5]  # Sample first 5 files
    
    for file_path in sample_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if 'events' in data:
                for event in data['events']:
                    if 'event_type' in event:
                        event_types.add(event['event_type'])
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return sorted(list(event_types))

def isolate_user_events(file_path, isolation_event):
    """
    Process a single user file and create isolated version
    Returns: (success, isolated_events_count, total_events_count)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'events' not in data or not data['events']:
            return False, 0, 0
        
        events = data['events']
        total_events = len(events)
        
        # Find the first occurrence of the isolation event
        isolation_index = None
        for i, event in enumerate(events):
            if event.get('event_type') == isolation_event:
                isolation_index = i
                break
        
        if isolation_index is None:
            print(f"   ⚠️  Isolation event '{isolation_event}' not found in this user's data")
            return False, 0, total_events
        
        # Keep events from isolation point onwards
        isolated_events = events[isolation_index:]
        
        # Create isolated data structure
        isolated_data = {
            "user_data": data['user_data'].copy(),
            "isolation_info": {
                "isolation_event": isolation_event,
                "isolation_date": isolated_events[0]['event_time'] if isolated_events else None,
                "events_before_isolation": isolation_index,
                "events_after_isolation": len(isolated_events)
            },
            "events": isolated_events,
            "total_events": len(isolated_events)
        }
        
        # Extract user ID for filename
        user_id = data['user_data']['user_id']
        
        # Save isolated data
        output_file = os.path.join(isolate_dir, f'userIsolated_{user_id}.json')
        with open(output_file, 'w') as f:
            json.dump(isolated_data, f, indent=2)
        
        return True, len(isolated_events), total_events
        
    except Exception as e:
        print(f"   ❌ Error processing file: {e}")
        return False, 0, 0

def main():
    print("🎯 EVENT ISOLATION TOOL")
    print("=" * 50)
    print("This tool creates isolated versions of clean user data,")
    print("keeping only events from a specified event onwards.\n")
    
    # Check if session directories are available
    if not clean_dir or not isolate_dir:
        print("❌ No active session found. Please run main.py first.")
        return
    
    # Ensure output directory exists
    os.makedirs(isolate_dir, exist_ok=True)
    
    # Get available event types
    print("📊 Scanning clean files for available event types...")
    available_events = get_available_event_types()
    
    if not available_events:
        print("❌ No event types found in clean files!")
        return
    
    print(f"Found {len(available_events)} unique event types:\n")
    
    # Check if running in non-interactive mode (from main.py)
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # Use a default isolation event for automated runs
        # Try common events in order of preference
        default_events = ['trial_started', 'app_start', 'session_start', 'first_open']
        isolation_event = None
        
        for event in default_events:
            if event in available_events:
                isolation_event = event
                print(f"🤖 Running in automated mode. Using default event: '{isolation_event}'")
                break
        
        if not isolation_event:
            # If no default found, use the first available event
            isolation_event = available_events[0]
            print(f"🤖 No default event found. Using first available: '{isolation_event}'")
    else:
        # Interactive mode - display available events
        for i, event_type in enumerate(available_events, 1):
            print(f"{i:2d}. {event_type}")
        
        print("\n" + "=" * 50)
        
        # Ask user for isolation event
        while True:
            isolation_event = input("\n🎯 Enter the isolation event name (or 'q' to quit): ").strip()
            
            if isolation_event.lower() == 'q':
                print("Exiting...")
                return
            
            if isolation_event in available_events:
                break
            else:
                print(f"❌ Event '{isolation_event}' not found in available events.")
                print("Please choose from the list above or type 'q' to quit.")
    
    print(f"\n🎯 Isolating events from '{isolation_event}' onwards...")
    print("=" * 50)
    
    # Get all clean files
    clean_files = glob.glob(os.path.join(clean_dir, 'userClean_*.json'))
    
    if not clean_files:
        print(f"❌ No clean files found in {clean_dir}")
        return
    
    print(f"Processing {len(clean_files)} user files...\n")
    
    # Process each file
    successful_isolations = 0
    total_files = len(clean_files)
    total_events_before = 0
    total_events_after = 0
    files_without_event = 0
    
    for i, file_path in enumerate(clean_files, 1):
        # Extract user ID from filename
        match = re.search(r'userClean_(.+?)\.json$', file_path)
        if not match:
            continue
        
        user_id = match.group(1)
        print(f"[{i:2d}/{total_files}] Processing: {user_id}")
        
        success, isolated_count, total_count = isolate_user_events(file_path, isolation_event)
        
        if success:
            successful_isolations += 1
            total_events_before += total_count
            total_events_after += isolated_count
            print(f"   ✅ Isolated {isolated_count} events (from {total_count} total)")
        else:
            if total_count > 0:
                files_without_event += 1
            print(f"   ❌ Failed to isolate (total events: {total_count})")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 ISOLATION COMPLETE!")
    print("=" * 50)
    print(f"Isolation event: '{isolation_event}'")
    print(f"Files processed: {total_files}")
    print(f"Successful isolations: {successful_isolations}")
    print(f"Files without isolation event: {files_without_event}")
    print(f"Total events before isolation: {total_events_before:,}")
    print(f"Total events after isolation: {total_events_after:,}")
    
    if total_events_before > 0:
        reduction_percent = ((total_events_before - total_events_after) / total_events_before) * 100
        print(f"Event reduction: {reduction_percent:.1f}%")
    
    print(f"\n📁 Isolated files saved to: userData/userData_isolate/")
    print("=" * 50)

if __name__ == "__main__":
    main() 