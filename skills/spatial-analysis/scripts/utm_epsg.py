#!/usr/bin/env python3
"""Find the UTM zone and EPSG codes for a longitude/latitude (WGS84).

Prints the zone, hemisphere, WGS84 UTM EPSG (326xx north, 327xx south) and,
in Europe zones 28 to 38, the ETRS89 UTM EPSG (258xx). Handles lon=180, the
Norway 32V and Svalbard exceptions, and flags polar areas (UPS 32661/32761).

Example: python3 utm_epsg.py 2.35 48.85
"""
import argparse
import sys


def utm_zone(lon, lat):
    """Return the UTM zone number, with the Norway and Svalbard exceptions."""
    if lon == 180:
        lon = 179.999999  # lon=180 belongs to zone 60
    zone = int((lon + 180) // 6) + 1
    if 56 <= lat < 64 and 3 <= lon < 12:
        zone = 32
    if 72 <= lat < 84:
        if 0 <= lon < 9:
            zone = 31
        elif 9 <= lon < 21:
            zone = 33
        elif 21 <= lon < 33:
            zone = 35
        elif 33 <= lon < 42:
            zone = 37
    return zone


def describe(lon, lat):
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError("lon must be in [-180, 180] and lat in [-90, 90]; did you swap them?")
    if lat > 84 or lat < -80:
        code = 32661 if lat > 0 else 32761
        return {"polar": True, "ups_epsg": code,
                "note": "Outside UTM: use UPS (EPSG:%d) or a polar stereographic CRS." % code}
    zone = utm_zone(lon, lat)
    north = lat >= 0
    out = {"polar": False, "zone": zone, "hemisphere": "N" if north else "S",
           "wgs84_epsg": (32600 if north else 32700) + zone}
    if north and 28 <= zone <= 38 and 34 <= lat <= 72 and -32 <= lon <= 45:
        out["etrs89_epsg"] = 25800 + zone
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("lon", type=float, help="longitude in degrees (x first)")
    p.add_argument("lat", type=float, help="latitude in degrees")
    a = p.parse_args()
    try:
        r = describe(a.lon, a.lat)
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if r["polar"]:
        print(r["note"])
        return 0
    line = "UTM zone %d%s, WGS84 EPSG:%d" % (r["zone"], r["hemisphere"], r["wgs84_epsg"])
    if "etrs89_epsg" in r:
        line += ", ETRS89 EPSG:%d (prefer it for European national data)" % r["etrs89_epsg"]
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
