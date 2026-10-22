#!/usr/bin/env python3
"""Build rhino/Rafah.3dm to match the web map views, layers, and colours.

Units are meters. XY origin is 34.25 E, 31.28 N. Z is metres above sea level.
Run from a venv with rhino3dm + pillow:

  python3 -m venv .venv
  .venv/bin/pip install rhino3dm pillow
  .venv/bin/python rhino/export_rhino.py
"""

from __future__ import annotations

import io
import json
import math
import urllib.request
from pathlib import Path

import rhino3dm
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAFAH = ROOT / "data" / "rafah"
URBICIDE = ROOT / "data" / "urbicide"
AUB = ROOT / "data" / "aub"
OUT = Path(__file__).resolve().parent / "Rafah.3dm"

ORIGIN_LON = 34.25
ORIGIN_LAT = 31.28
EARTH = 6_378_137.0
LAT0 = math.radians(ORIGIN_LAT)
SOUTH, WEST, NORTH, EAST = 31.2201289, 34.2158979, 31.3457700, 34.3294070
TERRAIN_ZOOM = 13
TERRAIN_STEP = 2

OSM_BUILDING_COLORS = {
    "mosque": (239, 226, 196, 255),
    "place_of_worship": (239, 226, 196, 255),
    "school": (215, 195, 162, 255),
    "university": (215, 195, 162, 255),
    "hospital": (215, 195, 162, 255),
    "civic": (215, 195, 162, 255),
    "apartments": (203, 181, 154, 255),
    "residential": (203, 181, 154, 255),
    "commercial": (183, 164, 140, 255),
    "retail": (183, 164, 140, 255),
    "office": (183, 164, 140, 255),
}

DAMAGE_COLORS = {
    "Destroyed": (135, 16, 20, 255),
    "Severe Damage": (181, 88, 76, 255),
    "Heavy Damage": (181, 88, 76, 255),
    "Moderate Damage": (207, 149, 130, 255),
    "Possible Damage": (212, 180, 131, 255),
    "No Damage": (196, 179, 154, 255),
}

PEOPLE_COLORS = {
    "Disruption of socio-spatial practices": (36, 93, 123, 255),
    "Everyday Resistance": (47, 125, 74, 255),
    "Displacement": (201, 162, 39, 255),
    "Displacement ": (201, 162, 39, 255),
}

# layer path -> default visible for OpenStreetMap view
LAYER_TREE = {
    "Shared": {
        "color": (120, 120, 120, 255),
        "visible": True,
        "children": {
            "Terrain": {"color": (176, 154, 120, 255), "visible": True},
            "Roads OSM": {"color": (242, 226, 196, 255), "visible": True},
            "Boundary": {"color": (227, 177, 90, 255), "visible": True},
        },
    },
    "01 OpenStreetMap": {
        "color": (196, 179, 154, 255),
        "visible": True,
        "children": {
            "Buildings OSM": {"color": (196, 179, 154, 255), "visible": True},
        },
    },
    "02 Basemap AUB": {
        "color": (111, 143, 78, 255),
        "visible": False,
        "children": {
            "Agriculture": {"color": (111, 143, 78, 255), "visible": False},
            "Greenhouses": {"color": (155, 187, 110, 255), "visible": False},
            "Institutional Land": {"color": (122, 158, 142, 255), "visible": False},
            "Coast": {"color": (106, 142, 168, 255), "visible": False},
            "Camps": {"color": (227, 177, 90, 255), "visible": False},
            "Cemetery Recreation": {"color": (138, 122, 106, 255), "visible": False},
            "Neighborhoods": {"color": (200, 190, 175, 255), "visible": False},
            "Institutions": {"color": (215, 195, 162, 255), "visible": False},
        },
    },
    "03 Damage AUB": {
        "color": (135, 16, 20, 255),
        "visible": False,
        "children": {
            "Natural Damage": {"color": (107, 47, 36, 255), "visible": False},
            "Institutional Damage": {"color": (160, 80, 64, 255), "visible": False},
            "Greenhouse Damage": {"color": (176, 96, 64, 255), "visible": False},
            "Road Damage": {"color": (196, 92, 72, 255), "visible": False},
            "Damaged Building Points": {"color": (135, 16, 20, 255), "visible": False},
            "Institutional Building Damage": {"color": (4, 113, 138, 255), "visible": False},
        },
    },
    "04 3D Map AUB": {
        "color": (135, 16, 20, 255),
        "visible": False,
        "children": {
            "Buildings Damage": {"color": (135, 16, 20, 255), "visible": False},
        },
    },
    "05 People and Place": {
        "color": (36, 93, 123, 255),
        "visible": False,
        "children": {
            "Narratives": {"color": (36, 93, 123, 255), "visible": False},
        },
    },
    "06 Heritage": {
        "color": (212, 168, 90, 255),
        "visible": False,
        "children": {
            "Heritage Sites": {"color": (212, 168, 90, 255), "visible": False},
            "Heritage Buildings": {"color": (227, 192, 122, 255), "visible": False},
        },
    },
}


