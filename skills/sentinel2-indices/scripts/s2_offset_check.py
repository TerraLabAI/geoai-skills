#!/usr/bin/env python3
"""Decide the Sentinel-2 L2A reflectance formula for one STAC item.

Reads the item JSON (local path or URL) and looks at: the collection id,
s2:processing_baseline / processing:baseline, earthsearch:boa_offset_applied,
and raster:bands scale/offset on the band assets. Prints the formula to turn
digital numbers (DN) into reflectance, and why.

Rules:
  - raster:bands has scale/offset    -> DN * scale + offset (the item says so)
  - baseline >= 04.00, no metadata   -> (DN - 1000) / 10000
  - baseline <  04.00                -> DN / 10000
  - Earth Search sentinel-2-l2a with earthsearch:boa_offset_applied=true
                                     -> DN / 10000 (pixels already shifted; its
                                        offset metadata would apply it twice).
                                        Prefer sentinel-2-c1-l2a.

Example: python3 s2_offset_check.py https://earth-search.aws.element84.com/v1/collections/sentinel-2-c1-l2a/items/<id>
"""
import argparse
import json
import sys
import urllib.request

BAND_KEYS = ("red", "nir", "B04", "B08", "green", "swir16", "B11")


def load(src):
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src, timeout=30) as r:
            return json.load(r)
    with open(src) as f:
        return json.load(f)


def baseline_of(props):
    for k in ("s2:processing_baseline", "processing:baseline", "sentinel2:processing_baseline"):
        if props.get(k):
            try:
                return float(str(props[k])), k
            except ValueError:
                pass
    return None, None


def band_scale(item):
    for k in BAND_KEYS:
        a = item.get("assets", {}).get(k)
        if not a:
            continue
        for b in a.get("raster:bands") or []:
            if "scale" in b or "offset" in b:
                return k, b.get("scale", 1), b.get("offset", 0)
    return None, None, None


def decide(item):
    props = item.get("properties", {})
    coll = item.get("collection", "")
    base, base_key = baseline_of(props)
    applied = props.get("earthsearch:boa_offset_applied")
    asset, scale, offset = band_scale(item)
    why = ["collection=%s" % (coll or "?"),
           "%s=%s" % (base_key or "baseline", "%.2f" % base if base is not None else "missing")]
    if applied is not None:
        why.append("earthsearch:boa_offset_applied=%s" % applied)
    warn = None
    if coll == "sentinel-2-l2a" and applied is True:
        why.append("Earth Search already removed the offset from the pixels; ignore raster:bands offset")
        warn = "old Earth Search collection; prefer sentinel-2-c1-l2a, whose metadata is correct"
        return "reflectance = DN / 10000", why, warn
    if asset:
        why.append("raster:bands on '%s' scale=%s offset=%s" % (asset, scale, offset))
        formula = "reflectance = DN * %s + (%s)" % (scale, offset)
    elif base is None:
        return None, why, "processing baseline unknown: read it from the product metadata (MTD_MSIL2A.xml BOA_ADD_OFFSET)"
    elif base >= 4.0:
        why.append("baseline >= 04.00 and no scale metadata: BOA_ADD_OFFSET is -1000")
        formula = "reflectance = (DN - 1000) / 10000"
    else:
        why.append("baseline < 04.00: no offset")
        formula = "reflectance = DN / 10000"
    return formula, why, warn


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("item", help="STAC item JSON: local path or http(s) URL")
    a = p.parse_args()
    try:
        item = load(a.item)
    except Exception as e:  # noqa: BLE001
        print("error: cannot read item: %s" % e, file=sys.stderr)
        return 2
    formula, why, warn = decide(item)
    print("item: %s" % item.get("id", "?"))
    if formula:
        print(formula + "  (DN = 0 is nodata; mask it first)")
    print("why: " + "; ".join(why))
    if warn:
        print("warning: " + warn)
    return 0 if formula else 1


if __name__ == "__main__":
    sys.exit(main())
