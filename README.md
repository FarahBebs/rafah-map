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

#### Move around

- Drag to move.
- Scroll, or pinch, to zoom.
- Right-drag, or use two fingers, to tilt.
- The compass control at the bottom left resets north and zoom.

#### Map view

At the top of the left panel, **Map view** chooses which data set you see. Roads and the Rafah boundary usually stay from OpenStreetMap. The buildings and coloured overlays change with the view.

| Map view | What you see |
| --- | --- |
| **OpenStreetMap** | Everyday Rafah buildings and roads from OpenStreetMap. Buildings are coloured by type (house, school, mosque, and so on). |
| **Basemap (AUB)** | Landscape layers from the AUB project: farmland, greenhouses, institutional land, coast, camps, cemetery/recreation areas, neighbourhoods, and institution points. |
| **Damage (AUB)** | Damage overlays for Rafah — damaged roads, greenhouses, natural and institutional land, damaged buildings — plus a small **Rafah building damage** stats box. Buildings are coloured by damage level. |
| **3D Map (AUB)** | The AUB 3D building damage view for Rafah. Buildings are extruded and coloured by cumulative damage (destroyed, severe/heavy, moderate, possible, no damage). The same stats box appears. |
| **People & Place (AUB)** | Story points across Gaza. Colours mark the theme: disruption of socio-spatial practices, everyday resistance, or displacement. The camera opens on a wider Gaza view. |
| **Heritage (AUB)** | Heritage sites and heritage buildings across Gaza (points and polygons). |

The first time you open a heavy AUB view (especially Damage or 3D Map), the page may pause for a few seconds while the files load.

