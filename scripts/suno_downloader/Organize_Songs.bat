@echo off
title Suno Audingo Organizer
chcp 65001 >nul
echo ======================================================
echo          Suno-Audingo Songs and Styles Organizer
echo ======================================================
echo.

set PYTHON_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    set PYTHON_CMD="C:\Users\ahmedMansour\AppData\Local\Programs\Python\Python311\python.exe"
)

%PYTHON_CMD% "%~dp0organize_suno_audingo.py"

echo.
echo ======================================================
echo                    Done!
echo ======================================================
pause
