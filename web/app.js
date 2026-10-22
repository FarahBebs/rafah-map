const CITY = { center: [34.254, 31.281], zoom: 15.5, pitch: 60, bearing: -28 };
const GOVERNORATE = { center: [34.272, 31.283], zoom: 12.15, pitch: 48, bearing: -12 };
const GAZA_PEOPLE = { center: [34.45, 31.45], zoom: 10.2, pitch: 45, bearing: -8 };

const map = new maplibregl.Map({
  container: "map",
  style: {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      satellite: {
        type: "raster",
        tiles: [
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        ],
        tileSize: 256,
        attribution: "Imagery © Esri",
        maxzoom: 19,
      },
      streets: {
        type: "raster",
        tiles: [
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        ],
        tileSize: 256,
        attribution: "Streets © Esri",
      },
      terrain: {
        type: "raster-dem",
        tiles: [`${location.origin}/terrain/{z}/{x}/{y}.png`],
        encoding: "terrarium",
        tileSize: 256,
        maxzoom: 15,
        attribution: "Elevation: AWS Terrain Tiles / Terrarium",
      },
    },
    layers: [
      { id: "satellite", type: "raster", source: "satellite" },
      {
        id: "streets",
        type: "raster",
        source: "streets",
        layout: { visibility: "none" },
      },
    ],
  },
  center: CITY.center,
  zoom: CITY.zoom,
  pitch: CITY.pitch,
  bearing: CITY.bearing,
  maxPitch: 75,
  attributionControl: true,
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-left");

const statusEl = document.getElementById("status");
const popupEl = document.getElementById("popup");
const dateInput = document.getElementById("rafah-date");
const imageryNote = document.getElementById("imagery-note");
const dataSourceSelect = document.getElementById("data-source");
const dataNote = document.getElementById("data-note");
const creditsEl = document.getElementById("credits");
const damagePanel = document.getElementById("damage-stats");
const MODIS_START = "2000-02-24";
const AUB_CREDIT =
  '<a href="https://experience.arcgis.com/experience/5c24d93ffc234d709efbbeb355d9496c/page/Page?views=3D-Map">Tracking The Urbicide in Gaza</a> (AUB)';

let heightScale = 1;
let releases = [];
let activeView = "osm";
let roadCount = 0;
let aubReady = false;
let damageStats = null;

const EMPTY = { type: "FeatureCollection", features: [] };

const OSM_BUILDING_COLOR = [
  "match",
  ["get", "building"],
  ["mosque", "place_of_worship"],
  "#efe2c4",
  ["school", "university", "hospital", "civic"],
  "#d7c3a2",
  ["apartments", "residential"],
  "#cbb59a",
  ["commercial", "retail", "office"],
  "#b7a48c",
  "#c4b39a",
];

const DAMAGE_BUILDING_COLOR = [
  "match",
  ["get", "damage"],
  "Destroyed",
  "#871014",
  ["Severe Damage", "Heavy Damage"],
  "#b5584c",
  "Moderate Damage",
  "#cf9582",
  "Possible Damage",
  "#d4b483",
  "No Damage",
  "#c4b39a",
  "#aaaaaa",
];

const PEOPLE_THEME_COLOR = [
  "match",
  ["get", "theme"],
  "Disruption of socio-spatial practices",
  "#245d7b",
  "Everyday Resistance",
  "#2f7d4a",
  ["Displacement", "Displacement "],
  "#c9a227",
  "#888888",
];

const VIEWS = {
  osm: {
    note: "Current OpenStreetMap footprints.",
    buildings: "osm",
    showBuildings: true,
    showAub: false,
    fly: CITY,
  },
  basemap: {
    note: "AUB basemap: agriculture, coast, camps, institutions.",
    buildings: "osm",
    showBuildings: true,
    showAub: true,
    aubGroups: ["basemap"],
    fly: GOVERNORATE,
  },
  damage: {
    note: "AUB damage overlays + Rafah building damage stats.",
    buildings: "urbicide",
    showBuildings: true,
    showAub: true,
    aubGroups: ["damage"],
    showStats: true,
    fly: GOVERNORATE,
  },
  "3d-map": {
    note: "AUB 3D map: Rafah buildings colored by cumulative damage.",
    buildings: "urbicide",
    showBuildings: true,
    showAub: false,
    showStats: true,
    fly: CITY,
  },
  people: {
    note: "People & Place narratives across Gaza (AUB).",
    buildings: "osm",
    showBuildings: false,
    showAub: true,
    aubGroups: ["people"],
    fly: GAZA_PEOPLE,
  },
  heritage: {
    note: "Heritage sites and buildings across Gaza (AUB).",
    buildings: "osm",
    showBuildings: false,
    showAub: true,
    aubGroups: ["heritage"],
    fly: GAZA_PEOPLE,
  },
};

const AUB_SOURCES = {
  agriculture: { file: "/data/aub/agriculture.geojson", type: "fill", group: "basemap", color: "#6f8f4e", opacity: 0.45 },
  greenhouses: { file: "/data/aub/greenhouses.geojson", type: "fill", group: "basemap", color: "#9bbb6e", opacity: 0.5 },
  institutional_land: {
    file: "/data/aub/institutional_land.geojson",
    type: "fill",
    group: "basemap",
    color: "#7a9e8e",
    opacity: 0.4,
  },
  coast: { file: "/data/aub/coast.geojson", type: "fill", group: "basemap", color: "#6a8ea8", opacity: 0.35 },
  cemetery_recreation: {
    file: "/data/aub/cemetery_recreation.geojson",
    type: "fill",
    group: "basemap",
    color: "#8a7a6a",
    opacity: 0.4,
  },
  neighborhoods: {
    file: "/data/aub/neighborhoods.geojson",
    type: "line",
    group: "basemap",
    color: "rgba(244,239,230,0.35)",
    width: 1,
  },
  camps: { file: "/data/aub/camps.geojson", type: "circle", group: "basemap", color: "#e3b15a", radius: 5 },
  institutions: {
    file: "/data/aub/institutions.geojson",
    type: "circle",
    group: "basemap",
    color: "#d7c3a2",
    radius: 3.5,
  },
  agriculture_damage: {
    file: "/data/aub/agriculture_damage.geojson",
    type: "fill",
    group: "damage",
    color: "#8b3a2a",
    opacity: 0.45,
  },
  natural_damage: {
    file: "/data/aub/natural_damage.geojson",
    type: "fill",
    group: "damage",
    color: "#6b2f24",
    opacity: 0.4,
  },
  institutional_damage: {
    file: "/data/aub/institutional_damage.geojson",
    type: "fill",
    group: "damage",
    color: "#a05040",
    opacity: 0.4,
  },
  greenhouse_damage: {
    file: "/data/aub/greenhouse_damage.geojson",
    type: "fill",
    group: "damage",
    color: "#b06040",
    opacity: 0.45,
  },
  road_damage: {
    file: "/data/aub/road_damage.geojson",
    type: "line",
    group: "damage",
    color: "#c45c48",
    width: 2.2,
  },
  damaged_buildings_pts: {
    file: "/data/aub/damaged_buildings_pts.geojson",
    type: "circle",
    group: "damage",
    color: "#871014",
    radius: 2.5,
  },
  institutional_building_damage: {
    file: "/data/aub/institutional_building_damage.geojson",
    type: "circle",
    group: "damage",
    color: DAMAGE_BUILDING_COLOR,
    radius: 3.5,
  },
  people_and_place: {
    file: "/data/aub/people_and_place.geojson",
    type: "circle",
    group: "people",
    color: PEOPLE_THEME_COLOR,
    radius: 7,
  },
  heritage_sites_poly: {
    file: "/data/aub/heritage_sites_poly.geojson",
    type: "fill",
    group: "heritage",
    color: "#8b6b3d",
    opacity: 0.35,
  },
  heritage_buildings_poly: {
    file: "/data/aub/heritage_buildings_poly.geojson",
    type: "fill",
    group: "heritage",
    color: "#b0894f",
    opacity: 0.5,
  },
  heritage_sites: {
    file: "/data/aub/heritage_sites.geojson",
    type: "circle",
    group: "heritage",
    color: "#d4a85a",
    radius: 6,
  },
  heritage_buildings: {
    file: "/data/aub/heritage_buildings.geojson",
    type: "circle",
    group: "heritage",
    color: "#e3c07a",
    radius: 5,
  },
};

const buildingCache = {};
const aubCache = {};

const releasesReady = fetch(
  "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json",
)
  .then((response) => response.json())
  .then((data) => {
    releases = Object.entries(data)
      .map(([id, item]) => {
        const match = String(item.itemTitle || "").match(/(\d{4}-\d{2}-\d{2})/);
        return match ? { id, date: match[1] } : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.date.localeCompare(b.date));
  })
  .catch((error) => {
    console.error(error);
    imageryNote.textContent = "Historical photos could not be loaded.";
  });

function formatDate(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day)).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function replaceSatellite(tiles, maxzoom) {
  if (!map.getSource("satellite")) return;
  const visible = map.getLayoutProperty("satellite", "visibility") || "visible";
  map.removeLayer("satellite");
  map.removeSource("satellite");
  map.addSource("satellite", {
    type: "raster",
    tiles,
    tileSize: 256,
    maxzoom,
    attribution: "Imagery © Esri, NASA",
  });
  const before = map.getLayer("streets") ? "streets" : undefined;
  map.addLayer(
    { id: "satellite", type: "raster", source: "satellite", layout: { visibility: visible } },
    before,
  );
}

function applyImageryDate(iso) {
  if (!releases.length) return;
  const firstDetailed = releases[0];
  const latest = releases[releases.length - 1];
  if (iso < firstDetailed.date) {
    const day = iso < MODIS_START ? MODIS_START : iso;
    replaceSatellite(
      [
        `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${day}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`,
      ],
      9,
    );
    imageryNote.textContent =
      iso < MODIS_START
        ? `First photo is ${formatDate(MODIS_START)}.`
        : `Wide view ${formatDate(day)}. Close photos start ${formatDate(firstDetailed.date)}.`;
    setLayerVisibility("buildings-3d", false);
    setLayerVisibility("roads-line", false);
    if (map.getZoom() > 10) map.easeTo({ center: CITY.center, zoom: 9, pitch: 40, bearing: 0, duration: 800 });
    return;
  }
  let chosen = firstDetailed;
  for (const release of releases) {
    if (release.date <= iso) chosen = release;
    else break;
  }
  replaceSatellite(
    [
      `https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/${chosen.id}/{z}/{y}/{x}`,
    ],
    19,
  );
  imageryNote.textContent =
    chosen.date === latest.date && iso >= latest.date
      ? `Latest photo ${formatDate(chosen.date)}.`
      : `Photo ${formatDate(chosen.date)}.`;
  const view = VIEWS[activeView];
  setLayerVisibility("buildings-3d", view.showBuildings && document.getElementById("layer-buildings").checked);
  setLayerVisibility("roads-line", document.getElementById("layer-roads").checked);
  if (map.getZoom() < 12 && activeView !== "people") map.easeTo({ ...CITY, duration: 800 });
}

function visibility(on) {
  return on ? "visible" : "none";
}

function setLayerVisibility(id, on) {
  if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visibility(on));
}

