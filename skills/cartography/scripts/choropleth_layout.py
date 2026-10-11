"""Graduated (choropleth) map of one numeric field, exported through a QGIS print layout.

Runs headless with the Python that ships with QGIS (or inside the QGIS Python console
without the QgsApplication lines). Tested with QGIS 3.44.

    python3 choropleth_layout.py INPUT.gpkg FIELD OUT_BASENAME \
        --title "Population density 2024" --credit "Source: INSEE 2024" \
        --method jenks --classes 5 --ramp Viridis --dpi 300 --label-field name

Writes OUT_BASENAME.png and OUT_BASENAME.pdf (A4 landscape). Prints the class breaks
and the feature count so the result can be checked. Open the PNG before sharing it.
"""
import argparse
import os
import sys

from qgis.core import (
    QgsApplication, QgsVectorLayer, QgsProject, QgsStyle, QgsGraduatedSymbolRenderer,
    QgsClassificationJenks, QgsClassificationQuantile, QgsClassificationEqualInterval,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLegend, QgsLayoutItemScaleBar,
    QgsLayoutItemLabel, QgsLayoutItemPicture, QgsLayoutPoint, QgsLayoutSize, Qgis,
    QgsLayoutExporter, QgsWkbTypes, QgsColorBrewerColorRamp,
)
from qgis.PyQt.QtGui import QColor

METHODS = {"jenks": QgsClassificationJenks, "quantile": QgsClassificationQuantile,
           "equal": QgsClassificationEqualInterval}


def text_format(size):
    fmt = QgsTextFormat()
    fmt.setSize(size)
    return fmt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("field"); ap.add_argument("out")
    ap.add_argument("--title", default=""); ap.add_argument("--credit", default="")
    ap.add_argument("--method", choices=METHODS, default="jenks")
    ap.add_argument("--classes", type=int, default=5)
    ap.add_argument("--ramp", default="Viridis")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--label-field")
    a = ap.parse_args()

    qgs = QgsApplication([], False)
    qgs.initQgis()
    project = QgsProject.instance()

    layer = QgsVectorLayer(a.input, "data", "ogr")
    if not layer.isValid():
        sys.exit(f"cannot open {a.input}")
    if layer.fields().indexOf(a.field) < 0:
        sys.exit(f"field {a.field} not in {[f.name() for f in layer.fields()]}")
    project.addMapLayer(layer)
    print("features:", layer.featureCount(), "| CRS:", layer.crs().authid(),
          "| geometry:", QgsWkbTypes.displayString(layer.wkbType()))

    # Graduated renderer: classification method + color ramp from the default style
    renderer = QgsGraduatedSymbolRenderer(a.field)
    renderer.setClassificationMethod(METHODS[a.method]())
    renderer.updateClasses(layer, a.classes)
    ramp = QgsStyle.defaultStyle().colorRamp(a.ramp)
    if ramp is None and a.ramp in QgsColorBrewerColorRamp.listSchemeNames():
        ramp = QgsColorBrewerColorRamp(a.ramp, a.classes)
    if ramp is None:
        sys.exit(f"ramp {a.ramp} not found; use Viridis or a ColorBrewer name such as YlOrRd")
    renderer.updateColorRamp(ramp)
    layer.setRenderer(renderer)
    for r in renderer.ranges():
        print(f"class {r.lowerValue():.4g} - {r.upperValue():.4g}  ({r.label()})")

    if a.label_field:
        s = QgsPalLayerSettings()
        s.fieldName = a.label_field
        fmt = QgsTextFormat(); fmt.setSize(8)
        buf = QgsTextBufferSettings(); buf.setEnabled(True); buf.setSize(0.8)
        buf.setColor(QColor("white")); fmt.setBuffer(buf)
        s.setFormat(fmt)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(s))
        layer.setLabelsEnabled(True)
    layer.setName(a.field)  # legend shows a readable name, not "data"

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()  # one A4 landscape page
    mm = Qgis.LayoutUnit.Millimeters

    m = QgsLayoutItemMap(layout)
    m.attemptMove(QgsLayoutPoint(10, 20, mm)); m.attemptResize(QgsLayoutSize(200, 175, mm))
    m.setCrs(layer.crs())
    m.setExtent(layer.extent())
    m.setFrameEnabled(True)
    layout.addLayoutItem(m)

    title = QgsLayoutItemLabel(layout)
    title.setText(a.title); title.setTextFormat(text_format(18))
    title.attemptMove(QgsLayoutPoint(10, 5, mm)); title.attemptResize(QgsLayoutSize(270, 12, mm))
    layout.addLayoutItem(title)

    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(m); legend.setTitle(f"{a.field} ({a.method}, {a.classes} classes)")
    legend.attemptMove(QgsLayoutPoint(215, 20, mm))
    layout.addLayoutItem(legend)

    bar = QgsLayoutItemScaleBar(layout)
    bar.setStyle("Single Box"); bar.setLinkedMap(m); bar.applyDefaultSize()
    bar.attemptMove(QgsLayoutPoint(215, 170, mm))
    layout.addLayoutItem(bar)

    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(os.path.join(QgsApplication.svgPaths()[0], "arrows/NorthArrow_02.svg"))
    north.setLinkedMap(m); north.setNorthMode(QgsLayoutItemPicture.NorthMode.GridNorth)
    north.attemptMove(QgsLayoutPoint(260, 150, mm)); north.attemptResize(QgsLayoutSize(12, 15, mm))
    layout.addLayoutItem(north)

    credit = QgsLayoutItemLabel(layout)
    credit.setText(f"{a.credit}\nCRS: [% @project_crs %]" if a.credit else "CRS: [% @project_crs %]")
    credit.setTextFormat(text_format(7))
    credit.attemptMove(QgsLayoutPoint(215, 190, mm)); credit.attemptResize(QgsLayoutSize(75, 12, mm))
    layout.addLayoutItem(credit)
    project.setCrs(layer.crs())

    exp = QgsLayoutExporter(layout)
    img = QgsLayoutExporter.ImageExportSettings(); img.dpi = a.dpi
    pdf = QgsLayoutExporter.PdfExportSettings(); pdf.dpi = a.dpi
    r1 = exp.exportToImage(a.out + ".png", img)
    r2 = exp.exportToPdf(a.out + ".pdf", pdf)
    print("png:", "ok" if r1 == QgsLayoutExporter.ExportResult.Success else r1,
          "| pdf:", "ok" if r2 == QgsLayoutExporter.ExportResult.Success else r2)
    qgs.exitQgis()


if __name__ == "__main__":
    main()
