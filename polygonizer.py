from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsPointXY
)
from PyQt5.QtCore import QVariant


def mask_to_polygons(mask, geotransform, name, min_area):

    gt = geotransform

    height, width = mask.shape

    layer = QgsVectorLayer("Polygon?crs=EPSG:3857", name, "memory")
    pr = layer.dataProvider()

    pr.addAttributes([QgsField("area_px", QVariant.Int)])
    layer.updateFields()

    features = []

    for y in range(height):
        for x in range(width):

            if not mask[y, x]:
                continue

            x1 = gt[0] + x * gt[1]
            y1 = gt[3] + y * gt[5]

            x2 = gt[0] + (x+1) * gt[1]
            y2 = gt[3] + (y+1) * gt[5]

            pts = [
                QgsPointXY(x1, y1),
                QgsPointXY(x2, y1),
                QgsPointXY(x2, y2),
                QgsPointXY(x1, y2),
                QgsPointXY(x1, y1),
            ]

            geom = QgsGeometry.fromPolygonXY([pts])

            feat = QgsFeature()
            feat.setGeometry(geom)
            feat.setAttributes([1])

            features.append(feat)

    pr.addFeatures(features)
    layer.updateExtents()

    return layer