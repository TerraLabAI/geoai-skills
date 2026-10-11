---
name: open-imagery-finder
description: Chooses open satellite imagery, aerial orthophotos and elevation data for a place and a date (Sentinel-2, Landsat 8 and 9, Sentinel-1 SAR, Copernicus DEM GLO-30 and GLO-90, NAIP, national orthophotos such as IGN BD ORTHO, ESA WorldCover) by resolution, revisit, coverage and license, then finds scenes through STAC (Earth Search, Microsoft Planetary Computer) with a cloud cover filter and loads them in QGIS as COG, XYZ or WMS. Use when the user asks where to download satellite images, which imagery or DEM to use, how to get a cloud-free Sentinel-2 or Landsat scene, how to search a STAC catalog with pystac-client, or how to open a COG or an orthophoto in QGIS.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
---

# Open imagery and elevation finder

## What goes wrong without this skill

- Recommending a basemap (Google, Bing, Esri World Imagery) for analysis. Their terms forbid most analysis and derivative data, and you do not know the capture date. Use sources with a stated open license.
- Picking Sentinel-2 for objects smaller than about 20 to 30 m (single trees, cars, small buildings). Ten-meter pixels cannot resolve them. Use an orthophoto.
- Downloading whole scenes when a STAC search plus a windowed COG read would fetch only the area of interest.
- Forgetting cloud cover, or trusting scene-level cloud cover for a small area. A 5 % cloudy tile can be fully cloudy over your field.
- Mixing Landsat Collection 2 Level-2 DN with reflectance: scale factor 0.0000275, offset -0.2.

## Step 1: pick the source

| Source | Resolution | Revisit | Coverage | Since | License |
| --- | --- | --- | --- | --- | --- |
| Sentinel-2 L2A (optical, 13 bands) | 10, 20, 60 m | 5 days (2 satellites) | Land, 56 S to 83 N | 2015 (Collection-1 L2A on CDSE and Earth Search c1; operational global L2A from December 2018) | Copernicus open data |
| Landsat 8 and 9 Collection 2 L2 | 30 m (thermal 100 m resampled to 30; 15 m pan only in Level-1) | 16 days each, 8 days combined | Global land | 2013 (L8), 2021 (L9) | US public domain |
| Sentinel-1 GRD or RTC (C-band SAR) | 10 m (IW mode) | 12 days per satellite | Global, sees through cloud and at night | 2014 | Copernicus open data |
| Copernicus DEM GLO-30 / GLO-90 | 30 m / 90 m | Static (surface model, includes buildings and trees) | Global | 2019 release | Copernicus DEM license, open with attribution |
| ESA WorldCover | 10 m land cover, 11 classes | 2020 and 2021 maps | Global | 2020 | CC BY 4.0 |
| NAIP (US) | 0.6 m to 1 m, RGB + NIR | Every 2 to 3 years per state | Contiguous US | 2003 | US public domain |
| IGN BD ORTHO (France) | 20 cm | Periodic campaigns per department | France | 2000s | Licence Ouverte Etalab 2.0 |

Verified on 2026-10-11 against the Copernicus, USGS, ESA WorldCover, USDA NAIP and IGN dataset pages.

Rules of thumb:
- Vegetation, water, land change, burn scars: Sentinel-2, Landsat for history before 2015.
- Cloudy regions, floods, ships, deformation: Sentinel-1.
- Terrain, slope, watershed: Copernicus DEM GLO-30. Heights are in EGM2008. It is a surface model, not bare earth.
- Buildings, trees, parcels: national orthophotos (IGN in France, NAIP in the US, national mapping agencies elsewhere).

## Step 2: find scenes with STAC

Public catalogs (no account needed to search):

