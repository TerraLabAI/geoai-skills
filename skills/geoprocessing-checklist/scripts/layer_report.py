#!/usr/bin/env python3
"""Report on a vector layer before and after each processing step.

Prints feature count, CRS, extent, invalid and null geometry counts, and the
total area (polygons) or length (lines) measured in a projected CRS (the
layer's own if projected, else its UTM zone). Uses osgeo.ogr (GDAL) or
geopandas, whichever is installed.

Example: python3 layer_report.py parcels.gpkg --layer parcels
Exit code 1 when invalid or null geometries are found.
"""
import argparse
import sys


def utm_epsg(lon, lat):
    zone = min(int((lon + 180) // 6) + 1, 60)
    return (32600 if lat >= 0 else 32700) + zone


def report_ogr(path, layer_name):
    from osgeo import ogr, osr
    ogr.UseExceptions()
    ds = ogr.Open(path)
    lyr = ds.GetLayerByName(layer_name) if layer_name else ds.GetLayer(0)
    srs = lyr.GetSpatialRef()
    xmin, xmax, ymin, ymax = lyr.GetExtent()
    target, transform = srs, None
    if srs is not None and (srs.IsGeographic() or "Pseudo-Mercator" in (srs.GetName() or "")):
        wgs = osr.SpatialReference(); wgs.ImportFromEPSG(4326)
        wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        ct = osr.CoordinateTransformation(srs, wgs)
        cx, cy, _ = ct.TransformPoint((xmin + xmax) / 2, (ymin + ymax) / 2)
        target = osr.SpatialReference(); target.ImportFromEPSG(utm_epsg(cx, cy))
        target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        transform = osr.CoordinateTransformation(srs, target)
    n = invalid = null = 0
    area = length = 0.0
    for f in lyr:
        n += 1
        g = f.GetGeometryRef()
        if g is None or g.IsEmpty():
            null += 1
            continue
        if not g.IsValid():
            invalid += 1
        g = g.Clone()
        if transform:
            g.Transform(transform)
        area += g.GetArea()
        length += g.Length() if g.GetDimension() == 1 else 0.0
    crs = "none" if srs is None else "%s:%s %s" % (srs.GetAuthorityName(None), srs.GetAuthorityCode(None), srs.GetName())
    mcrs = "none" if target is None else "EPSG:%s" % target.GetAuthorityCode(None)
    return n, crs, (xmin, ymin, xmax, ymax), invalid, null, area, length, mcrs


def report_gpd(path, layer_name):
    import geopandas as gpd
    gdf = gpd.read_file(path, layer=layer_name) if layer_name else gpd.read_file(path)
    null = int((gdf.geometry.isna() | gdf.geometry.is_empty).sum())
    valid = gdf[~(gdf.geometry.isna() | gdf.geometry.is_empty)]
    invalid = int((~valid.geometry.is_valid).sum())
    proj, mcrs = valid, "none"
    if gdf.crs is not None:
        proj = valid if (gdf.crs.is_projected and gdf.crs.to_epsg() != 3857) else valid.to_crs(valid.estimate_utm_crs())
        mcrs = str(proj.crs.to_string())
    dim = proj.geometry.geom_type.str.contains("Line")
    return (len(gdf), str(gdf.crs), tuple(gdf.total_bounds), invalid, null,
            float(proj.geometry.area.sum()), float(proj[dim].geometry.length.sum()), mcrs)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", help="vector file (GeoPackage, Shapefile, GeoJSON, ...)")
    p.add_argument("--layer", help="layer name in a multi-layer file")
    a = p.parse_args()
    try:
        import osgeo  # noqa: F401
        fn = report_ogr
    except ImportError:
        try:
            import geopandas  # noqa: F401
            fn = report_gpd
        except ImportError:
            print("error: needs GDAL Python bindings (osgeo) or geopandas; in QGIS use its Python", file=sys.stderr)
            return 2
    try:
        n, crs, ext, invalid, null, area, length, mcrs = fn(a.path, a.layer)
    except Exception as e:  # noqa: BLE001
        print("error: cannot read %s: %s" % (a.path, e), file=sys.stderr)
        return 2
    print("features: %d" % n)
    print("crs: %s" % crs)
    print("extent: %.6f %.6f %.6f %.6f" % ext)
    print("invalid geometries: %d, null or empty: %d" % (invalid, null))
    if area:
        print("total area: %.1f m2 (%.4f km2) measured in %s" % (area, area / 1e6, mcrs))
    if length:
        print("total length: %.1f m measured in %s" % (length, mcrs))
    return 1 if (invalid or null) else 0


if __name__ == "__main__":
    sys.exit(main())
