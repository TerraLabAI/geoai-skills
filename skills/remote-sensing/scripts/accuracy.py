#!/usr/bin/env python3
"""Accuracy assessment for a classification: overall accuracy, kappa,
producer's and user's accuracy per class.

Usage:
  python3 accuracy.py matrix.csv
      CSV confusion matrix with a header row of class names; first column is
      the class name; rows = reference (truth), columns = predicted (map).
      Add --rows-predicted if your rows are the map classes instead.
  python3 accuracy.py --pairs ref_pred.csv
      CSV with columns reference,predicted (header required), one sample per row.

Standard library only.
"""
import argparse
import csv
import sys
from collections import Counter


def from_pairs(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or not {"reference", "predicted"} <= set(rows[0]):
        sys.exit("pairs CSV needs columns: reference,predicted")
    classes = sorted({r["reference"] for r in rows} | {r["predicted"] for r in rows})
    c = Counter((r["reference"], r["predicted"]) for r in rows)
    return classes, [[c[(a, b)] for b in classes] for a in classes]


def from_matrix(path, rows_predicted):
    with open(path, newline="") as f:
        data = [r for r in csv.reader(f) if r]
    classes = [h.strip() for h in data[0][1:]]
    m = [[float(v) for v in r[1:]] for r in data[1:]]
    if len(m) != len(classes) or any(len(r) != len(classes) for r in m):
        sys.exit("matrix must be square with matching header and row labels")
    if rows_predicted:
        m = [list(col) for col in zip(*m)]
    return classes, m


def report(classes, m):
    n = sum(map(sum, m))
    if n == 0:
        sys.exit("empty matrix")
    k = len(classes)
    diag = sum(m[i][i] for i in range(k))
    row = [sum(m[i]) for i in range(k)]                      # reference totals
    col = [sum(m[i][j] for i in range(k)) for j in range(k)]  # predicted totals
    oa = diag / n
    pe = sum(row[i] * col[i] for i in range(k)) / (n * n)
    kappa = (oa - pe) / (1 - pe) if pe < 1 else float("nan")
    print(f"samples: {n:g}  overall accuracy: {oa:.3f}  kappa: {kappa:.3f}")
    print(f"{'class':<20}{'reference':>10}{'mapped':>10}{'producer':>10}{'user':>10}")
    for i, c in enumerate(classes):
        pa = m[i][i] / row[i] if row[i] else float("nan")
        ua = m[i][i] / col[i] if col[i] else float("nan")
        flag = "  <50 samples" if row[i] < 50 else ""
        print(f"{c:<20}{row[i]:>10g}{col[i]:>10g}{pa:>10.3f}{ua:>10.3f}{flag}")
    print("producer = 1 - omission error (rows, reference); user = 1 - commission error (columns, map)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("matrix", nargs="?")
    ap.add_argument("--pairs")
    ap.add_argument("--rows-predicted", action="store_true")
    a = ap.parse_args()
    if a.pairs:
        classes, m = from_pairs(a.pairs)
    elif a.matrix:
        classes, m = from_matrix(a.matrix, a.rows_predicted)
    else:
        ap.error("give a matrix CSV or --pairs")
    report(classes, m)


if __name__ == "__main__":
    main()
