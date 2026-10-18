#!/bin/bash
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo ""
  echo "Python is needed to open the map, and it is not installed yet."
  echo "1. Go to https://www.python.org/downloads/"
  echo "2. Download and install Python."
  echo "3. Double-click this file again."
  echo ""
  read -r -p "Press Enter to close."
  exit 1
fi

echo "Opening the Rafah map in your browser."
echo "Leave this window open while you use the map. Closing it turns the map off."
(sleep 1 && open "http://127.0.0.1:8765/web/") &
python3 web/server.py
