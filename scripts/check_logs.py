#!/usr/bin/env python3
"""
SCIM Server Log Checker

This script helps you check and display the SCIM server logs.
"""

import sys
import os
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.config import settings

def check_log_file():
    """Check if the log file exists and display its contents."""
    log_path = settings.log_file_path
    
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        print(f"📁 Expected location: {os.path.abspath(log_path)}")
        print("\nPossible reasons:")
        print("1. Server hasn't been started yet")
        print("2. Logging to file is disabled (check settings.log_to_file)")
        print("3. Logs directory doesn't exist")
        return False
    
    print(f"✅ Log file found: {log_path}")
    print(f"📊 File size: {os.path.getsize(log_path)} bytes")
    print(f"📅 Last modified: {datetime.fromtimestamp(os.path.getmtime(log_path))}")
    return True

def display_logs(lines=50, follow=False):
    """Display the log file contents."""
    log_path = settings.log_file_path
    
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        return
    
    print(f"📋 Displaying last {lines} lines from: {log_path}")
    print("=" * 80)
    
    try:
        with open(log_path, 'r') as f:
            if follow:
                # Follow the log file (like tail -f)
                import time
                f.seek(0, 2)  # Go to end of file
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    print(line.rstrip())
            else:
                # Display last N lines
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line.rstrip())
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def show_logging_config():
    """Display current logging configuration."""
    print("🔧 Current Logging Configuration:")
    print(f"  Log to file: {settings.log_to_file}")
    print(f"  Log file path: {settings.log_file_path}")
    print(f"  Log level: {settings.log_level}")
    print(f"  Log rotation: {settings.log_file_rotation}")
    print(f"  Log retention: {settings.log_file_retention}")
    print(f"  Log compression: {settings.log_file_compression}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="SCIM Server Log Checker")
    parser.add_argument("--lines", "-n", type=int, default=50, 
                       help="Number of lines to display (default: 50)")
    parser.add_argument("--follow", "-f", action="store_true",
                       help="Follow log file (like tail -f)")
    parser.add_argument("--config", "-c", action="store_true",
                       help="Show logging configuration")
    parser.add_argument("--check", action="store_true",
                       help="Check if log file exists")
    
    args = parser.parse_args()
    
    if args.config:
        show_logging_config()
        return
    
    if args.check:
        check_log_file()
        return
    
    if args.follow:
        print("🔄 Following log file (press Ctrl+C to stop)...")
        display_logs(follow=True)
    else:
        display_logs(lines=args.lines)

if __name__ == "__main__":
    main() 