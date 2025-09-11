@echo off
echo Starting Etiqa Auto Backup Scheduler...
echo.
echo This will run the backup scheduler in the background.
echo Press Ctrl+C to stop the scheduler.
echo.

REM Install required packages if not already installed
pip install schedule

REM Start the backup scheduler
python backup_scheduler.py

pause