def to_xy(lon, lat):
    x = math.radians(lon - ORIGIN_LON) * EARTH * math.cos(LAT0)
    y = math.radians(lat - ORIGIN_LAT) * EARTH
    return x, y


def lonlat_to_pixel(lon, lat, zoom):
    scale = 2**zoom * 256
    x = (lon + 180.0) / 360.0 * scale
    lat_r = math.radians(lat)
    y = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * scale
    return x, y


def tile_range(zoom):
    x0, y1 = lonlat_to_pixel(WEST, SOUTH, zoom)
    x1, y0 = lonlat_to_pixel(EAST, NORTH, zoom)
    return (
        math.floor(x0 / 256),
        math.floor(y0 / 256),
        math.floor(x1 / 256),
        math.floor(y1 / 256),
    )


def fetch_tile(tx, ty, zoom):
    url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{tx}/{ty}.png"
    request = urllib.request.Request(url, headers={"User-Agent": "rafah-map/1.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read()
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    pixels = list(image.getdata())
    return [(red * 256 + green + blue / 256.0) - 32768.0 for red, green, blue in pixels]


class Terrain:
    def __init__(self):
        self.zoom = TERRAIN_ZOOM
        self.tiles = {}
        self.fallback = 70.0

    def load(self):
        tx0, ty0, tx1, ty1 = tile_range(self.zoom)
        print(f"Elevation tiles z{self.zoom}: x {tx0}-{tx1}, y {ty0}-{ty1}")
        samples = []
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                print(f"  tile {tx}/{ty}")
                self.tiles[(tx, ty)] = fetch_tile(tx, ty, self.zoom)
                samples.append(self.tiles[(tx, ty)][128 * 256 + 128])
        if samples:
            samples.sort()
            self.fallback = samples[len(samples) // 2]

    def in_rafah(self, lon, lat):
        return WEST <= lon <= EAST and SOUTH <= lat <= NORTH

    def height(self, lon, lat):
        if not self.in_rafah(lon, lat):
            return self.fallback
        px, py = lonlat_to_pixel(lon, lat, self.zoom)
        x0, y0 = math.floor(px), math.floor(py)
        dx, dy = px - x0, py - y0
        try:
            h00 = self._pixel(x0, y0)
            h10 = self._pixel(x0 + 1, y0)
            h01 = self._pixel(x0, y0 + 1)
            h11 = self._pixel(x0 + 1, y0 + 1)
        except KeyError:
            return self.fallback
        return (
            h00 * (1 - dx) * (1 - dy)
            + h10 * dx * (1 - dy)
            + h01 * (1 - dx) * dy
            + h11 * dx * dy
        )

    def _pixel(self, px, py):
        tile = self.tiles[(px // 256, py // 256)]
        return tile[(py % 256) * 256 + (px % 256)]


def signed_area(points):
    area = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return area / 2


def clean_ring(coords):
    points = []
    for lon, lat in coords:
        xy = to_xy(lon, lat)
        if not points or (abs(points[-1][0] - xy[0]) > 0.05 or abs(points[-1][1] - xy[1]) > 0.05):
            points.append((xy[0], xy[1], lon, lat))
    if len(points) > 1 and abs(points[0][0] - points[-1][0]) < 0.05 and abs(points[0][1] - points[-1][1]) < 0.05:
        points.pop()
    return points


def triangulate(points):
    count = len(points)
    if count < 3:
        return []
    if count == 3:
        return [(0, 1, 2)]
    index = list(range(count))
    triangles = []

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def contains(a, b, c, p):
        c1 = cross(a, b, p)
        c2 = cross(b, c, p)
        c3 = cross(c, a, p)
        return c1 > 1e-8 and c2 > 1e-8 and c3 > 1e-8

    guard = 0
    while len(index) > 3 and guard < count * count:
        guard += 1
        clipped = False
        n = len(index)
        for i in range(n):
            i0, i1, i2 = index[i - 1], index[i], index[(i + 1) % n]
            a, b, c = points[i0], points[i1], points[i2]
            if cross(a, b, c) <= 1e-8:
                continue
            if any(contains(a, b, c, points[j]) for j in index if j not in (i0, i1, i2)):
                continue
            triangles.append((i0, i1, i2))
            del index[i]
            clipped = True
            break
        if not clipped:
            break
    if len(index) == 3:
        triangles.append(tuple(index))
    if not triangles:
        for i in range(1, count - 1):
            triangles.append((0, i, i + 1))
    return triangles


def rgba(hex_color, alpha=255):
    value = hex_color.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)


def add_layer(model, name, color, parent_id=None, visible=True):
    layer = rhino3dm.Layer()
    layer.Name = name
    layer.Color = color
    layer.Visible = visible
    if parent_id is not None:
        layer.ParentLayerId = parent_id
    return model.Layers.Add(layer)


def build_layers(model):
    ids = {}
    for parent_name, parent in LAYER_TREE.items():
        parent_index = add_layer(model, parent_name, parent["color"], visible=parent["visible"])
        parent_id = model.Layers[parent_index].Id
        ids[parent_name] = parent_index
        for child_name, child in parent["children"].items():
            path = f"{parent_name}::{child_name}"
            ids[path] = add_layer(
                model,
                child_name,
                child["color"],
                parent_id=parent_id,
                visible=child["visible"],
            )
    return ids


def attributes(layer_index, name, color, **user_text):
    attr = rhino3dm.ObjectAttributes()
    attr.LayerIndex = layer_index
    attr.Name = (name or "")[:250]
    attr.ObjectColor = color
    attr.ColorSource = rhino3dm.ObjectColorSource.ColorFromObject
    for key, value in user_text.items():
        if value not in (None, ""):
            attr.SetUserString(key, str(value)[:900])
    return attr


def extrude_building(points, height, terrain):
    if signed_area([(p[0], p[1]) for p in points]) < 0:
        points = list(reversed(points))
    flat = [(p[0], p[1]) for p in points]
    if abs(signed_area(flat)) < 0.5:
        return None
    triangles = triangulate(flat)
    if not triangles:
        return None
    mesh = rhino3dm.Mesh()
    n = len(points)
    bases = []
    for x, y, lon, lat in points:
        base = terrain.height(lon, lat)
        bases.append(base)
        mesh.Vertices.Add(x, y, base)
    for (x, y, _, _), base in zip(points, bases):
        mesh.Vertices.Add(x, y, base + max(height, 1.0))
    for i0, i1, i2 in triangles:
        mesh.Faces.AddFace(i0, i2, i1)
        mesh.Faces.AddFace(i0 + n, i1 + n, i2 + n)
    for i in range(n):
        j = (i + 1) % n
        mesh.Faces.AddFace(i, j, j + n, i + n)
    mesh.Normals.ComputeNormals()
    return mesh


def flat_mesh(points, terrain, lift=0.35):
    if signed_area([(p[0], p[1]) for p in points]) < 0:
        points = list(reversed(points))
    flat = [(p[0], p[1]) for p in points]
    if abs(signed_area(flat)) < 0.2:
        return None
    triangles = triangulate(flat)
    if not triangles:
        return None
    mesh = rhino3dm.Mesh()
    for x, y, lon, lat in points:
        mesh.Vertices.Add(x, y, terrain.height(lon, lat) + lift)
    for i0, i1, i2 in triangles:
        mesh.Faces.AddFace(i0, i1, i2)
    mesh.Normals.ComputeNormals()
    return mesh


def terrain_mesh(terrain):
    px0, py1 = lonlat_to_pixel(WEST, SOUTH, terrain.zoom)
    px1, py0 = lonlat_to_pixel(EAST, NORTH, terrain.zoom)
    cols = list(range(math.floor(px0), math.ceil(px1), TERRAIN_STEP))
    rows = list(range(math.floor(py0), math.ceil(py1), TERRAIN_STEP))
    mesh = rhino3dm.Mesh()
    index = {}
    for row, py in enumerate(rows):
        for col, px in enumerate(cols):
            scale = 2**terrain.zoom * 256
            lon = px / scale * 360 - 180
            lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / scale))))
            x, y = to_xy(lon, lat)
            mesh.Vertices.Add(x, y, terrain.height(lon, lat))
            index[(col, row)] = len(index)
    for row in range(len(rows) - 1):
        for col in range(len(cols) - 1):
            a = index[(col, row)]
            b = index[(col + 1, row)]
            c = index[(col + 1, row + 1)]
            d = index[(col, row + 1)]
            mesh.Faces.AddFace(a, d, c, b)
    mesh.Normals.ComputeNormals()
    return mesh


