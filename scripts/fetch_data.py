#!/usr/bin/env python3
"""Download Rafah buildings, roads, and the governorate boundary from OpenStreetMap."""

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rafah"
DATA.mkdir(exist_ok=True)

# Rafah Governorate, Palestine — OSM relation 4731201
SOUTH, WEST, NORTH, EAST = 31.2201289, 34.2158979, 31.3457700, 34.3294070
BBOX = f"{SOUTH},{WEST},{NORTH},{EAST}"
SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def overpass(query: str) -> dict:
    payload = urllib.parse.urlencode({"data": query}).encode()
    last_error = None
    for url in SERVERS:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"User-Agent": "rafah-map/1.0 (local 3d map)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=240) as resp:
                return json.load(resp)
        except Exception as exc:  # noqa: BLE001 — try the next public server
            last_error = exc
            print(f"  {url} failed: {exc}")
    raise SystemExit(f"Overpass request failed: {last_error}")


def num(tags: dict, key: str):
    raw = tags.get(key)
    if not raw:
        return None
    token = str(raw).strip().lower().replace("meters", "").replace("meter", "").replace("m", "")
    token = token.replace(",", ".").split(";")[0].strip()
    try:
        return float(token)
    except ValueError:
        return None


DEFAULT_LEVELS = {
    "house": 2,
    "detached": 2,
    "semidetached_house": 2,
    "terrace": 2,
    "bungalow": 1,
    "apartments": 5,
    "residential": 3,
    "dormitory": 4,
    "commercial": 2,
    "retail": 1,
    "office": 3,
    "industrial": 1,
    "warehouse": 1,
    "school": 2,
    "university": 3,
    "hospital": 3,
    "mosque": 2,
    "church": 2,
    "civic": 2,
    "public": 2,
    "yes": 2,
    "hut": 1,
    "cabin": 1,
    "garage": 1,
    "shed": 1,
    "roof": 1,
}


def height_m(tags: dict) -> float:
    height = num(tags, "height")
    if height and height > 0:
        return height
    levels = num(tags, "building:levels")
    if not levels or levels <= 0:
        levels = DEFAULT_LEVELS.get(tags.get("building", "yes"), 2)
    return levels * 3.2


def ring(geometry) -> list:
    coords = [[point["lon"], point["lat"]] for point in geometry or []]
    if len(coords) >= 2 and coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def way_polygon(element):
    coords = ring(element.get("geometry"))
    if len(coords) < 4 or coords[0] != coords[-1]:
        return None
    return {"type": "Polygon", "coordinates": [coords]}


def relation_polygons(element):
    outers, inners = [], []
    for member in element.get("members") or []:
        if member.get("type") != "way":
            continue
        coords = ring(member.get("geometry"))
        if len(coords) < 4 or coords[0] != coords[-1]:
            continue
        if member.get("role") == "inner":
            inners.append(coords)
        else:
            outers.append(coords)
    if not outers:
        return None
    if len(outers) == 1:
        return {"type": "Polygon", "coordinates": [outers[0], *inners]}
    return {"type": "MultiPolygon", "coordinates": [[outer] for outer in outers]}


def feature(element, geometry, extra):
    tags = element.get("tags") or {}
    props = {
        "osm_id": element.get("id"),
        "osm_type": element.get("type"),
        "name": tags.get("name") or tags.get("name:en") or tags.get("name:ar"),
        "name_ar": tags.get("name:ar"),
        "name_en": tags.get("name:en"),
    }
    props.update(extra)
    props = {key: value for key, value in props.items() if value not in (None, "")}
    return {"type": "Feature", "properties": props, "geometry": geometry}


def save(name: str, features: list) -> None:
    collection = {"type": "FeatureCollection", "features": features}
    path = DATA / name
    with path.open("w", encoding="utf-8") as handle:
        json.dump(collection, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote {name}: {len(features)} features, {path.stat().st_size / 1_048_576:.1f} MB")


def main() -> None:
    print("Fetching buildings…")
    buildings = overpass(
        f"""
        [out:json][timeout:180];
        (
          way["building"]({BBOX});
          relation["building"]({BBOX});
        );
        out geom;
        """
    )
    building_features = []
    for element in buildings.get("elements", []):
        if element["type"] == "way":
            geometry = way_polygon(element)
        elif element["type"] == "relation":
            geometry = relation_polygons(element)
        else:
            continue
        if not geometry:
            continue
        tags = element.get("tags") or {}
        building_features.append(
            feature(
                element,
                geometry,
                {
                    "building": tags.get("building", "yes"),
                    "height_m": round(height_m(tags), 2),
                    "levels": num(tags, "building:levels"),
                    "amenity": tags.get("amenity"),
                },
            )
        )
    save("buildings.geojson", building_features)

    print("Fetching roads…")
    roads = overpass(
        f"""
        [out:json][timeout:180];
        way["highway"]({BBOX});
        out geom;
        """
    )
    road_features = []
    for element in roads.get("elements", []):
        coords = [[point["lon"], point["lat"]] for point in element.get("geometry") or []]
        if len(coords) < 2:
            continue
        tags = element.get("tags") or {}
        road_features.append(
            feature(
                element,
                {"type": "LineString", "coordinates": coords},
                {"highway": tags.get("highway"), "surface": tags.get("surface")},
            )
        )
    save("roads.geojson", road_features)

    print("Fetching governorate boundary…")
    boundary = overpass(
        """
        [out:json][timeout:90];
        relation(4731201);
        out geom;
        """
    )
    boundary_features = []
    for element in boundary.get("elements", []):
        geometry = relation_polygons(element)
        if not geometry:
            continue
        tags = element.get("tags") or {}
        boundary_features.append(
            feature(
                element,
                geometry,
                {
                    "boundary": tags.get("boundary"),
                    "admin_level": tags.get("admin_level"),
                },
            )
        )
    save("boundary.geojson", boundary_features)

    meta = {
        "place": "Rafah Governorate",
        "place_ar": "محافظة رفح",
        "osm_relation": 4731201,
        "bbox": {"south": SOUTH, "west": WEST, "north": NORTH, "east": EAST},
        "center": [34.248, 31.287],
        "fetched": "2026-10-18",
        "counts": {
            "buildings": len(building_features),
            "roads": len(road_features),
        },
        "sources": {
            "vector": "OpenStreetMap via the Overpass API",
            "elevation": "AWS Terrain Tiles, Terrarium encoding (SRTM and related DEMs)",
            "catalog": "https://data.nextgis.com/en/data-samples/#formats-base",
        },
    }
    (DATA / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Done.")


if __name__ == "__main__":
    main()