| Catalog | URL | Useful collections |
| --- | --- | --- |
| Earth Search (Element 84, AWS) | https://earth-search.aws.element84.com/v1 | `sentinel-2-c1-l2a`, `sentinel-2-l2a`, `landsat-c2-l2`, `sentinel-1-grd`, `cop-dem-glo-30`, `cop-dem-glo-90`, `naip` |
| Microsoft Planetary Computer | https://planetarycomputer.microsoft.com/api/stac/v1 | `sentinel-2-l2a`, `landsat-c2-l2`, `sentinel-1-rtc`, `cop-dem-glo-30`, `esa-worldcover`, `naip` |

Verified on 2026-10-11 against the Earth Search and Planetary Computer `/collections` endpoints.

Always list collections first; ids change: `client.get_collections()`.

```python
# pip install pystac-client planetary-computer rasterio
from pystac_client import Client

bbox = [2.25, 48.80, 2.42, 48.91]          # lon_min, lat_min, lon_max, lat_max
client = Client.open("https://earth-search.aws.element84.com/v1")
search = client.search(
    collections=["sentinel-2-c1-l2a"],
    bbox=bbox,
    datetime="2025-06-01/2025-08-31",
    query={"eo:cloud_cover": {"lt": 10}},
    sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    max_items=20,
)
items = list(search.items())
for it in items:
    print(it.id, it.datetime.date(), it.properties["eo:cloud_cover"], list(it.assets)[:6])
```

Planetary Computer: same search, but it ignores `sortby`; sort locally: `items = sorted(search.items(), key=lambda i: i.properties["eo:cloud_cover"])`. Sign the asset URLs before reading them:
```python
import planetary_computer
client = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                     modifier=planetary_computer.sign_inplace)
```

Notes:
- Asset keys differ by catalog: Earth Search uses names (`red`, `nir`, `scl`, `visual`), Planetary Computer uses band ids (`B04`, `B08`, `SCL`, `visual`). Print `item.assets` before coding against them.
- Check `raster:bands` scale and offset in the asset metadata before converting to reflectance. For Sentinel-2 offset handling see the `sentinel2-indices` skill.
- Scene cloud cover is per tile. For a small area, compute the cloud fraction from the SCL band (Sentinel-2) or `qa_pixel` (Landsat) inside the area, and sort by that.
- Sentinel-2 tiles overlap. The same date can appear as two items over a tile border; pick by `s2:mgrs_tile` or mosaic.

Read only your window of a COG:
```python
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

href = items[0].assets["red"].href
with rasterio.open(href) as src:
    b = transform_bounds("EPSG:4326", src.crs, *bbox)
    data = src.read(1, window=from_bounds(*b, transform=src.transform))
```

## Step 3: load in QGIS

- COG over HTTP: Layer > Add Layer > Add Raster Layer > Protocol: HTTP(S), paste the asset URL. Or in Python:
  ```python
  iface.addRasterLayer("/vsicurl/https://.../B04.tif", "B04")
  ```
  Planetary Computer URLs must be signed first and the signature expires after a while.
- Sentinel-2 true color quick look: the `visual` asset (8-bit RGB COG) of the item.
- STAC browsing without code: Browser panel > STAC (QGIS 3.40+); search and filter items in Data Source Manager > STAC (QGIS 3.42+).
- IGN orthophotos (France), WMS: `https://data.geopf.fr/wms-r` with layer `ORTHOIMAGERY.ORTHOPHOTOS`. WMTS at `https://data.geopf.fr/wmts`.
- XYZ tiles are for display only. Do not run analysis on rendered tiles; use the underlying COG.

## Before you hand over data

- [ ] License allows the intended use, attribution text noted (for example "Contains modified Copernicus Sentinel data 2025").
- [ ] Capture date known and within the user's window.
- [ ] Cloud cover checked over the area itself, not only per scene.
- [ ] Resolution suits the smallest object of interest (at least 3 to 5 pixels across the smallest side to detect, 10 or more for clean outlines).
- [ ] CRS of the data noted before measuring (UTM for Sentinel-2 and Landsat).

## Going further

AI Agent for QGIS fetches Sentinel-2 and Landsat scenes and computes indices from a chat: https://terra-lab.ai/ai-agent?utm_source=skills&utm_medium=geoai-skills&utm_campaign=open-imagery-finder
