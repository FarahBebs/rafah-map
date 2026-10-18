# Rafah map

A 3D map of Rafah for a web browser and for Rhino. The repository is public so anyone can download the files and use them.

## Folders

| Folder | What is inside |
| --- | --- |
| `data/rafah/` | Rafah governorate buildings, roads, and boundary as GeoJSON |
| `rhino/Rafah.3dm` | The same place as a Rhino 7 model (meters). Opens in Rhino 7 and Rhino 8 |
| `web/` | Browser map |
| `data/nextgis/basemap/` | NextGIS basemap sample: roads, buildings, water, land use, and a QGIS project |
| `data/nextgis/elevation/` | NextGIS elevation sample: DEM, hillshade, and contour lines |
| `data/nextgis/buildings/` | NextGIS building-footprint sample from OpenStreetMap, Microsoft, and Google |
| `scripts/fetch_data.py` | Downloads a fresh Rafah extract from OpenStreetMap |
| `rhino/export_rhino.py` | Rebuilds `Rafah.3dm` from `data/rafah/` |

The NextGIS folders are the free GeoJSON samples from [data.nextgis.com](https://data.nextgis.com/en/data-samples/#formats-base). They show the layer structure and file layout. They are a demo area, not an extract of Rafah. Rafah itself is in `data/rafah/` and `rhino/Rafah.3dm`.

## Open the browser map

```bash
python3 web/server.py
```

Then open http://127.0.0.1:8765/web/

Drag to look around. The panel turns layers on and off and changes terrain relief and building height.

## Open it in Rhino

Use **File → Open** and choose `rhino/Rafah.3dm`.

Units are meters. The XY origin is 34.25°E, 31.28°N. Z is meters above sea level. Layers are Terrain, Buildings, Roads, and Boundary. A named building keeps its name on the object.

## Data licenses

Rafah buildings, roads, and the boundary come from OpenStreetMap and are available under the [Open Database License](https://opendatacommons.org/licenses/odbl/1.0/). © OpenStreetMap contributors.

The NextGIS samples are also shared under the Open Database License. Each sample folder has a `README.txt` or `readme.txt` with the full credit for OpenStreetMap, Copernicus WorldDEM-30, Microsoft, and Google. QGIS project styles are CC BY 4.0 © NextGIS.

The code in `web/`, `scripts/`, and `rhino/export_rhino.py` is MIT. See `LICENSE`.
