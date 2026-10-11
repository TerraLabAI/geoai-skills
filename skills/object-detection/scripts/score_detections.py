"""Precision, recall and F1 of detections against a hand-labeled reference set.

A detection matches a reference object when their IoU is at least the threshold;
each reference object matches at most one detection (greedy, best IoU first).
Only detections inside the labeled area count, so pass the area polygon(s) that
were fully labeled.

    python score_detections.py detections.gpkg reference.gpkg labeled_area.gpkg --iou 0.5
"""
import argparse

import geopandas as gpd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("detections"); ap.add_argument("reference"); ap.add_argument("area")
    ap.add_argument("--iou", type=float, default=0.5)
    a = ap.parse_args()

    ref = gpd.read_file(a.reference)
    crs = ref.estimate_utm_crs() if ref.crs.is_geographic else ref.crs
    ref = ref.to_crs(crs)
    det = gpd.read_file(a.detections).to_crs(crs)
    area = gpd.read_file(a.area).to_crs(crs).union_all()
    det = det[det.intersects(area)].reset_index(drop=True)
    ref = ref[ref.intersects(area)].reset_index(drop=True)

    pairs = []
    for i, j in zip(*det.sindex.query(ref.geometry, predicate="intersects")[::-1]):
        d, r = det.geometry[i], ref.geometry[j]
        inter = d.intersection(r).area
        iou = inter / (d.area + r.area - inter)
        if iou >= a.iou:
            pairs.append((iou, i, j))
    used_d, used_r = set(), set()
    for iou, i, j in sorted(pairs, reverse=True):
        if i not in used_d and j not in used_r:
            used_d.add(i); used_r.add(j)

    tp = len(used_d); fp = len(det) - tp; fn = len(ref) - tp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    print(f"reference {len(ref)}, detections {len(det)}, IoU >= {a.iou}")
    print(f"TP {tp}  FP {fp}  FN {fn}")
    print(f"precision {p:.3f}  recall {r:.3f}  F1 {f1:.3f}")


if __name__ == "__main__":
    main()