def outer_rings(geometry):
    if not geometry:
        return []
    gtype = geometry.get("type")
    if gtype == "Polygon":
        polygons = [geometry["coordinates"]]
    elif gtype == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        return []
    rings = []
    for polygon in polygons:
        if not polygon:
            continue
        ring = polygon[0]
        while ring and isinstance(ring[0][0], (list, tuple)):
            ring = ring[0]
        rings.append(ring)
    return rings


def load_geojson(path: Path):
    if not path.exists():
        print(f"  missing {path}")
        return []
    with path.open(encoding="utf-8") as handle:
        return json.load(handle).get("features") or []


def useful_name(props: dict) -> str:
    for key in (
        "title",
        "Narratives",
        "NameEn",
        "name_en",
        "Building_N",
        "BuildingNa",
        "Name",
        "name",
        "name_ar",
        "NameAr",
    ):
        value = props.get(key)
        if value in (None, "", "Null", "null", "yes"):
            continue
        text = str(value).strip()
        if text and not text.isdigit():
            return text
    for key in ("building", "Building_T", "BuildingType", "fclass", "RoadType", "theme", "Theme", "damage", "Damage"):
        value = props.get(key)
        if value not in (None, "", "Null", "null", "yes"):
            return str(value)
    return ""


def add_extruded_buildings(model, layer_index, features, terrain, color_fn, label):
    kept = 0
    for feature in features:
        geometry = feature.get("geometry") or {}
        props = feature.get("properties") or {}
        height = float(props.get("height_m") or props.get("ELEVATION") or 6.4)
        color = color_fn(props)
        name = useful_name(props)
        for ring in outer_rings(geometry):
            points = clean_ring(ring)
            if len(points) < 3:
                continue
            mesh = extrude_building(points, height, terrain)
            if mesh is None:
                continue
            model.Objects.AddMesh(
                mesh,
                attributes(
                    layer_index,
                    name,
                    color,
                    building=props.get("building") or props.get("Building_T"),
                    damage=props.get("damage") or props.get("Damage") or props.get("AllDamage"),
                    height_m=f"{height:.1f}",
                    source=label,
                ),
            )
            kept += 1
    print(f"  {kept} {label}")
    return kept


