#!/usr/bin/env python3
"""Download all public layers used by Tracking The Urbicide in Gaza (AUB).

Saves GeoJSON under data/aub/ for Basemap, Damage, People & Place, and Heritage.
Building damage for Rafah already lives in data/urbicide/ (see fetch_urbicide.py).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "aub"
OUT.mkdir(parents=True, exist_ok=True)

UA = "rafah-map/1.0 (local 3d map; aub urbicide download)"
PAGE = 2000
RAFAH_WHERE = "Mohafaza='محافظة رفح'"
BBOX = {
    "xmin": 34.2158979,
    "ymin": 31.2201289,
    "xmax": 34.3294070,
    "ymax": 31.34577,
    "spatialReference": {"wkid": 4326},
}
EXPERIENCE = (
    "https://experience.arcgis.com/experience/5c24d93ffc234d709efbbeb355d9496c/"
    "page/Page?views=3D-Map"
)

# name -> (url, mode: 'bbox' | 'all' | 'rafah_mohafaza', keep_fields or None)
LAYERS = {
    # Basemap
    "agriculture": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Map_AgriculturalLandscape_Greenhouse_NewLayers/FeatureServer/6",
        "bbox",
        ["name", "Area", "code", "fclass", "Mohafaz"],
    ),
    "greenhouses": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Map_AgriculturalLandscape_Greenhouse_NewLayers/FeatureServer/5",
        "bbox",
        ["Area", "build_id", "BuildingType", "Damage_111123", "Damage_300124"],
    ),
    "institutional_land": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Map_InstitutionalLandscapes/FeatureServer/0",
        "bbox",
        ["Name", "Damage_07Jan2024", "Damage_07Nov2023"],
    ),
    "coast": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/Coastal_Gaza/FeatureServer/0",
        "bbox",
        ["name", "code", "Damage_10_27", "Damage_11_11", "Damage_12_11"],
    ),
    "camps": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "GazaCamps_FeatureToPoint/FeatureServer/0",
        "all",
        ["Name"],
    ),
    "cemetery_recreation": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "GazaNewLayers_GovernebtLine_WaterWay_InstitutionalLS/FeatureServer/2",
        "bbox",
        ["Name", "Damage_11_11_2023", "Damage_27_10_2023", "Damage_30_01_2024"],
    ),
    "neighborhoods": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Gaza_Neighborhoods_OSM/FeatureServer/0",
        "bbox",
        None,
    ),
    "institutions": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Gaza_Institution_Labels_all/FeatureServer/0",
        "bbox",
        ["Building_I", "Building_N", "Building_T", "Categories", "Damage", "date", "Mohafaza"],
    ),
    # Damage overlays
    "agriculture_damage": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/a6bdfc/FeatureServer/0",
        "bbox",
        ["Area", "Classname", "date", "Mohafaz", "Damage"],
    ),
    "natural_damage": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/acaa80/FeatureServer/0",
        "bbox",
        ["Damage", "date", "fclass", "Mohafaz", "Mohafaza"],
    ),
    "institutional_damage": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/acd3e6/FeatureServer/0",
        "bbox",
        None,
    ),
    "greenhouse_damage": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/a59666/FeatureServer/0",
        "bbox",
        ["Damage", "date", "fclass", "Mohafaz"],
    ),
    "road_damage": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Gaza_RoadAssesment_20240529/FeatureServer/0",
        "bbox",
        None,
    ),
    "damaged_buildings_pts": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/aee2d9/FeatureServer/0",
        "bbox",
        None,
    ),
    "institutional_building_damage": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/a968e8/FeatureServer/0",
        "bbox",
        None,
    ),
    # People & Place (full Gaza narratives — small)
    "people_and_place": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/People_and_Place/FeatureServer/0",
        "all",
        [
            "OBJECTID",
            "N_No",
            "Narratives",
            "Location",
            "Theme",
            "Description",
            "Text_Sourc",
            "Text_Source_2",
            "Quote_1",
            "Quote_So",
            "media1",
            "media2",
            "media3",
            "Date1",
            "Date2",
            "Date3",
        ],
    ),
    # Heritage
    "heritage_sites_poly": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "Polygon_Master_Heritage/FeatureServer/0",
        "bbox",
        None,
    ),
    "heritage_sites": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/HeritageSites_2/FeatureServer/0",
        "bbox",
        None,
    ),
    "heritage_buildings": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
        "HeritageBldgCentroids_2025_01_31/FeatureServer/0",
        "bbox",
        None,
    ),
    "heritage_buildings_poly": (
        "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/ad6f25/FeatureServer/0",
        "bbox",
        None,
    ),
}

BUILDINGS = (
    "https://services3.arcgis.com/tuNLpt6Wfhd22qmO/arcgis/rest/services/"
    "GazaBuilding_26_03_2024/FeatureServer/0"
)


def get_json(url: str, retries: int = 5) -> dict:
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Request failed: {url}\n{last}")


def clean(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "nan"}:
        return None
    return text


def esri_geom_to_geojson(geom: dict | None) -> dict | None:
    if not geom:
        return None
    if "x" in geom and "y" in geom:
        return {"type": "Point", "coordinates": [geom["x"], geom["y"]]}
    if "paths" in geom:
        paths = [[[pt[0], pt[1]] for pt in path] for path in geom["paths"] if len(path) >= 2]
        if not paths:
            return None
        if len(paths) == 1:
            return {"type": "LineString", "coordinates": paths[0]}
        return {"type": "MultiLineString", "coordinates": paths}
    if "rings" in geom:
        rings = [[[pt[0], pt[1]] for pt in ring] for ring in geom["rings"] if len(ring) >= 4]
        if not rings:
            return None
        if len(rings) == 1:
            return {"type": "Polygon", "coordinates": rings}
        return {"type": "MultiPolygon", "coordinates": [[ring] for ring in rings]}
    return None


def query_page(url: str, where: str, offset: int, fields: str, use_bbox: bool) -> dict:
    params = {
        "where": where,
        "outFields": fields,
        "returnGeometry": "true",
        "outSR": "4326",
        "resultOffset": offset,
        "resultRecordCount": PAGE,
        "f": "json",
    }
    if use_bbox:
        params.update(
            {
                "geometry": json.dumps(BBOX),
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    return get_json(url + "/query?" + urllib.parse.urlencode(params))


def download_layer(name: str, url: str, mode: str, keep_fields: list[str] | None) -> dict:
    where = RAFAH_WHERE if mode == "rafah_mohafaza" else "1=1"
    use_bbox = mode == "bbox"
    fields = ",".join(keep_fields) if keep_fields else "*"

    count_params = {"where": where, "returnCountOnly": "true", "f": "json"}
    if use_bbox:
        count_params.update(
            {
                "geometry": json.dumps(BBOX),
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    try:
        count = get_json(url + "/query?" + urllib.parse.urlencode(count_params)).get("count", 0)
    except Exception as exc:  # noqa: BLE001
        print(f"  SKIP {name}: count failed ({exc})")
        return {"type": "FeatureCollection", "features": []}

    print(f"  {name}: {count} features ({mode})")
    features: list[dict] = []
    offset = 0
    while offset < count or (count == 0 and offset == 0):
        page = query_page(url, where, offset, fields, use_bbox)
        batch = page.get("features") or []
        if not batch:
            break
        for item in batch:
            attrs = item.get("attributes") or {}
            geometry = esri_geom_to_geojson(item.get("geometry"))
            if not geometry:
                continue
            if keep_fields:
                props = {k: clean(attrs.get(k)) for k in keep_fields if clean(attrs.get(k)) is not None}
            else:
                props = {
                    k: clean(v)
                    for k, v in attrs.items()
                    if k not in {"Shape__Area", "Shape__Length", "OBJECTID", "FID", "GlobalID"}
                    and clean(v) is not None
                }
            # Normalize common name/damage keys for the web app
            for src, dst in [
                ("Narratives", "title"),
                ("Theme", "theme"),
                ("Description", "description"),
                ("Building_N", "name"),
                ("Name", "name"),
                ("name", "name"),
                ("Damage", "damage"),
                ("AllDamage", "damage"),
                ("Categories", "category"),
                ("Building_T", "building"),
                ("Location", "location"),
                ("Text_Sourc", "source_url"),
            ]:
                if src in attrs and clean(attrs.get(src)) is not None:
                    props.setdefault(dst, clean(attrs.get(src)))
            features.append({"type": "Feature", "geometry": geometry, "properties": props})
        offset += len(batch)
        print(f"    {min(offset, max(count, offset))} / {count or '?'}")
        if not page.get("exceededTransferLimit") and len(batch) < PAGE:
            break
        if count and offset >= count:
            break

    return {"type": "FeatureCollection", "features": features}


def damage_stats() -> dict:
    """Overall + Rafah cumulative damage counts from the building layer."""
    stats: dict = {"source_layer": BUILDINGS, "overall": {}, "rafah": {}}

    for label, where in [("overall", "1=1"), ("rafah", RAFAH_WHERE)]:
        total = get_json(
            BUILDINGS
            + "/query?"
            + urllib.parse.urlencode({"where": where, "returnCountOnly": "true", "f": "json"})
        )["count"]
        grouped = get_json(
            BUILDINGS
            + "/query?"
            + urllib.parse.urlencode(
                {
                    "where": where,
                    "outStatistics": json.dumps(
                        [
                            {
                                "statisticType": "count",
                                "onStatisticField": "OBJECTID",
                                "outStatisticFieldName": "cnt",
                            }
                        ]
                    ),
                    "groupByFieldsForStatistics": "AllDamage",
                    "f": "json",
                }
            )
        )
        by_damage = {
            (f["attributes"].get("AllDamage") or "Unknown"): f["attributes"]["cnt"]
            for f in grouped.get("features", [])
        }
        damaged = total - by_damage.get("No Damage", 0)
        stats[label] = {
            "total_buildings": total,
            "all_damaged": damaged,
            "all_damaged_pct": round(100 * damaged / total, 1) if total else 0,
            "by_damage": by_damage,
            "destroyed": by_damage.get("Destroyed", 0),
            "severe_or_heavy": by_damage.get("Severe Damage", 0),
            "moderate": by_damage.get("Moderate Damage", 0),
            "possible": by_damage.get("Possible Damage", 0),
            "no_damage": by_damage.get("No Damage", 0),
        }
        # percentages like the dashboard
        for key in ("destroyed", "severe_or_heavy", "moderate", "possible", "all_damaged"):
            stats[label][f"{key}_pct"] = (
                round(100 * stats[label][key] / total, 1) if total else 0
            )
    return stats


def main() -> None:
    print("Downloading AUB Urbicide layers…")
    index = {
        "experience": EXPERIENCE,
        "credit": "Tracking The Urbicide in Gaza — American University of Beirut (AUB) / ArcGIS Online",
        "bbox_rafah": BBOX,
        "layers": {},
        "views": {
            "basemap": [
                "agriculture",
                "greenhouses",
                "institutional_land",
                "coast",
                "camps",
                "cemetery_recreation",
                "neighborhoods",
                "institutions",
            ],
            "damage": [
                "agriculture_damage",
                "natural_damage",
                "institutional_damage",
                "greenhouse_damage",
                "road_damage",
                "damaged_buildings_pts",
                "institutional_building_damage",
                "buildings",
            ],
            "3d_map": ["buildings"],
            "people_and_place": ["people_and_place"],
            "heritage": [
                "heritage_sites_poly",
                "heritage_sites",
                "heritage_buildings",
                "heritage_buildings_poly",
            ],
        },
    }

    for name, (url, mode, keep) in LAYERS.items():
        print(f"\n[{name}]")
        try:
            collection = download_layer(name, url, mode, keep)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED {name}: {exc}")
            collection = {"type": "FeatureCollection", "features": []}
        path = OUT / f"{name}.geojson"
        path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
        index["layers"][name] = {
            "file": f"{name}.geojson",
            "count": len(collection["features"]),
            "bytes": path.stat().st_size,
            "url": url,
            "mode": mode,
        }
        print(f"  wrote {path.name} ({path.stat().st_size / 1_000_000:.2f} MB)")

    # Point buildings at existing urbicide download
    urbicide_buildings = ROOT / "data" / "urbicide" / "buildings.geojson"
    urbicide_meta = ROOT / "data" / "urbicide" / "meta.json"
    if urbicide_buildings.exists():
        count = json.loads(urbicide_meta.read_text()).get("counts", {}).get("buildings")
        if count is None:
            count = len(json.loads(urbicide_buildings.read_text()).get("features", []))
        index["layers"]["buildings"] = {
            "file": "../urbicide/buildings.geojson",
            "count": count,
            "bytes": urbicide_buildings.stat().st_size,
            "url": BUILDINGS,
            "mode": "rafah_mohafaza",
            "note": "Rafah building footprints + AllDamage (see data/urbicide/)",
        }

    print("\n[damage_stats]")
    stats = damage_stats()
    (OUT / "damage_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    index["damage_stats"] = "damage_stats.json"
    print(
        "  overall damaged:",
        stats["overall"]["all_damaged"],
        f"({stats['overall']['all_damaged_pct']}%) of",
        stats["overall"]["total_buildings"],
    )
    print(
        "  rafah damaged:",
        stats["rafah"]["all_damaged"],
        f"({stats['rafah']['all_damaged_pct']}%) of",
        stats["rafah"]["total_buildings"],
    )

    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(f"\nDone. Index: {OUT / 'index.json'}")


if __name__ == "__main__":
    main()
