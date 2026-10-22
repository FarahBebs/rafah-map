#!/bin/bash
cd "$(dirname "$0")"
set -e
echo "Building Rafah.3dm for Rhino (this can take a few minutes)…"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q rhino3dm pillow
.venv/bin/python rhino/export_rhino.py
echo ""
echo "Done. Open rhino/Rafah.3dm in Rhino, then run rhino/Set Map View.py"
echo "to switch OpenStreetMap / Basemap / Damage / 3D Map / People & Place / Heritage."
open -R rhino/Rafah.3dm 2>/dev/null || true
read -n 1 -s -r -p "Press any key to close…"
echo