The AUB views come from the public project [Tracking The Urbicide in Gaza](https://experience.arcgis.com/experience/5c24d93ffc234d709efbbeb355d9496c/page/Page?views=3D-Map) (American University of Beirut).

#### What happens when you click

Click a building, coloured land area, road, camp, story pin, or heritage place. A card opens at the top right.

- The **title** is the best available name (building name, story title, heritage name in English, and so on).
- If there is no real name, the card uses a clear label instead, such as the building type, farmland class, road type, or “Building · Destroyed”.
- Under the title you usually see type, category, damage level, place, and sometimes height or a short description.
- For People & Place stories, a longer description can appear, with a **Source** link when one exists.
- Click another feature to replace the card. There is no separate close button; choosing a new view or clicking elsewhere on empty map space leaves the last card until the next click.

#### Rafah date

**Rafah date** picks a day from 1 Jan 2000 through the latest available photo. Only the **satellite photo** changes.

- From 2000 until early 2014 the photo is a wide, lower-detail view.
- From 20 Feb 2014 onward it is a closer Esri Wayback photo.
- Buildings and roads stay on the current map data. The date does not rewind the building footprints.

#### Layer checkboxes

| Checkbox | What it does |
| --- | --- |
| **Satellite** | Shows or hides the aerial photo. |
| **Streets** | Shows or hides the street basemap. |
| **Buildings** | Shows or hides the 3D buildings (when that view uses them). |
| **Roads** | Shows or hides the OpenStreetMap roads. |
| **Boundary** | Shows or hides the Rafah governorate outline. |
| **Terrain** | Turns ground height on or off. |

#### Sliders

| Slider | What it does |
| --- | --- |
| **Terrain relief** | How strong the hills look when terrain is on. |
| **Building height** | Scales how tall the extruded buildings look. |

#### Buttons

| Button | What it does |
| --- | --- |
| **City** | Flies to central Rafah. |
| **Governorate** | Zooms out to the wider Rafah area. |
| **Tilt** | Flattens the view or tips it back into 3D. |

#### Status line and credits

- The line under the title (**status**) shows a short count for the current view, for example how many buildings, how many are damaged, or how many stories.
- On Damage and 3D Map, the **Rafah building damage** box lists damaged / destroyed / severe / moderate / possible counts for Rafah, plus a one-line Gaza overall total.
- The footer credit text updates with the current view and links to OpenStreetMap or the AUB experience.

To stop the map, close the Terminal window on a Mac, or the black window on Windows.

## Open the same place in Rhino

The Rhino file is built to mirror the web map: the same Map view options, similar colours, extruded buildings, and named camera views (City / Governorate / People and Heritage).

The `.3dm` is large (about 200 MB), so it is **not stored in GitHub**. You build it once on your computer from the same data the web map uses.

### 1. Build the Rhino file (once)

You need Python and an internet connection for this step (elevation tiles download once).

**On a Mac**

1. Open the project folder.
2. Double-click **Build Rafah Rhino.command**.
3. If macOS blocks it, right-click → **Open** → **Open**.
4. Wait until it finishes (a few minutes). It creates `rhino/Rafah.3dm`.

**On Windows**

1. Open the project folder.
2. Double-click **Build Rafah Rhino.bat**.
3. Wait until it finishes. It creates `rhino\Rafah.3dm`.

Or in a terminal:

```bash
python3 -m venv .venv
.venv/bin/pip install rhino3dm pillow
.venv/bin/python rhino/export_rhino.py
```

### 2. Open the model

1. Open **Rhino 7** or **Rhino 8**.
2. Choose **File → Open**.
3. Choose `rhino/Rafah.3dm`.

Units are metres. The flat coordinates start at 34.25°E, 31.28°N. Height is metres above sea level.

When the file opens it starts in the **OpenStreetMap** layout (terrain, OSM roads, boundary, OSM buildings), like the web default.

### 3. Switch views (same options as the web)

The web **Map view** menu is reproduced by layer groups plus a small Python script.

1. In Rhino, type `EditPythonScript` and press Enter  
   (or **Tools → PythonScript → Edit…**).
2. Open `rhino/Set Map View.py`.
3. Click **Run**.
4. Pick one of:
   - **OpenStreetMap**
   - **Basemap (AUB)**
   - **Damage (AUB)**
   - **3D Map (AUB)**
   - **People & Place (AUB)**
   - **Heritage (AUB)**

That shows and hides the same layer groups the web map turns on and off, and jumps to the matching named camera (City, Governorate, or People and Heritage).

You can also toggle layers by hand in the **Layers** panel. Parent groups are:

| Layer group | Matches web view |
| --- | --- |
| `Shared` (Terrain, Roads OSM, Boundary) | Always kept on by the script |
| `01 OpenStreetMap` | OpenStreetMap / also used under Basemap |
| `02 Basemap AUB` | Basemap (AUB) |
| `03 Damage AUB` | Damage (AUB) overlays |
| `04 3D Map AUB` | Damage-coloured extruded buildings |
| `05 People and Place` | People & Place pins |
| `06 Heritage` | Heritage sites and buildings |

### 4. Cameras and looking around

- Named views: open the viewport title menu → **Named Views**, then choose **City**, **Governorate**, or **People and Heritage** (same framing as the web City / Governorate buttons and the wider Gaza People/Heritage view).
- Right-drag or use the mouse wheel to orbit and zoom, as usual in Rhino.
- Click an object and open **Properties** (or use `What` / `ObjInfo`) to read its name and user-text fields (damage, theme, height, description), similar to the web popup card.

### 5. What looks the same — and what is different

**Same as the web**

- Map view choices and layer grouping
- OSM vs AUB damage building colours
- People & Place theme colours (blue / green / gold)
- Extruded 3D buildings with height
- City / Governorate / wider Gaza framing

**Different from the web**

- Rhino does **not** stream the live satellite photo or the Rafah date slider. The ground is a 3D terrain mesh. Use the browser map when you need historical imagery.
- Very dense greenhouse / damage overlays are simplified for file size; the structure and colours still match the web layers.
- People & Place and Heritage points outside the Rafah elevation tiles sit on a flat fallback height so they still appear when you zoom out to Gaza.

### 6. Rebuild after data changes

Run **Build Rafah Rhino** again (or the `export_rhino.py` commands above) whenever you refresh the GeoJSON downloads and want an updated `.3dm`.

## What is in the folder

| Folder | What is inside |
| --- | --- |
| `web/` | The browser map |
| `data/rafah/` | OpenStreetMap buildings, roads, and the governorate boundary for Rafah |
| `data/urbicide/` | Rafah building footprints with cumulative damage (AUB 3D / damage view) |
| `data/aub/` | Other AUB layers: basemap, damage overlays, People & Place, heritage, and damage stats |
| `rhino/Rafah.3dm` | Generated Rhino model (build locally; not in GitHub) |
| `rhino/Set Map View.py` | Rhino script to switch views like the web menu |
| `rhino/export_rhino.py` | Builds `Rafah.3dm` from the GeoJSON data |
| `Build Rafah Rhino.command` / `.bat` | One-click builder for the Rhino file |
| `scripts/` | Optional download scripts to refresh OSM or AUB data |
| `data/nextgis/basemap/` | Sample roads, buildings, water, land use, and a QGIS project |
| `data/nextgis/elevation/` | Sample elevation, hillshade, and contour lines |
| `data/nextgis/buildings/` | Sample building footprints |

The NextGIS folders are free samples from [data.nextgis.com](https://data.nextgis.com/en/data-samples/#formats-base). They show how those map files are organized. They are a demo area. Rafah itself is in `data/rafah/` and `rhino/Rafah.3dm`. The AUB layers live in `data/urbicide/` and `data/aub/`.

## Licenses

Rafah buildings, roads, and the boundary come from OpenStreetMap and are available under the [Open Database License](https://opendatacommons.org/licenses/odbl/1.0/). © OpenStreetMap contributors.

The AUB views reuse public layers from [Tracking The Urbicide in Gaza](https://experience.arcgis.com/experience/5c24d93ffc234d709efbbeb355d9496c/page/Page?views=3D-Map) (American University of Beirut / ArcGIS Online). Credit that project when you use those layers.

The NextGIS samples are also shared under the Open Database License. Each sample folder has a readme with the full credit for OpenStreetMap, Copernicus WorldDEM-30, Microsoft, and Google. The QGIS styles are CC BY 4.0 © NextGIS.

The map pages and scripts are MIT. See `LICENSE`.
