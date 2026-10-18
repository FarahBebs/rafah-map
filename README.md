# Rafah map

A 3D map of Rafah. You can look at it in a web browser. You do not need Rhino, and you do not need to know how to program.

If you use Rhino, you can also open the model file. That part is further down.

## Open the map on your computer

### 1. Download the folder

1. Open [https://github.com/FarahBebs/rafah-map](https://github.com/FarahBebs/rafah-map).
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Find the downloaded file, usually in your Downloads folder. It is named `rafah-map-main.zip`.
5. Unzip it.
   - On a Mac, double-click the zip file.
   - On Windows, right-click the zip file and choose **Extract All**, then **Extract**.

You should now have a folder named `rafah-map-main`. Leave the files inside that folder. Do not pull the starter file out by itself.

### 2. Start the map

You need an internet connection. The satellite photos and the ground height are loaded from the internet.

**On a Mac**

1. Open the `rafah-map-main` folder.
2. Double-click **Open Rafah Map.command**.
3. If your Mac says the file cannot be opened, right-click it, choose **Open**, then click **Open** again.
4. Your browser opens the map. Leave the Terminal window open while you look at it.

**On Windows**

1. Open the `rafah-map-main` folder.
2. Double-click **Open Rafah Map.bat**.
3. Your browser opens the map. Leave the black window open while you look at it.

The page address is [http://127.0.0.1:8765/web/](http://127.0.0.1:8765/web/). That address works only on your computer, and only while the starter window is open.

### 3. If it asks for Python

The map uses Python, which is free. You install it once.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/).
2. Download Python and run the installer.
3. On Windows, on the first screen, tick **Add python.exe to PATH**, then install.
4. Double-click the starter file again.

### 4. How to use the map

- Drag to move around.
- Right-drag, or use two fingers, to tilt the view.
- **Rafah date** picks a day from 1 Jan 2000 through today. The satellite photo changes to that time. From 2000 until early 2014 the photo is a wide view. From 20 Feb 2014 onward it is a close photo.
- The checkboxes turn the satellite, streets, buildings, roads, boundary, and terrain on and off.
- The sliders change how strong the hills look and how tall the buildings look.
- **City** returns to central Rafah. **Governorate** shows the wider area. **Tilt** lays the view flat or stands it back up.
- Click a building to see its name.

Buildings and roads are the current map. The date changes the satellite photo.

To stop the map, close the Terminal window on a Mac, or the black window on Windows.

## Open the same place in Rhino

1. Open Rhino 7 or Rhino 8.
2. Choose **File → Open**.
3. Choose `rhino/Rafah.3dm` inside the downloaded folder.

The model is in meters. The flat coordinates start at 34.25°E, 31.28°N. Height is meters above sea level. The layers are Terrain, Buildings, Roads, and Boundary. A named building keeps its name on the object.

## What is in the folder

| Folder | What is inside |
| --- | --- |
| `web/` | The browser map |
| `data/rafah/` | Rafah buildings, roads, and the governorate boundary |
| `rhino/Rafah.3dm` | The Rhino model |
| `data/nextgis/basemap/` | Sample roads, buildings, water, land use, and a QGIS project |
| `data/nextgis/elevation/` | Sample elevation, hillshade, and contour lines |
| `data/nextgis/buildings/` | Sample building footprints |

The NextGIS folders are free samples from [data.nextgis.com](https://data.nextgis.com/en/data-samples/#formats-base). They show how those map files are organized. They are a demo area. Rafah itself is in `data/rafah/` and `rhino/Rafah.3dm`.

## Licenses

Rafah buildings, roads, and the boundary come from OpenStreetMap and are available under the [Open Database License](https://opendatacommons.org/licenses/odbl/1.0/). © OpenStreetMap contributors.

The NextGIS samples are also shared under the Open Database License. Each sample folder has a readme with the full credit for OpenStreetMap, Copernicus WorldDEM-30, Microsoft, and Google. The QGIS styles are CC BY 4.0 © NextGIS.

The map pages and scripts are MIT. See `LICENSE`.
