@echo off
cd /d "%~dp0"
echo Building Rafah.3dm for Rhino (this can take a few minutes)...
if not exist .venv (
  py -3 -m venv .venv
  if errorlevel 1 python -m venv .venv
)
call .venv\Scripts\pip install -q rhino3dm pillow
call .venv\Scripts\python rhino\export_rhino.py
echo.
echo Done. Open rhino\Rafah.3dm in Rhino, then run rhino\Set Map View.py
echo to switch OpenStreetMap / Basemap / Damage / 3D Map / People ^& Place / Heritage.
pause