function applyTerrain(on) {
  const scale = Number(document.getElementById("terrain-scale").value);
  if (on) map.setTerrain({ source: "terrain", exaggeration: scale });
  else map.setTerrain(null);
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} ${response.status}`);
  return response.json();
}

async function loadBuildings(kind) {
  if (buildingCache[kind]) return buildingCache[kind];
  if (kind === "urbicide") {
    const [meta, buildings] = await Promise.all([
      loadJson("/data/urbicide/meta.json"),
      loadJson("/data/urbicide/buildings.geojson"),
    ]);
    buildingCache[kind] = { meta, buildings };
  } else {
    const [meta, buildings] = await Promise.all([
      loadJson("/data/rafah/meta.json"),
      loadJson("/data/rafah/buildings.geojson"),
    ]);
    buildingCache[kind] = { meta, buildings };
  }
  return buildingCache[kind];
}

async function loadAubLayer(key) {
  if (aubCache[key]) return aubCache[key];
  const conf = AUB_SOURCES[key];
  try {
    aubCache[key] = await loadJson(conf.file);
  } catch (error) {
    console.warn("Missing AUB layer", key, error);
    aubCache[key] = EMPTY;
  }
  return aubCache[key];
}

function ensureAubLayers() {
  if (aubReady) return;
  const before = map.getLayer("roads-line") ? "roads-line" : undefined;
  for (const [key, conf] of Object.entries(AUB_SOURCES)) {
    const sourceId = `aub-${key}`;
    const layerId = `aub-${key}`;
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, { type: "geojson", data: EMPTY });
    }
    if (map.getLayer(layerId)) continue;
    if (conf.type === "fill") {
      map.addLayer(
        {
          id: layerId,
          type: "fill",
          source: sourceId,
          layout: { visibility: "none" },
          paint: {
            "fill-color": conf.color,
            "fill-opacity": conf.opacity ?? 0.4,
            "fill-outline-color": "rgba(244,239,230,0.2)",
          },
        },
        before,
      );
    } else if (conf.type === "line") {
      map.addLayer(
        {
          id: layerId,
          type: "line",
          source: sourceId,
          layout: { visibility: "none" },
          paint: {
            "line-color": conf.color,
            "line-width": conf.width ?? 1.5,
            "line-opacity": 0.85,
          },
        },
        before,
      );
    } else {
      map.addLayer(
        {
          id: layerId,
          type: "circle",
          source: sourceId,
          layout: { visibility: "none" },
          paint: {
            "circle-color": conf.color,
            "circle-radius": conf.radius ?? 5,
            "circle-stroke-color": "#1c1814",
            "circle-stroke-width": 1,
            "circle-opacity": 0.92,
          },
        },
        map.getLayer("buildings-3d") ? "buildings-3d" : undefined,
      );
    }
  }
  aubReady = true;
}

async function hydrateAubGroup(group) {
  const keys = Object.entries(AUB_SOURCES)
    .filter(([, conf]) => conf.group === group)
    .map(([key]) => key);
  await Promise.all(
    keys.map(async (key) => {
      const data = await loadAubLayer(key);
      if (map.getSource(`aub-${key}`)) map.getSource(`aub-${key}`).setData(data);
    }),
  );
}

function setAubVisibility(activeGroups) {
  for (const [key, conf] of Object.entries(AUB_SOURCES)) {
    const on = activeGroups.includes(conf.group);
    setLayerVisibility(`aub-${key}`, on);
  }
}

function renderDamageStats() {
  if (!damagePanel) return;
  if (!damageStats || !VIEWS[activeView].showStats) {
    damagePanel.hidden = true;
    return;
  }
  const rafah = damageStats.rafah || {};
  const overall = damageStats.overall || {};
  const rows = [
    ["All damaged", rafah.all_damaged, rafah.all_damaged_pct],
    ["Destroyed", rafah.destroyed, rafah.destroyed_pct],
    ["Severe / heavy", rafah.severe_or_heavy, rafah.severe_or_heavy_pct],
    ["Moderate", rafah.moderate, rafah.moderate_pct],
    ["Possible", rafah.possible, rafah.possible_pct],
  ];
  damagePanel.hidden = false;
  damagePanel.innerHTML = `
    <p class="stats-title">Rafah building damage</p>
    <ul>
      ${rows
        .map(
          ([label, count, pct]) =>
            `<li><span>${escapeHtml(label)}</span><strong>${Number(count || 0).toLocaleString()} (${Number(
              pct || 0,
            )}%)</strong></li>`,
        )
        .join("")}
    </ul>
    <p class="stats-foot">Gaza overall: ${Number(overall.all_damaged || 0).toLocaleString()} damaged of ${Number(
      overall.total_buildings || 0,
    ).toLocaleString()} (${Number(overall.all_damaged_pct || 0)}%).</p>
  `;
}

function updateStatusForView(meta, buildings) {
  const view = VIEWS[activeView];
  if (view.showStats && damageStats?.rafah) {
    const r = damageStats.rafah;
    statusEl.textContent = `${Number(r.total_buildings || 0).toLocaleString()} buildings · ${Number(
      r.all_damaged || 0,
    ).toLocaleString()} damaged (${r.all_damaged_pct}%)`;
    return;
  }
  if (activeView === "people") {
    const n = aubCache.people_and_place?.features?.length;
    statusEl.textContent = n ? `${n.toLocaleString()} people & place stories` : "People & Place";
    return;
  }
  if (activeView === "heritage") {
    const sites = aubCache.heritage_sites?.features?.length || 0;
    const bldgs = aubCache.heritage_buildings?.features?.length || 0;
    statusEl.textContent = `${(sites + bldgs).toLocaleString()} heritage sites & buildings`;
    return;
  }
  if (activeView === "basemap") {
    statusEl.textContent = "AUB basemap layers · Rafah area";
    return;
  }
  const buildingCount = meta?.counts?.buildings ?? buildings?.features?.length ?? 0;
  statusEl.textContent = `${buildingCount.toLocaleString()} buildings · ${roadCount.toLocaleString()} roads`;
}

function creditsFor(viewKey) {
  if (viewKey === "osm") {
    return `Buildings, roads, and boundary from
      <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>.
      Elevation from AWS Terrain Tiles (Terrarium).
      Extra views come from ${AUB_CREDIT}.
      The date changes the satellite photo.`;
  }
  return `View data from ${AUB_CREDIT}.
    Roads/boundary fallback from
    <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>.
    Elevation from AWS Terrain Tiles (Terrarium).`;
}

async function switchView(viewKey) {
  activeView = viewKey;
  const view = VIEWS[viewKey];
  dataNote.textContent = view.note;
  creditsEl.innerHTML = creditsFor(viewKey);
  ensureAubLayers();

  statusEl.textContent = "Loading view…";
  try {
    const { meta, buildings } = await loadBuildings(view.buildings);
    if (map.getSource("buildings")) map.getSource("buildings").setData(buildings);
    if (map.getLayer("buildings-3d")) {
      map.setPaintProperty(
        "buildings-3d",
        "fill-extrusion-color",
        view.buildings === "urbicide" ? DAMAGE_BUILDING_COLOR : OSM_BUILDING_COLOR,
      );
      setLayerVisibility(
        "buildings-3d",
        view.showBuildings && document.getElementById("layer-buildings").checked,
      );
    }

    const groups = view.aubGroups || [];
    if (view.showAub && groups.length) {
      await Promise.all(groups.map((group) => hydrateAubGroup(group)));
      setAubVisibility(groups);
    } else {
      setAubVisibility([]);
    }

    if (view.showStats && !damageStats) {
      try {
        damageStats = await loadJson("/data/aub/damage_stats.json");
      } catch (error) {
        console.warn(error);
      }
    }
    renderDamageStats();
    updateStatusForView(meta, buildings);
    if (view.fly) map.easeTo({ ...view.fly, duration: 1100 });
  } catch (error) {
    statusEl.textContent = "Could not load that view. Is the AUB data downloaded?";
    console.error(error);
  }
}

function propText(value) {
  if (value == null) return "";
  const text = String(value).trim();
  if (!text || text.toLowerCase() === "null" || text.toLowerCase() === "undefined") return "";
  return text;
}

function looksLikeId(value) {
  const text = propText(value);
  if (!text) return true;
  // Numeric / coded IDs are not useful titles
  return /^[A-Z]?\d{4,}([_-]?\d+)*$/i.test(text);
}

function firstUseful(...values) {
  for (const value of values) {
    const text = propText(value);
    if (!text || looksLikeId(text)) continue;
    if (text.toLowerCase() === "yes" || text.toLowerCase() === "no") continue;
    return text;
  }
  return "";
}

function layerLabel(layerId) {
  const labels = {
    "buildings-3d": "Building",
    "aub-agriculture": "Agricultural land",
    "aub-greenhouses": "Greenhouse",
    "aub-greenhouse_damage": "Damaged greenhouse",
    "aub-institutional_land": "Institutional land",
    "aub-institutional_damage": "Damaged institutional land",
    "aub-institutional_building_damage": "Institutional building",
    "aub-road_damage": "Damaged road",
    "aub-natural_damage": "Natural land damage",
    "aub-damaged_buildings_pts": "Damaged building",
    "aub-heritage_sites": "Heritage site",
    "aub-heritage_sites_poly": "Heritage site",
    "aub-heritage_buildings": "Heritage building",
    "aub-heritage_buildings_poly": "Heritage building",
    "aub-coast": "Coast",
    "aub-cemetery_recreation": "Cemetery / recreation",
    "aub-neighborhoods": "Neighborhood",
    "aub-institutions": "Institution",
    "aub-camps": "Camp",
    "aub-people_and_place": "People & Place",
  };
  return labels[layerId] || "Feature";
}

function propsTitle(props, layerId) {
  const named = firstUseful(
    props.title,
    props.Narratives,
    props.NameEn,
    props.name_en,
    props.Building_N,
    props.BuildingNa,
    props.Name,
    props.name,
    props.name_ar,
    props.NameAr,
  );
  if (named) return named;

  const kind = firstUseful(
    props.building,
    props.Building_T,
    props.BuildingType,
    props.Building_Type,
    props.fclass,
    props.RoadType,
    props.Typology,
    props.category,
    props.Category,
    props.Categories,
    props.Period,
  );
  const damage = firstUseful(props.damage, props.Damage, props.AllDamage);
  const place = firstUseful(props.Mohafaza, props.Mohafaz, props.Moh_name, props.MohName, props.Governorate, props.Sub_Urban, props.SubUrban);

  if (kind && damage) return `${kind} · ${damage}`;
  if (kind) return kind;
  if (damage) return `${layerLabel(layerId)} · ${damage}`;
  if (place) return `${layerLabel(layerId)} · ${place}`;
  return layerLabel(layerId);
}

function showFeaturePopup(feature, layerId) {
  const props = feature.properties || {};
  const title = propsTitle(props, layerId);
  const parts = [];

  const kind = firstUseful(
    props.building,
    props.Building_T,
    props.BuildingType,
    props.fclass,
    props.RoadType,
    props.Typology,
    props.amenity,
  );
  const category = firstUseful(props.category, props.Category, props.Categories);
  const damage = firstUseful(
    props.damage,
    props.Damage,
    props.AllDamage,
    props.Damage_07Jan2024,
    props.Damage_30_01_2024,
    props.UNOSAT_Damage,
  );
  const place = firstUseful(
    props.location,
    props.Location,
    props.Mohafaza,
    props.Mohafaz,
    props.Governorate,
    props.Sub_Urban,
    props.SubUrban,
    props.name_ar,
    props.NameAr,
  );
  const period = firstUseful(props.Period);
  const theme = firstUseful(props.theme, props.Theme);

  if (layerId === "buildings-3d") {
    const buildingKind = kind && kind !== "yes" ? kind : "building";
    parts.push(`${escapeHtml(buildingKind)} · ${Number(props.height_m || 0).toFixed(0)} m`);
  } else if (kind && kind.toLowerCase() !== title.toLowerCase()) {
    parts.push(escapeHtml(kind));
  }
  if (category && category.toLowerCase() !== title.toLowerCase()) parts.push(escapeHtml(category));
  if (theme) parts.push(escapeHtml(theme));
  if (damage) parts.push(escapeHtml(damage));
  if (period) parts.push(escapeHtml(period));
  if (place) parts.push(escapeHtml(place));
  if (props.Length_m) parts.push(`${Number(props.Length_m).toFixed(0)} m`);
  if (props.Area && !Number.isNaN(Number(props.Area))) {
    /* keep quiet — area units vary */
  }

  let body = parts.length ? `<p>${parts.join(" · ")}</p>` : "";
  const description = propText(props.description) || propText(props.Description) || propText(props.Comments);
  if (description) {
    const text = description.slice(0, 420);
    body += `<p class="popup-body">${escapeHtml(text)}${description.length > 420 ? "…" : ""}</p>`;
  }
  const source = propText(props.source_url) || propText(props.Text_Sourc) || propText(props.Source);
  if (source && /^https?:\/\//i.test(source)) {
    body += `<p><a href="${escapeHtml(source)}" target="_blank" rel="noopener">Source</a></p>`;
  }
  popupEl.hidden = false;
  popupEl.innerHTML = `<h2>${escapeHtml(title)}</h2>${body}`;
}

function bindPopupLayer(layerId) {
  map.on("click", layerId, (event) => {
    const feature = event.features && event.features[0];
    if (feature) showFeaturePopup(feature, layerId);
  });
  map.on("mouseenter", layerId, () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", layerId, () => {
    map.getCanvas().style.cursor = "";
  });
}

map.on("load", async () => {
  try {
    const [dataset, roads, boundary] = await Promise.all([
      loadBuildings("osm"),
      loadJson("/data/rafah/roads.geojson"),
      loadJson("/data/rafah/boundary.geojson"),
    ]);

    roadCount = dataset.meta.counts?.roads ?? roads.features.length;

    map.addSource("boundary", { type: "geojson", data: boundary });
    map.addSource("roads", { type: "geojson", data: roads });
    map.addSource("buildings", { type: "geojson", data: dataset.buildings });

    map.addLayer({
      id: "boundary-line",
      type: "line",
      source: "boundary",
      paint: {
        "line-color": "#e3b15a",
        "line-width": 2.2,
        "line-dasharray": [1.4, 1.1],
      },
    });

    map.addLayer({
      id: "roads-line",
      type: "line",
      source: "roads",
      paint: {
        "line-color": [
          "match",
          ["get", "highway"],
          ["motorway", "trunk", "primary"],
          "#f2e2c4",
          ["secondary", "tertiary"],
          "#d7c4a4",
          "rgba(255,255,255,0.45)",
        ],
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          11,
          ["match", ["get", "highway"], ["motorway", "trunk", "primary"], 1.2, 0.3],
          15,
          ["match", ["get", "highway"], ["motorway", "trunk", "primary"], 3.4, ["secondary", "tertiary"], 2.2, 0.8],
        ],
      },
    });

    map.addLayer({
      id: "buildings-3d",
      type: "fill-extrusion",
      source: "buildings",
      paint: {
        "fill-extrusion-color": OSM_BUILDING_COLOR,
        "fill-extrusion-height": ["*", ["get", "height_m"], heightScale],
        "fill-extrusion-base": 0,
        "fill-extrusion-opacity": 0.92,
      },
    });

    ensureAubLayers();
    applyTerrain(true);
    updateStatusForView(dataset.meta, dataset.buildings);
    creditsEl.innerHTML = creditsFor("osm");

    bindPopupLayer("buildings-3d");
    for (const key of Object.keys(AUB_SOURCES)) bindPopupLayer(`aub-${key}`);

    try {
      damageStats = await loadJson("/data/aub/damage_stats.json");
    } catch (_) {
      /* optional until download finishes */
    }

    await releasesReady;
    applyImageryDate(dateInput.value);
  } catch (error) {
    statusEl.textContent = "Map data is still downloading. Refresh in a moment.";
    console.error(error);
  }
});

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

document.getElementById("layer-satellite").addEventListener("change", (event) => {
  setLayerVisibility("satellite", event.target.checked);
});
document.getElementById("layer-streets").addEventListener("change", (event) => {
  setLayerVisibility("streets", event.target.checked);
});
document.getElementById("layer-buildings").addEventListener("change", (event) => {
  setLayerVisibility("buildings-3d", event.target.checked && VIEWS[activeView].showBuildings);
});
document.getElementById("layer-roads").addEventListener("change", (event) => {
  setLayerVisibility("roads-line", event.target.checked);
});
document.getElementById("layer-boundary").addEventListener("change", (event) => {
  setLayerVisibility("boundary-line", event.target.checked);
});
document.getElementById("layer-terrain").addEventListener("change", (event) => {
  applyTerrain(event.target.checked);
});

document.getElementById("terrain-scale").addEventListener("input", (event) => {
  document.getElementById("terrain-out").textContent = Number(event.target.value).toFixed(1);
  if (document.getElementById("layer-terrain").checked) applyTerrain(true);
});

document.getElementById("height-scale").addEventListener("input", (event) => {
  heightScale = Number(event.target.value);
  document.getElementById("height-out").textContent = heightScale.toFixed(1);
  if (map.getLayer("buildings-3d")) {
    map.setPaintProperty("buildings-3d", "fill-extrusion-height", ["*", ["get", "height_m"], heightScale]);
  }
});

dateInput.addEventListener("change", () => applyImageryDate(dateInput.value));

dataSourceSelect.addEventListener("change", (event) => {
  switchView(event.target.value);
});

document.getElementById("view-city").addEventListener("click", () => map.easeTo({ ...CITY, duration: 1200 }));
document.getElementById("view-gov").addEventListener("click", () => map.easeTo({ ...GOVERNORATE, duration: 1200 }));
document.getElementById("tilt").addEventListener("click", () => {
  const pitched = map.getPitch() < 40;
  map.easeTo({ pitch: pitched ? 64 : 0, duration: 800 });
});
