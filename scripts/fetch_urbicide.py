#!/usr/bin/env python3
"""Download Rafah building-damage footprints from the AUB ArcGIS experience."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "urbicide"
OUT.mkdir(parents=True, exist_ok=True)

LAYER = (
    "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
    "GazaBuilding_26_03_2024/FeatureServer/0"
)
WHERE = "Mohafaza='محافظة رفح'"
PAGE = 2000
UA = "rafah-map/1.0 (local 3d map; urbicide download)"
SOURCE = {
    "experience": "https://experience.arcgis.com/experience/5c24d93ffc234d709efbbeb355d9496c/page/Page?views=3D-Map",
    "web_scene": "https://www.arcgis.com/home/item.html?id=e6f1cab62fda40608dee21f5081f7c60",
    "layer": LAYER,
    "credit": "Tracking The Urbicide in Gaza — American University of Beirut (AUB) / ArcGIS Online",
}

OUT_FIELDS = [
    "OBJECTID",
    "Building_ID",
    "Building_Name",
    "Building_Type",
    "Categories_Type",
    "ELEVATION",
    "AllDamage",
    "Heritage",
]


def get_json(url: str, retries: int = 4) -> dict:
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"Request failed: {url}\n{last}")


def ring_to_coords(ring: list) -> list:
    return [[pt[0], pt[1]] for pt in ring]


def esri_polygon_to_geojson(geom: dict) -> dict | None:
    if not geom or not geom.get("rings"):
        return None
    rings = [ring_to_coords(ring) for ring in geom["rings"] if len(ring) >= 4]
    if not rings:
        return None
    if len(rings) == 1:
        return {"type": "Polygon", "coordinates": rings}
    return {"type": "MultiPolygon", "coordinates": [[ring] for ring in rings]}


def clean(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "nan"}:
        return None
    return text


def feature_from_esri(item: dict) -> dict | None:
    attrs = item.get("attributes") or {}
    geometry = esri_polygon_to_geojson(item.get("geometry") or {})
    if not geometry:
        return None
    name = clean(attrs.get("Building_Name"))
    building = clean(attrs.get("Building_Type")) or "yes"
    height = attrs.get("ELEVATION")
    try:
        height_m = float(height) if height is not None else 6.0
    except (TypeError, ValueError):
        height_m = 6.0
    if height_m <= 0:
        height_m = 3.0

    props = {
        "building": building,
        "height_m": height_m,
        "damage": clean(attrs.get("AllDamage")) or "No Damage",
        "source": "aub-urbicide",
    }
    if name:
        props["name"] = name
        props["name_ar"] = name
    amenity = clean(attrs.get("Categories_Type"))
    if amenity:
        props["amenity"] = amenity
    heritage = clean(attrs.get("Heritage"))
    if heritage:
        props["heritage"] = heritage
    building_id = clean(attrs.get("Building_ID"))
    if building_id:
        props["building_id"] = building_id
    return {"type": "Feature", "geometry": geometry, "properties": props}


def download_buildings() -> dict:
    count = get_json(
        LAYER
        + "/query?"
        + urllib.parse.urlencode({"where": WHERE, "returnCountOnly": "true", "f": "json"})
    )["count"]
    print(f"Rafah buildings to download: {count}")

    features: list[dict] = []
    offset = 0
    while offset < count:
        params = {
            "where": WHERE,
            "outFields": ",".join(OUT_FIELDS),
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": PAGE,
            "orderByFields": "OBJECTID ASC",
            "f": "json",
        }
        page = get_json(LAYER + "/query?" + urllib.parse.urlencode(params))
        batch = page.get("features") or []
        if not batch:
            break
        for item in batch:
            feat = feature_from_esri(item)
            if feat:
                features.append(feat)
        offset += len(batch)
        print(f"  {min(offset, count)} / {count}")
        if not page.get("exceededTransferLimit") and len(batch) < PAGE:
            break

    return {"type": "FeatureCollection", "features": features}


def damage_counts(collection: dict) -> dict:
    counts: dict[str, int] = {}
    for feat in collection["features"]:
        key = feat["properties"].get("damage") or "Unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def main() -> None:
    buildings = download_buildings()
    path = OUT / "buildings.geojson"
    path.write_text(json.dumps(buildings, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path} ({path.stat().st_size / 1_000_000:.1f} MB, {len(buildings['features'])} features)")

    meta = {
        "place": "Rafah Governorate",
        "place_ar": "محافظة رفح",
        "fetched_from": SOURCE,
        "counts": {
            "buildings": len(buildings["features"]),
            "damage": damage_counts(buildings),
        },
        "notes": (
            "Building footprints and cumulative damage (AllDamage) from the public "
            "'Tracking The Urbicide in Gaza' ArcGIS experience / Gaza3DMap_St web scene. "
            "Filtered to محافظة رفح."
        ),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote meta.json")


if __name__ == "__main__":
    main()
