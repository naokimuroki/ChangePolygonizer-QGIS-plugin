from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsPointXY
)
from PyQt5.QtCore import QVariant

import numpy as np
from scipy import ndimage


def mask_to_polygons(mask, geotransform, name, min_area):

    gt = geotransform

    height, width = mask.shape

    # -----------------------------
    # ラベリング（連結成分）
    # -----------------------------
    labeled, num = ndimage.label(mask)

    sizes = ndimage.sum(mask, labeled, range(1, num + 1))

    # min_area未満を除去
    cleaned = np.zeros_like(mask, dtype=bool)

    for i, size in enumerate(sizes):
        if size >= min_area:
            cleaned[labeled == (i + 1)] = True

    # -----------------------------
    # レイヤ作成
    # -----------------------------
    layer = QgsVectorLayer("Polygon?crs=EPSG:3857", name, "memory")
    pr = layer.dataProvider()

    pr.addAttributes([QgsField("area_px", QVariant.Int)])
    layer.updateFields()

    features = []

    # -----------------------------
    # ピクセル→ポリゴン
    # -----------------------------
    for y in range(height):
        for x in range(width):

            if not cleaned[y, x]:
                continue

            x1 = gt[0] + x * gt[1]
            y1 = gt[3] + y * gt[5]

            x2 = gt[0] + (x + 1) * gt[1]
            y2 = gt[3] + (y + 1) * gt[5]

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