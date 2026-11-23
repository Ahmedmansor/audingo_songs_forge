@echo off
setlocal
title Audingo Songs Forge

:: Change working directory to project root
cd /d "%~dp0"

echo ======================================================
echo            Audingo - Songs Forge Launcher
echo ======================================================
echo.

:: Verify virtual environment
if not exist ".\venv\Scripts\streamlit.exe" (
    echo [ERROR] Streamlit executable not found in .\venv\Scripts\
    echo Please make sure the virtual environment exists at .\venv
    echo.
    pause
    exit /b 1
)

echo Starting Audingo Songs Forge...
echo The app will open in your default browser shortly.
echo (Keep this window open while using the app. Close it to stop the server.)
echo.

:: Run streamlit app using the venv's streamlit binary directly
".\venv\Scripts\streamlit.exe" run app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [NOTE] Streamlit server stopped.
    pause
)

