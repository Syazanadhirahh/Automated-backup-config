#!/usr/bin/env python
"""
Simple backup scheduler for Windows
Run this script to start the automatic backup scheduler
"""

import os
import sys
import time
import schedule
from pathlib import Path

# tambah project directory ke python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# set django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etiqa.settings')

import django  
django.setup()

from django.core.management import call_command
from network_scanner.backup_service import backup_service


def run_backups():
    """Run all scheduled backups"""
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled backups...")
        backup_service.run_scheduled_backups()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Backup check completed")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error running backups: {e}")


def main():
    """Main scheduler function"""
    print("Starting Etiqa Auto Backup Scheduler...")
    print("Press Ctrl+C to stop")
    
    # Schedule backup checks setiap 5 minit
    schedule.every(5).minutes.do(run_backups)
    
    # Run initial backup check
    # run initial backup check
    run_backups()

    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check setiap minit
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        print(f"Scheduler error: {e}")


if __name__ == "__main__":
    main()
