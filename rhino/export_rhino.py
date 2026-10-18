#!/usr/bin/env python3
"""Write a Rhino 3dm of Rafah: terrain, extruded buildings, roads, boundary.

Units are meters. XY is a local grid whose origin is 34.25 E, 31.28 N.
Z is meters above sea level. Rhino 7 and Rhino 8 can open the file.
"""

import io
import json
import math
import urllib.request
from pathlib import Path

import rhino3dm
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rafah"
OUT = Path(__file__).resolve().parent / "Rafah.3dm"

ORIGIN_LON = 34.25
ORIGIN_LAT = 31.28
EARTH = 6_378_137.0
LAT0 = math.radians(ORIGIN_LAT)
SOUTH, WEST, NORTH, EAST = 31.2201289, 34.2158979, 31.3457700, 34.3294070
TERRAIN_ZOOM = 13
TERRAIN_STEP = 2

BUILDING_COLORS = {
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

    def height(self, lon, lat):
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
    """Ear-clip a polygon. points are (x, y) in CCW order."""
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


def add_layer(model, name, color):
    layer = rhino3dm.Layer()
    layer.Name = name
    layer.Color = color
    return model.Layers.Add(layer)


def attributes(layer_index, name, color, **user_text):
    attr = rhino3dm.ObjectAttributes()
    attr.LayerIndex = layer_index
    attr.Name = name or ""
    attr.ObjectColor = color
    attr.ColorSource = rhino3dm.ObjectColorSource.ColorFromObject
    for key, value in user_text.items():
        if value not in (None, ""):
            attr.SetUserString(key, str(value))
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
        mesh.Vertices.Add(x, y, base + height)
    for i0, i1, i2 in triangles:
        mesh.Faces.AddFace(i0, i2, i1)
        mesh.Faces.AddFace(i0 + n, i1 + n, i2 + n)
    for i in range(n):
        j = (i + 1) % n
        mesh.Faces.AddFace(i, j, j + n, i + n)
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
            # rows run north to south in pixel space, so flip the quad
            mesh.Faces.AddFace(a, d, c, b)
    mesh.Normals.ComputeNormals()
    return mesh


def outer_rings(geometry):
    """Return exterior rings as lists of [lon, lat], including a bad extra nest."""
    if geometry["type"] == "Polygon":
        polygons = [geometry["coordinates"]]
    else:
        polygons = geometry["coordinates"]
    rings = []
    for polygon in polygons:
        ring = polygon[0]
        while ring and isinstance(ring[0][0], (list, tuple)):
            ring = ring[0]
        rings.append(ring)
    return rings


def load_features(name):
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)["features"]


def main():
    terrain = Terrain()
    terrain.load()

    model = rhino3dm.File3dm()
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Meters
    model.StartSectionComments = (
        "Rafah 3D map. Units: meters. "
        f"XY origin: {ORIGIN_LON} E, {ORIGIN_LAT} N. "
        "Z: meters above sea level. "
        "Buildings and roads: OpenStreetMap. Elevation: AWS Terrain Tiles."
    )

    terrain_layer = add_layer(model, "Terrain", (176, 154, 120, 255))
    building_layer = add_layer(model, "Buildings", (196, 179, 154, 255))
    road_layer = add_layer(model, "Roads", (90, 84, 74, 255))
    boundary_layer = add_layer(model, "Boundary", (227, 177, 90, 255))

    print("Terrain mesh…")
    ground = terrain_mesh(terrain)
    model.Objects.AddMesh(
        ground,
        attributes(terrain_layer, "Rafah terrain", (176, 154, 120, 255), source="AWS Terrain Tiles"),
    )

    print("Buildings…")
    kept = 0
    for feature in load_features("buildings.geojson"):
        geometry = feature["geometry"]
        props = feature["properties"]
        rings = outer_rings(geometry)
        height = float(props.get("height_m") or 6.4)
        color = BUILDING_COLORS.get(props.get("building"), (196, 179, 154, 255))
        for ring in rings:
            points = clean_ring(ring)
            if len(points) < 3:
                continue
            mesh = extrude_building(points, height, terrain)
            if mesh is None:
                continue
            model.Objects.AddMesh(
                mesh,
                attributes(
                    building_layer,
                    props.get("name") or props.get("name_ar") or "",
                    color,
                    building=props.get("building"),
                    height_m=f"{height:.1f}",
                    osm_id=props.get("osm_id"),
                    name_ar=props.get("name_ar"),
                ),
            )
            kept += 1
    print(f"  {kept} buildings")

    print("Roads…")
    margin = 0.008
    roads = 0

    def inside_rafah(lon, lat):
        return WEST - margin <= lon <= EAST + margin and SOUTH - margin <= lat <= NORTH + margin

    for feature in load_features("roads.geojson"):
        coords = feature["geometry"]["coordinates"]
        runs = []
        current = []
        for lon, lat in coords:
            if inside_rafah(lon, lat):
                current.append((lon, lat))
            elif len(current) >= 2:
                runs.append(current)
                current = []
            else:
                current = []
        if len(current) >= 2:
            runs.append(current)
        props = feature["properties"]
        for run in runs:
            line = rhino3dm.Polyline()
            for lon, lat in run:
                x, y = to_xy(lon, lat)
                line.Add(x, y, terrain.height(lon, lat) + 0.4)
            model.Objects.AddPolyline(
                line,
                attributes(
                    road_layer,
                    props.get("name") or "",
                    (90, 84, 74, 255),
                    highway=props.get("highway"),
                    osm_id=props.get("osm_id"),
                ),
            )
            roads += 1
    print(f"  {roads} roads")

    print("Boundary…")
    for feature in load_features("boundary.geojson"):
        for ring in outer_rings(feature["geometry"]):
            line = rhino3dm.Polyline()
            for lon, lat in ring:
                x, y = to_xy(lon, lat)
                line.Add(x, y, terrain.height(lon, lat) + 2.0)
            if line.Count > 2:
                line.Add(line[0].X, line[0].Y, line[0].Z)
            model.Objects.AddPolyline(
                line,
                attributes(boundary_layer, "محافظة رفح", (227, 177, 90, 255), boundary="administrative"),
            )

    if not model.Write(str(OUT), 7):
        raise SystemExit("Rhino could not write the 3dm")
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()
