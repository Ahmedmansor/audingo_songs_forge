@echo off
title Start Opera with Remote Debugging
chcp 65001 >nul
echo ==============================================================
echo       Starting Opera with Remote Debugging (Port 9222)
echo ==============================================================
echo.

set OPERA_EXE="C:\Users\ahmedMansour\AppData\Local\Programs\Opera\opera.exe"

REM Check if port 9222 is already listening
netstat -ano | findstr 9222 >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [V] Opera is ALREADY running with remote debugging on port 9222!
    echo     You can now run 'run_downloader.bat' directly!
    echo ==============================================================
    timeout /t 4
    exit /b 0
)

REM Check if Opera is running normally without debugging
tasklist /FI "IMAGENAME eq opera.exe" 2>NUL | find /I /N "opera.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [!] Opera is currently running without remote debugging.
    echo     Closing Opera to enable remote debugging on port 9222...
    taskkill /F /IM opera.exe /T >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo Starting Opera on port 9222...
start "" %OPERA_EXE% --remote-debugging-port=9222 "https://suno.com/create"

echo.
echo [V] Opera has started with remote debugging on port 9222.
echo [i] You can now run 'run_downloader.bat'.
echo ==============================================================
timeout /t 4
