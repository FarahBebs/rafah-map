@echo off
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo.
    echo Python is needed to open the map, and it is not installed yet.
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download and install Python.
    echo 3. On the first install screen, tick "Add python.exe to PATH".
    echo 4. Double-click this file again.
    echo.
    pause
    exit /b 1
  )
)

echo Opening the Rafah map in your browser.
echo Leave this window open while you use the map. Closing it turns the map off.
start "" "http://127.0.0.1:8765/web/"
%PY% web\server.py
pause
