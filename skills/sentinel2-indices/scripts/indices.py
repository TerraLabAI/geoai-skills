#!/usr/bin/env python3
"""Sentinel-2 spectral index formulas, band numbers and optional compute.

List all formulas:      python3 indices.py
One index:              python3 indices.py ndvi
Compute (needs numpy and rasterio, input already in reflectance 0-1):
  python3 indices.py ndvi --band B04=red.tif --band B08=nir.tif -o ndvi.tif
dNBR needs --band pre=nbr_pre.tif --band post=nbr_post.tif.
"""
import argparse
import sys

INDICES = {
    "ndvi": ("(B08 - B04) / (B08 + B04)", ["B08", "B04"], "NIR 10 m, red 10 m; vegetation 0.2-0.9, water < 0"),
    "ndwi": ("(B03 - B08) / (B03 + B08)", ["B03", "B08"], "McFeeters open water; water > 0"),
    "ndmi": ("(B8A - B11) / (B8A + B11)", ["B8A", "B11"], "Gao NDWI / NDMI, leaf moisture; 20 m bands"),
    "ndbi": ("(B11 - B08) / (B11 + B08)", ["B11", "B08"], "built-up; resample B11 (20 m) to 10 m or B08 to 20 m"),
    "nbr": ("(B08 - B12) / (B08 + B12)", ["B08", "B12"], "burn ratio; B8A with B12 keeps both at 20 m"),
    "dnbr": ("pre - post  (NBR before fire minus NBR after)", ["pre", "post"],
             "> 0.1 burned, > 0.66 high severity (USGS ranges)"),
}


def normalized_difference(a, b):
    import numpy as np
    a = a.astype("float32")
    b = b.astype("float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / (a + b)
    out[~np.isfinite(out)] = np.nan
    return out


def compute(name, paths, out_path):
    try:
        import numpy as np  # noqa: F401
        import rasterio
    except ImportError:
        raise SystemExit("error: computing needs numpy and rasterio (pip install numpy rasterio)")
    need = INDICES[name][1]
    missing = [b for b in need if b not in paths]
    if missing:
        raise SystemExit("error: missing --band for %s" % ", ".join(missing))
    arrays, profile = [], None
    for b in need:
        with rasterio.open(paths[b]) as src:
            arrays.append(src.read(1, masked=False))
            if profile is None:
                profile = src.profile
            elif (src.width, src.height, src.transform) != (profile["width"], profile["height"], profile["transform"]):
                raise SystemExit("error: %s grid differs from %s; resample first" % (paths[b], paths[need[0]]))
    res = arrays[0].astype("float32") - arrays[1] if name == "dnbr" else normalized_difference(*arrays)
    profile.update(dtype="float32", count=1, nodata=float("nan"))
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(res, 1)
    print("wrote %s" % out_path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("index", nargs="?", choices=sorted(INDICES), help="index name; omit to list all")
    p.add_argument("--band", action="append", default=[], metavar="NAME=PATH", help="band raster in reflectance")
    p.add_argument("-o", "--output", help="output GeoTIFF; triggers computation")
    a = p.parse_args()
    names = [a.index] if a.index else sorted(INDICES)
    for n in names:
        f, bands, note = INDICES[n]
        print("%-5s = %s   bands: %s   %s" % (n.upper(), f, ", ".join(bands), note))
    if a.output:
        if not a.index:
            print("error: name an index to compute", file=sys.stderr)
            return 2
        compute(a.index, dict(x.split("=", 1) for x in a.band), a.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
