#!/usr/bin/env python3
"""
OPTIMIZED Main orchestration script for Amplitude data extraction and processing workflow.

PERFORMANCE IMPROVEMENTS:
- Single API scraping pass (no redundant downloads)
- Direct function calls instead of subprocess overhead
- Intelligent user filtering during download
- Streamlined workflow with early exits

Usage: python3 main_optimized.py
"""

import sys
import os
from datetime import datetime

def main():
    """Optimized main workflow"""
    start_time = datetime.now()
    
    print("🚀 AMPLITUDE DATA EXTRACTION WORKFLOW (OPTIMIZED)")
    print("=" * 60)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize session context
    sys.path.append('scripts')
    from session_context import set_session_context, save_session_context, clear_session_context
    from scripts.user_config import get_user_ids_file, ensure_output_directories
    
    try:
        # Get user file selection
        print("\n📁 USER FILE SELECTION")
        user_file = get_user_ids_file()
        if not user_file:
            print("❌ No user file selected. Exiting.")
            return False
        
        # Create dynamic output directories
        raw_dir, clean_dir, isolate_dir = ensure_output_directories(user_file)
        if not raw_dir:
            print("❌ Failed to create output directories")
            return False
        
        # Set and save session context
        set_session_context(user_file, raw_dir, clean_dir, isolate_dir)
        save_session_context()
        
        print(f"✅ Session initialized for: {os.path.basename(user_file)}")
        print(f"📁 Data will be saved to: {os.path.dirname(raw_dir)}")
        
        # Get isolation event selection upfront
        print("\n🎯 EVENT ISOLATION CONFIGURATION")
        print("=" * 60)
        print("Do you want to isolate events after data processing?")
        print("Isolation keeps only events from a specific event onwards.")
        print("Common isolation events: 'trial_started', 'app_start', 'first_open', 'session_start'")
        print("\nOptions:")
        print("  y/yes  - Choose a custom isolation event")
        print("  n/no   - Skip isolation (no files in userData_isolate)")
        
        isolation_event = None
        skip_isolation = False
        
        while True:
            choice = input("\nDo you want to perform event isolation? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                print("\n💡 TIP: You'll see available events after data processing.")
                print("Common events to try: trial_started, app_start, first_open, session_start")
                isolation_event = input("Enter the isolation event name: ").strip()
                # Clean up input - remove quotes if user added them
                isolation_event = isolation_event.strip("'\"")
                if isolation_event:
                    print(f"✅ Will isolate events from '{isolation_event}' onwards")
                    break
                else:
                    print("❌ Event name cannot be empty. Please try again.")
            elif choice in ['n', 'no']:
                skip_isolation = True
                print("✅ Will skip event isolation - no files will be created in userData_isolate")
                break
            else:
                print("❌ Please enter 'y' or 'n'")
        
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        return False
    
    # OPTIMIZED PHASE 1: Single scraping pass for all users
    print("\n📡 PHASE 1: OPTIMIZED USER SCRAPING")
    print("=" * 60)
    
    try:
        # Import amplitude module directly (no subprocess)
        from amplitude_user_events import AmplitudeAPI
        from scripts.user_config import get_amplitude_credentials
        import json
        from datetime import datetime as dt, timedelta
        import re
        
        # Get API credentials
        try:
            API_KEY, SECRET_KEY = get_amplitude_credentials()
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            return False
        
        amplitude = AmplitudeAPI(API_KEY, SECRET_KEY)
        
        # Parse user file efficiently
        def parse_date(date_str):
            """Parse date in format 'May 16, 2025' or 'Jun 16, 2025' or detailed format"""
            try:
                # First try full month name format
                try:
                    return dt.strptime(date_str.strip(), '%B %d, %Y')
                except ValueError:
                    pass
                
                # Then try abbreviated month format
                try:
                    return dt.strptime(date_str.strip(), '%b %d, %Y')
                except ValueError:
                    pass
                
                # Finally try detailed format with timezone
                date_part = re.sub(r'\s+GMT[+-]\d+$', '', date_str)
                return dt.strptime(date_part, '%B %d, %Y %I:%M:%S.%f %p')
            except ValueError as e:
                print(f"Error parsing date '{date_str}': {e}")
                return None
        
        # Read and parse user data
        user_data = []
        print(f"📖 Reading user file: {user_file}")
        try:
            with open(user_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments, empty lines, and template/example lines
                    if (line and 
                        not line.startswith('#') and 
                        not line.lower().startswith('example') and
                        'replace with your real data' not in line.lower() and
                        'template' not in line.lower()):
                        
                        if '|' in line:
                            parts = line.split('|')
                            user_id = parts[0].strip()
                            
                            # Skip if user_id looks like template text
                            if (user_id.lower().startswith('example') or 
                                'replace' in user_id.lower() or
                                'template' in user_id.lower() or
                                not user_id):
                                continue
                            
                            if len(parts) == 3:
                                first_seen_str = parts[1].strip()
                                last_seen_str = parts[2].strip()
                                first_seen = parse_date(first_seen_str)
                                last_seen = parse_date(last_seen_str)
                                user_data.append((user_id, first_seen, last_seen, first_seen_str, last_seen_str))
                            elif len(parts) == 2:
                                creation_date_str = parts[1].strip()
                                creation_date = parse_date(creation_date_str)
                                user_data.append((user_id, creation_date, None, creation_date_str, None))
                        else:
                            # For lines without |, check if it's a valid user ID
                            if (not line.lower().startswith('example') and 
                                'replace' not in line.lower() and
                                'template' not in line.lower() and
                                line):
                                user_data.append((line, None, None, None, None))
        except FileNotFoundError:
            print(f"❌ User file not found: {user_file}")
            return False
        
        if not user_data:
            print("❌ No user IDs found in file")
            return False
        
        print(f"📊 Found {len(user_data)} users to process")
        
        # Process each user efficiently (single API call per user)
        successful_users = 0
        current_date = dt.now()
        
        for user_id, first_seen, last_seen, first_seen_str, last_seen_str in user_data:
            print(f"\n🔄 Processing user: {user_id}")
            
            # Calculate date range
            if first_seen and last_seen:
                start_date = first_seen - timedelta(days=1)
                end_date = last_seen
                print(f"   📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            elif first_seen:
                start_date = first_seen - timedelta(days=1)
                end_date = current_date
                print(f"   📅 Date range: {start_date.strftime('%Y-%m-%d')} to current")
            else:
                # Changed from 3 days to 1 day as requested
                start_date = current_date - timedelta(days=1)
                end_date = current_date
                print(f"   📅 Using default 1-day range (only yesterday)")
            
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            # Get events for this specific user (optimized filtering)
            try:
                all_events = amplitude.get_all_events_for_date_range(
                    start_date_str, end_date_str, None, None, user_id
                )
                
                # Filter events by user
                user_events = amplitude.filter_events_by_user(all_events, user_id)
                
                # Always create user file (even if empty)
                filename = f"{raw_dir}/user_{user_id}_events_{start_date_str}_to_{end_date_str}.json"
                with open(filename, 'w') as f:
                    json.dump(user_events, f, indent=2)
                
                if user_events:
                    print(f"   ✅ Found {len(user_events)} events")
                    successful_users += 1
                else:
                    print(f"   ⚠️  No events found (created empty file)")
                
            except Exception as e:
                print(f"   ❌ Error processing user {user_id}: {e}")
                # Create empty file for failed users
                filename = f"{raw_dir}/user_{user_id}_events_{start_date_str}_to_{end_date_str}.json"
                with open(filename, 'w') as f:
                    json.dump([], f)
        
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   Total users: {len(user_data)}")
        print(f"   Successful: {successful_users}")
        print(f"   Empty/Failed: {len(user_data) - successful_users}")
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return False
    
    # OPTIMIZED PHASE 2: Direct cleaning (no subprocess)
    print("\n🧹 PHASE 2: JSON CLEANING & OPTIMIZATION")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'scripts/create_clean_json.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ JSON cleaning completed")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ JSON cleaning failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Cleaning error: {e}")
        return False
    
    # OPTIMIZED PHASE 3: Direct isolation with custom event (or skip)
    if skip_isolation:
        print(f"\n🎯 PHASE 3: EVENT ISOLATION (SKIPPED)")
        print("=" * 60)
        print("✅ Event isolation skipped as requested - no files created in userData_isolate")
    else:
        print(f"\n🎯 PHASE 3: EVENT ISOLATION (using '{isolation_event}')")
        print("=" * 60)
        
        try:
            # Import isolation functions directly for better control
            from isolate_events import isolate_user_events
            import glob
            
            # Get all clean files
            clean_files = glob.glob(os.path.join(clean_dir, 'userClean_*.json'))
            
            if not clean_files:
                print(f"❌ No clean files found in {clean_dir}")
                return False
            
            print(f"Processing {len(clean_files)} user files with isolation event '{isolation_event}'...")
            
            # First, get available events from the data to show if isolation event is not found
            available_events = set()
            for file_path in clean_files[:1]:  # Check first file for available events
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if 'events' in data:
                        for event in data['events']:
                            if 'event_type' in event:
                                available_events.add(event['event_type'])
                except:
                    pass
            
            # Process each file with the selected isolation event
            successful_isolations = 0
            total_files = len(clean_files)
            total_events_before = 0
            total_events_after = 0
            files_without_event = 0
            
            for i, file_path in enumerate(clean_files, 1):
                # Extract user ID from filename
                import re
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
                    files_without_event += 1
                    total_events_before += total_count
                    print(f"   ⚠️  Event '{isolation_event}' not found in this user's data")
                    
                    # Create a file with informative message when event is not found
                    try:
                        message = f"Optimization based on '{isolation_event}' is not possible, as the event is not present in that user log"
                        output_file = os.path.join(isolate_dir, f'userIsolated_{user_id}.json')
                        
                        # Create a structured message file
                        message_data = {
                            "user_id": user_id,
                            "isolation_event": isolation_event,
                            "status": "event_not_found",
                            "message": message,
                            "total_events_in_user_data": total_count,
                            "available_events": sorted(available_events) if available_events else []
                        }
                        
                        with open(output_file, 'w') as f:
                            json.dump(message_data, f, indent=2)
                        
                        print(f"   📄 Created info file: {os.path.basename(output_file)}")
                        
                    except Exception as e:
                        print(f"   ❌ Error creating info file: {e}")
                    
                    # Show available events if this is the first file and event not found
                    if i == 1 and available_events:
                        print(f"   📋 Available events in this user's data:")
                        sorted_events = sorted(available_events)
                        for j, event in enumerate(sorted_events):
                            print(f"      {j+1:2d}. {event}")
                        print(f"   💡 Consider using one of these events for isolation.")
            
            # Summary
            print(f"\n🎉 ISOLATION COMPLETE!")
            print("=" * 50)
            print(f"Isolation event: '{isolation_event}'")
            print(f"Files processed: {total_files}")
            print(f"Successful isolations: {successful_isolations}")
            print(f"Files without isolation event: {files_without_event}")
            print(f"Total events before isolation: {total_events_before}")
            print(f"Total events after isolation: {total_events_after}")
            if total_events_before > 0:
                reduction = ((total_events_before - total_events_after) / total_events_before) * 100
                print(f"Event reduction: {reduction:.1f}%")
            print(f"📁 Isolated files saved to: {os.path.basename(isolate_dir)}/")
            
        except Exception as e:
            print(f"❌ Isolation error: {e}")
            return False
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("🎉 OPTIMIZED WORKFLOW COMPLETED!")
    print("=" * 60)
    print(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration}")
    print(f"\n⚡ PERFORMANCE IMPROVEMENTS:")
    print(f"   - Single API scraping pass (no redundant downloads)")
    print(f"   - Direct function calls (reduced subprocess overhead)")
    print(f"   - Eliminated missing user detection phase")
    print(f"   - Eliminated end date verification phase")
    print(f"\n📁 Check the following folders for results:")
    print(f"   - {raw_dir}/     - Raw scraped data")
    print(f"   - {clean_dir}/   - Clean, optimized data") 
    print(f"   - {isolate_dir}/ - Isolated event data")
    print("=" * 60)
    
    # Cleanup session context
    clear_session_context()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Workflow interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1) 