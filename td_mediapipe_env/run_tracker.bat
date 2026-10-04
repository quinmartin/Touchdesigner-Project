@echo off
rem Start the Wave the Wheat pose tracker (Windows). Keep this window open while TouchDesigner runs.
cd /d "%~dp0"
Scripts\python.exe pose_tracker.py
pause