def add_flat_polygons(model, layer_index, features, terrain, color, lift=0.4, color_fn=None):
    kept = 0
    for feature in features:
        props = feature.get("properties") or {}
        name = useful_name(props)
        fill = color_fn(props) if color_fn else color
        for ring in outer_rings(feature.get("geometry") or {}):
            # Cap very dense rings for export speed
            if len(ring) > 80:
                step = max(1, len(ring) // 60)
                ring = ring[::step]
                if ring[0] != ring[-1]:
                    ring = ring + [ring[0]]
            points = clean_ring(ring)
            if len(points) < 3:
                continue
            mesh = flat_mesh(points, terrain, lift=lift)
            if mesh is None:
                continue
            model.Objects.AddMesh(
                mesh,
                attributes(
                    layer_index,
                    name,
                    fill,
                    damage=props.get("damage") or props.get("Damage"),
                    fclass=props.get("fclass") or props.get("BuildingType"),
                ),
            )
            kept += 1
    print(f"  {kept} polygons")
    return kept


def add_polylines(model, layer_index, features, terrain, color, lift=0.5):
    kept = 0
    for feature in features:
        geometry = feature.get("geometry") or {}
        props = feature.get("properties") or {}
        gtype = geometry.get("type")
        runs = []
        if gtype == "LineString":
            runs = [geometry.get("coordinates") or []]
        elif gtype == "MultiLineString":
            runs = geometry.get("coordinates") or []
        elif gtype in {"Polygon", "MultiPolygon"}:
            runs = outer_rings(geometry)
        for run in runs:
            if len(run) < 2:
                continue
            line = rhino3dm.Polyline()
            for lon, lat in run:
                if isinstance(lon, (list, tuple)):
                    continue
                x, y = to_xy(lon, lat)
                line.Add(x, y, terrain.height(lon, lat) + lift)
            if line.Count < 2:
                continue
            model.Objects.AddPolyline(
                line,
                attributes(
                    layer_index,
                    useful_name(props),
                    color,
                    road=props.get("RoadType") or props.get("highway"),
                    damage=props.get("damage") or props.get("Damage"),
                ),
            )
            kept += 1
    print(f"  {kept} lines")
    return kept


def add_points(model, layer_index, features, terrain, color_fn, radius=8.0, lift=4.0):
    kept = 0
    for feature in features:
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            continue
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = coords[0], coords[1]
        x, y = to_xy(lon, lat)
        z = terrain.height(lon, lat) + lift
        props = feature.get("properties") or {}
        color = color_fn(props)
        sphere = rhino3dm.Sphere(rhino3dm.Point3d(x, y, z), radius)
        brep = sphere.ToBrep()
        if brep is None:
            continue
        model.Objects.AddBrep(
            brep,
            attributes(
                layer_index,
                useful_name(props),
                color,
                theme=props.get("theme") or props.get("Theme"),
                damage=props.get("damage") or props.get("Damage"),
                category=props.get("category") or props.get("Categories") or props.get("Category"),
                description=(props.get("description") or props.get("Description") or "")[:400],
            ),
        )
        kept += 1
    print(f"  {kept} points")
    return kept


def osm_building_color(props):
    return OSM_BUILDING_COLORS.get(props.get("building"), (196, 179, 154, 255))


def damage_building_color(props):
    key = props.get("damage") or props.get("Damage") or props.get("AllDamage") or "No Damage"
    return DAMAGE_COLORS.get(key, (170, 170, 170, 255))


def people_color(props):
    key = props.get("theme") or props.get("Theme") or ""
    return PEOPLE_COLORS.get(key, (136, 136, 136, 255))


def add_named_view(model, name, lon, lat, zoom, pitch, bearing, terrain):
    tx, ty = to_xy(lon, lat)
    tz = terrain.height(lon, lat)
    mpp = 156543.03 * math.cos(math.radians(lat)) / (2**zoom)
    dist = max(250.0, mpp * 900.0)
    pitch_r = math.radians(pitch)
    bearing_r = math.radians(bearing)
    horiz = dist * math.cos(pitch_r)
    vert = max(80.0, dist * math.sin(pitch_r))
    # Camera sits opposite the map "up" direction
    cam_x = tx - horiz * math.sin(bearing_r)
    cam_y = ty - horiz * math.cos(bearing_r)
    cam_z = tz + vert

    view = rhino3dm.ViewInfo()
    view.Name = name
    # rhino3dm signature: targetDistance, symmetricFrustum, lensLength
    view.Viewport.ChangeToPerspectiveProjection(dist, True, 50)
    view.Viewport.SetCameraLocation(rhino3dm.Point3d(cam_x, cam_y, cam_z))
    view.Viewport.SetCameraDirection(rhino3dm.Vector3d(tx - cam_x, ty - cam_y, tz - cam_z))
    view.Viewport.SetCameraUp(rhino3dm.Vector3d(0, 0, 1))
    model.NamedViews.Add(view)


def main():
    terrain = Terrain()
    terrain.load()

    model = rhino3dm.File3dm()
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Meters
    model.StartSectionComments = (
        "Rafah 3D map — matches the web map views. Units: meters. "
        f"XY origin: {ORIGIN_LON} E, {ORIGIN_LAT} N. Z: metres above sea level. "
        "Use rhino/Set Map View.py inside Rhino to switch OpenStreetMap / Basemap / "
        "Damage / 3D Map / People and Place / Heritage, same as the web Map view menu. "
        "Named views: City, Governorate, People and Heritage."
    )

    layers = build_layers(model)

    print("Terrain…")
    model.Objects.AddMesh(
        terrain_mesh(terrain),
        attributes(layers["Shared::Terrain"], "Rafah terrain", (176, 154, 120, 255), source="AWS Terrain Tiles"),
    )

    print("Buildings OSM…")
    add_extruded_buildings(
        model,
        layers["01 OpenStreetMap::Buildings OSM"],
        load_geojson(RAFAH / "buildings.geojson"),
        terrain,
        osm_building_color,
        "OSM buildings",
    )

    print("Buildings Damage (AUB)…")
    add_extruded_buildings(
        model,
        layers["04 3D Map AUB::Buildings Damage"],
        load_geojson(URBICIDE / "buildings.geojson"),
        terrain,
        damage_building_color,
        "AUB damage buildings",
    )

    print("Roads OSM…")
    margin = 0.008

    def inside(lon, lat):
        return WEST - margin <= lon <= EAST + margin and SOUTH - margin <= lat <= NORTH + margin

    road_feats = []
    for feature in load_geojson(RAFAH / "roads.geojson"):
        coords = feature.get("geometry", {}).get("coordinates") or []
        runs = []
        current = []
        for lon, lat in coords:
            if inside(lon, lat):
                current.append((lon, lat))
            elif len(current) >= 2:
                runs.append(current)
                current = []
            else:
                current = []
        if len(current) >= 2:
            runs.append(current)
        for run in runs:
            road_feats.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": run},
                    "properties": feature.get("properties") or {},
                }
            )
    add_polylines(model, layers["Shared::Roads OSM"], road_feats, terrain, (242, 226, 196, 255), lift=0.4)

    print("Boundary…")
    add_polylines(
        model,
        layers["Shared::Boundary"],
        load_geojson(RAFAH / "boundary.geojson"),
        terrain,
        (227, 177, 90, 255),
        lift=2.0,
    )

    print("Basemap AUB…")
    add_flat_polygons(
        model,
        layers["02 Basemap AUB::Agriculture"],
        load_geojson(AUB / "agriculture.geojson"),
        terrain,
        (111, 143, 78, 255),
        lift=0.3,
    )
    # Keep greenhouses readable but lighter for the .3dm size limit.
    greenhouses = load_geojson(AUB / "greenhouses.geojson")
    if len(greenhouses) > 12000:
        greenhouses = greenhouses[::2]
    add_flat_polygons(
        model,
        layers["02 Basemap AUB::Greenhouses"],
        greenhouses,
        terrain,
        (155, 187, 110, 255),
        lift=0.45,
    )
    add_flat_polygons(
        model,
        layers["02 Basemap AUB::Institutional Land"],
        load_geojson(AUB / "institutional_land.geojson"),
        terrain,
        (122, 158, 142, 255),
        lift=0.35,
    )
    add_flat_polygons(
        model,
        layers["02 Basemap AUB::Coast"],
        load_geojson(AUB / "coast.geojson"),
        terrain,
        (106, 142, 168, 255),
        lift=0.2,
    )
    add_flat_polygons(
        model,
        layers["02 Basemap AUB::Cemetery Recreation"],
        load_geojson(AUB / "cemetery_recreation.geojson"),
        terrain,
        (138, 122, 106, 255),
        lift=0.35,
    )
    add_polylines(
        model,
        layers["02 Basemap AUB::Neighborhoods"],
        load_geojson(AUB / "neighborhoods.geojson"),
        terrain,
        (200, 190, 175, 255),
        lift=1.0,
    )
    add_points(
        model,
        layers["02 Basemap AUB::Camps"],
        load_geojson(AUB / "camps.geojson"),
        terrain,
        lambda _p: (227, 177, 90, 255),
        radius=18.0,
        lift=6.0,
    )
    add_points(
        model,
        layers["02 Basemap AUB::Institutions"],
        load_geojson(AUB / "institutions.geojson"),
        terrain,
        lambda _p: (215, 195, 162, 255),
        radius=6.0,
        lift=5.0,
    )

    print("Damage AUB overlays…")
    add_flat_polygons(
        model,
        layers["03 Damage AUB::Natural Damage"],
        load_geojson(AUB / "natural_damage.geojson"),
        terrain,
        (107, 47, 36, 255),
        lift=0.5,
    )
    add_flat_polygons(
        model,
        layers["03 Damage AUB::Institutional Damage"],
        load_geojson(AUB / "institutional_damage.geojson"),
        terrain,
        (160, 80, 64, 255),
        lift=0.55,
    )
    greenhouse_damage = [
        f
        for f in load_geojson(AUB / "greenhouse_damage.geojson")
        if "رفح" in str((f.get("properties") or {}).get("Mohafaz") or "")
    ]
    add_flat_polygons(
        model,
        layers["03 Damage AUB::Greenhouse Damage"],
        greenhouse_damage,
        terrain,
        (176, 96, 64, 255),
        lift=0.5,
    )
    add_polylines(
        model,
        layers["03 Damage AUB::Road Damage"],
        load_geojson(AUB / "road_damage.geojson"),
        terrain,
        (196, 92, 72, 255),
        lift=0.7,
    )
    # These AUB layers are footprints (polygons), not true points.
    add_flat_polygons(
        model,
        layers["03 Damage AUB::Damaged Building Points"],
        load_geojson(AUB / "damaged_buildings_pts.geojson"),
        terrain,
        (135, 16, 20, 255),
        lift=0.85,
        color_fn=damage_building_color,
    )
    add_flat_polygons(
        model,
        layers["03 Damage AUB::Institutional Building Damage"],
        load_geojson(AUB / "institutional_building_damage.geojson"),
        terrain,
        (4, 113, 138, 255),
        lift=0.9,
        color_fn=damage_building_color,
    )

    print("People & Place…")
    add_points(
        model,
        layers["05 People and Place::Narratives"],
        load_geojson(AUB / "people_and_place.geojson"),
        terrain,
        people_color,
        radius=22.0,
        lift=12.0,
    )

    print("Heritage…")
    add_flat_polygons(
        model,
        layers["06 Heritage::Heritage Sites"],
        load_geojson(AUB / "heritage_sites_poly.geojson"),
        terrain,
        (139, 107, 61, 255),
        lift=0.6,
    )
    add_points(
        model,
        layers["06 Heritage::Heritage Sites"],
        load_geojson(AUB / "heritage_sites.geojson"),
        terrain,
        lambda _p: (212, 168, 90, 255),
        radius=14.0,
        lift=8.0,
    )
    add_flat_polygons(
        model,
        layers["06 Heritage::Heritage Buildings"],
        load_geojson(AUB / "heritage_buildings_poly.geojson"),
        terrain,
        (176, 137, 79, 255),
        lift=0.7,
    )
    add_points(
        model,
        layers["06 Heritage::Heritage Buildings"],
        load_geojson(AUB / "heritage_buildings.geojson"),
        terrain,
        lambda _p: (227, 192, 122, 255),
        radius=10.0,
        lift=7.0,
    )

    print("Named views…")
    add_named_view(model, "City", 34.254, 31.281, 15.5, 60, -28, terrain)
    add_named_view(model, "Governorate", 34.272, 31.283, 12.15, 48, -12, terrain)
    add_named_view(model, "People and Heritage", 34.45, 31.45, 10.2, 45, -8, terrain)

    if not model.Write(str(OUT), 8):
        raise SystemExit("Rhino could not write the 3dm")
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1_048_576:.1f} MB)")
    print("Open in Rhino, then run rhino/Set Map View.py to switch views like the web map.")


if __name__ == "__main__":
    main()
