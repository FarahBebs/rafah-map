const CITY = { center: [34.254, 31.281], zoom: 15.5, pitch: 60, bearing: -28 };
const GOVERNORATE = { center: [34.272, 31.283], zoom: 12.15, pitch: 48, bearing: -12 };

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
          "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
          "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        ],
        tileSize: 256,
        attribution: "© OpenStreetMap, © CARTO",
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
let heightScale = 1;

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

map.on("load", async () => {
  try {
    const [meta, buildings, roads, boundary] = await Promise.all([
      loadJson("/data/rafah/meta.json"),
      loadJson("/data/rafah/buildings.geojson"),
      loadJson("/data/rafah/roads.geojson"),
      loadJson("/data/rafah/boundary.geojson"),
    ]);

    map.addSource("boundary", { type: "geojson", data: boundary });
    map.addSource("roads", { type: "geojson", data: roads });
    map.addSource("buildings", { type: "geojson", data: buildings });

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
        "fill-extrusion-color": [
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
        ],
        "fill-extrusion-height": ["*", ["get", "height_m"], heightScale],
        "fill-extrusion-base": 0,
        "fill-extrusion-opacity": 0.92,
      },
    });

    applyTerrain(true);

    const buildingCount = meta.counts?.buildings ?? buildings.features.length;
    const roadCount = meta.counts?.roads ?? roads.features.length;
    statusEl.textContent = `${buildingCount.toLocaleString()} buildings · ${roadCount.toLocaleString()} roads`;

    map.on("click", "buildings-3d", (event) => {
      const feature = event.features && event.features[0];
      if (!feature) return;
      const props = feature.properties || {};
      const name = props.name_ar || props.name || "Unnamed building";
      const kind = props.building && props.building !== "yes" ? props.building : "building";
      popupEl.hidden = false;
      popupEl.innerHTML = `<h2>${escapeHtml(name)}</h2><p>${escapeHtml(kind)} · ${Number(props.height_m || 0).toFixed(0)} m${
        props.amenity ? ` · ${escapeHtml(props.amenity)}` : ""
      }</p>`;
    });

    map.on("mouseenter", "buildings-3d", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "buildings-3d", () => {
      map.getCanvas().style.cursor = "";
    });
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
  setLayerVisibility("buildings-3d", event.target.checked);
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

document.getElementById("view-city").addEventListener("click", () => map.easeTo({ ...CITY, duration: 1200 }));
document.getElementById("view-gov").addEventListener("click", () => map.easeTo({ ...GOVERNORATE, duration: 1200 }));
document.getElementById("tilt").addEventListener("click", () => {
  const pitched = map.getPitch() < 40;
  map.easeTo({ pitch: pitched ? 64 : 0, duration: 800 });
});
