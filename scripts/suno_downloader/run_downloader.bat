@echo off
title Suno Playwright Downloader
chcp 65001 >nul
echo ==============================================================
echo             Suno AI Automated Style Downloader
echo ==============================================================
echo.
echo Make sure Opera is running with remote debugging (port 9222).
echo If not, run 'start_opera.bat' first.
echo.

set PYTHON_CMD=python
if exist "C:\Users\ahmedMansour\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD="C:\Users\ahmedMansour\AppData\Local\Programs\Python\Python311\python.exe"
)

%PYTHON_CMD% "%~dp0suno_downloader.py"

echo.
echo ==============================================================
echo                       Execution Finished
echo ==============================================================
pause
