# Web maps

Library URLs checked on 2026-10-11 (maplibre-gl 5.6.0, pmtiles 4.3.0, leaflet 1.9.4 on unpkg). Pin an exact version.

## Rules

- Web maps draw in Web Mercator (EPSG:3857). Send data as GeoJSON in EPSG:4326 (longitude, latitude order); reproject first (`ogr2ogr -t_srs EPSG:4326 out.geojson in.gpkg`).
- Keep inline GeoJSON small (a few MB). Larger data: vector tiles, ideally one PMTiles file on static hosting that supports HTTP range requests.
- Always show attribution for every source (`© OpenStreetMap contributors` for OSM tiles and data). Do not hide the attribution control.
- Do not use a third-party basemap whose terms you have not checked. OpenStreetMap's own tile servers are not for heavy production use (tile usage policy: operations.osmfoundation.org/policies/tiles).
- Check the page in a browser: features in the right place, legend matches, no console errors.

## MapLibre GL JS: GeoJSON choropleth

```html
<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<link href="https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js"></script>
<style>html,body,#map{margin:0;height:100%}</style></head>
<body><div id="map"></div><script>
const map = new maplibregl.Map({
  container: "map",
  style: "https://demotiles.maplibre.org/style.json",
  center: [2.35, 46.5], zoom: 5
});
map.addControl(new maplibregl.NavigationControl());
map.addControl(new maplibregl.ScaleControl({unit: "metric"}));
map.on("load", () => {
  map.addSource("zones", {type: "geojson", data: "zones.geojson",
    attribution: "Source: your data provider, 2024"});
  map.addLayer({id: "zones-fill", type: "fill", source: "zones", paint: {
    "fill-color": ["step", ["get", "density"],
      "#ffffb2", 50, "#fecc5c", 100, "#fd8d3c", 250, "#f03b20", 500, "#bd0026"],
    "fill-opacity": 0.8 }});
  map.addLayer({id: "zones-line", type: "line", source: "zones",
    paint: {"line-color": "#ffffff", "line-width": 0.5}});
});
</script></body></html>
```

The `step` breaks are the class breaks computed in QGIS or Python; MapLibre does not classify. Attribution passed on a source appears in the default attribution control.

## MapLibre GL JS: PMTiles vector tiles

Make the file: `ogr2ogr -f PMTiles zones.pmtiles zones.gpkg -dsco MAXZOOM=12` (GDAL 3.8 or later) or `tippecanoe -o zones.pmtiles zones.geojson`.

```html
<script src="https://unpkg.com/pmtiles@4.3.0/dist/pmtiles.js"></script>
<script>
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);
// then, in map.on("load"):
map.addSource("zones", {type: "vector", url: "pmtiles://https://example.com/zones.pmtiles",
  attribution: "Source: your data provider"});
map.addLayer({id: "zones", type: "fill", source: "zones", "source-layer": "zones",
  paint: {"fill-color": "#3182bd", "fill-opacity": 0.6}});
</script>
```

`source-layer` is the layer name inside the tiles (with ogr2ogr, the input layer name). Check it with `ogrinfo zones.pmtiles`.

## Leaflet: GeoJSON with OSM tiles

```html
<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{margin:0;height:100%}</style></head>
<body><div id="map"></div><script>
const map = L.map("map").setView([46.5, 2.35], 6);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);
L.control.scale({imperial: false}).addTo(map);
const color = d => d > 500 ? "#bd0026" : d > 250 ? "#f03b20" : d > 100 ? "#fd8d3c" : d > 50 ? "#fecc5c" : "#ffffb2";
fetch("zones.geojson").then(r => r.json()).then(data => {
  L.geoJSON(data, {
    style: f => ({fillColor: color(f.properties.density), fillOpacity: 0.8, color: "#fff", weight: 0.5}),
    onEachFeature: (f, layer) => layer.bindPopup(`${f.properties.name}: ${f.properties.density}`)
  }).addTo(map);
});
</script></body></html>
```

Leaflet suits raster tiles and small GeoJSON; for many features or vector tiles, use MapLibre.

## Serving locally

`fetch` of a local file fails from `file://`. Serve the folder: `python3 -m http.server 8000`, then open http://localhost:8000. Stop the server after checking.
