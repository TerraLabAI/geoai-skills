#!/usr/bin/env python3
"""Say whether distances and areas are safe to measure in a CRS.

Give an EPSG code, or a vector file (GeoPackage, Shapefile, GeoJSON) whose CRS
is read with pyproj+fiona, or osgeo (GDAL), whichever is installed. Geographic
CRSs (degrees) and Web Mercator (EPSG:3857 and aliases) are unsafe. With
--lonlat, suggests the UTM EPSG for that point.

Examples:
  python3 check_measurement_crs.py --epsg 4326 --lonlat 2.35 48.85
  python3 check_measurement_crs.py --file parcels.gpkg
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utm_epsg import describe  # noqa: E402

MERCATOR = {3857, 900913, 3785, 102100, 102113, 54004, 3395}
GEOGRAPHIC_COMMON = {4326, 4258, 4269, 4171, 4283, 4612, 4674, 4490, 4167, 4936}


def epsg_from_file(path):
    """Return (epsg or None, is_geographic or None, name) for a vector file."""
    try:
        from osgeo import ogr
        ogr.UseExceptions()
        ds = ogr.Open(path)
        if ds is None:
            raise SystemExit("error: cannot open %s" % path)
        srs = ds.GetLayer(0).GetSpatialRef()
        if srs is None:
            return None, None, "no CRS"
        srs.AutoIdentifyEPSG()
        code = srs.GetAuthorityCode(None)
        return (int(code) if code else None), bool(srs.IsGeographic()), srs.GetName()
    except ImportError:
        pass
    try:
        import fiona
        from pyproj import CRS
    except ImportError:
        raise SystemExit("error: reading a file needs GDAL Python bindings (osgeo) "
                         "or fiona + pyproj; pass --epsg instead")
    with fiona.open(path) as src:
        if not src.crs_wkt:
            return None, None, "no CRS"
        crs = CRS.from_wkt(src.crs_wkt)
    return crs.to_epsg(), crs.is_geographic, crs.name


def classify(epsg, geographic=None):
    if epsg in MERCATOR:
        return False, "Web Mercator: lengths grow by 1/cos(lat), areas by 1/cos(lat)^2"
    if geographic is None:
        try:
            from pyproj import CRS
            geographic = CRS.from_epsg(epsg).is_geographic
        except ImportError:
            geographic = epsg in GEOGRAPHIC_COMMON or (4000 <= epsg < 5000)
    if geographic:
        return False, "geographic CRS: units are degrees, not meters"
    return True, "projected CRS: fine for local distances and areas (check its area of use)"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--epsg", type=int, help="EPSG code to check")
    g.add_argument("--file", help="vector file to read the CRS from")
    p.add_argument("--lonlat", nargs=2, type=float, metavar=("LON", "LAT"),
                   help="a point in the data, to suggest a UTM EPSG")
    a = p.parse_args()
    geographic, name = None, ""
    if a.file:
        epsg, geographic, name = epsg_from_file(a.file)
        if epsg is None and geographic is None:
            print("UNSAFE: %s has no CRS; assign the right one first (do not guess)." % a.file)
            return 1
    else:
        epsg = a.epsg
    safe, why = classify(epsg, geographic)
    label = "EPSG:%s" % epsg if epsg else name
    print("%s: %s (%s)" % (label, "SAFE" if safe else "UNSAFE", why))
    if a.lonlat:
        r = describe(*a.lonlat)
        if r["polar"]:
            print("Suggest: " + r["note"])
        else:
            s = "Suggest: EPSG:%d (UTM %d%s)" % (r["wgs84_epsg"], r["zone"], r["hemisphere"])
            if "etrs89_epsg" in r:
                s += " or EPSG:%d (ETRS89)" % r["etrs89_epsg"]
            print(s)
    return 0 if safe else 1


if __name__ == "__main__":
    sys.exit(main())
