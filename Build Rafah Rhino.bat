@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo Building Rafah.3dm for Rhino...
echo This can take several minutes. Leave this window open.
echo.

REM Prefer Python 3.12 — it has ready-made rhino3dm packages on Windows.
set "PYLAUNCH="
py -3.12 -c "import sys; print(sys.version)" >nul 2>&1
if not errorlevel 1 (
  set "PYLAUNCH=py -3.12"
  goto have_python
)
py -3.11 -c "import sys; print(sys.version)" >nul 2>&1
if not errorlevel 1 (
  set "PYLAUNCH=py -3.11"
  goto have_python
)
py -3.13 -c "import sys; print(sys.version)" >nul 2>&1
if not errorlevel 1 (
  set "PYLAUNCH=py -3.13"
  goto have_python
)
py -3 -c "import sys; print(sys.version)" >nul 2>&1
if not errorlevel 1 (
  set "PYLAUNCH=py -3"
  goto have_python
)
python -c "import sys; print(sys.version)" >nul 2>&1
if not errorlevel 1 (
  set "PYLAUNCH=python"
  goto have_python
)

echo Python was not found.
echo.
echo Install Python 3.12 from:
echo   https://www.python.org/downloads/release/python-31210/
echo Download "Windows installer (64-bit)".
echo On the first screen, tick "Add python.exe to PATH", then Install Now.
echo.
echo Then delete the ".venv" folder in this project if it exists,
echo and double-click this file again.
echo.
pause
exit /b 1

:have_python
echo Using: %PYLAUNCH%
%PYLAUNCH% -c "import sys; print('Python', sys.version)"

REM Recreate the virtual environment if packages are missing/broken.
if exist .venv\Scripts\python.exe goto venv_ready
echo Creating .venv ...
if exist .venv rmdir /s /q .venv
%PYLAUNCH% -m venv .venv
if errorlevel 1 (
  echo Could not create .venv
  pause
  exit /b 1
)

:venv_ready
echo Upgrading pip...
call .venv\Scripts\python -m pip install --upgrade pip
if errorlevel 1 (
  echo pip upgrade failed.
  pause
  exit /b 1
)

echo Installing rhino3dm and pillow (ready-made packages only)...
call .venv\Scripts\python -m pip install --only-binary=:all: rhino3dm pillow
if errorlevel 1 (
  echo.
  echo Could not install rhino3dm for this Python version.
  echo.
  echo Fix: install Python 3.12 64-bit from python.org, then:
  echo   1. Delete the ".venv" folder in this project
  echo   2. Double-click Build Rafah Rhino.bat again
  echo.
  echo Direct download:
  echo   https://www.python.org/downloads/release/python-31210/
  echo Use "Windows installer (64-bit)".
  echo Tick "Add python.exe to PATH" on the first screen.
  echo.
  pause
  exit /b 1
)

echo.
echo Exporting Rhino file...
call .venv\Scripts\python rhino\export_rhino.py
if errorlevel 1 (
  echo.
  echo Export failed. Scroll up for the error.
  pause
  exit /b 1
)

echo.
echo SUCCESS.
echo Open rhino\Rafah.3dm in Rhino, then run rhino\Set Map View.py
echo to switch OpenStreetMap / Basemap / Damage / 3D Map / People ^& Place / Heritage.
echo.
pause
exit /b 0
