from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsFillSymbol

import os
import numpy as np

from .dialog import ChangePolygonizerDialog
from .raster_engine import compute_diff
from .polygonizer import mask_to_polygons


class ChangePolygonizer:
    def __init__(self, iface):
        self.iface = iface
        self.dlg = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")

        self.action = QAction(QIcon(icon_path), "Change Polygonizer", self.iface.mainWindow())
        self.action.setToolTip("Change Polygonizer")

        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Change Polygonizer", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Change Polygonizer", self.action)

    def run(self):
        if self.dlg is None:
            self.dlg = ChangePolygonizerDialog(self.iface)
            self.dlg.runButton.clicked.connect(self.execute)

        self.dlg.populate_layers()

        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()

    # -----------------------------
    # スタイル（CMY）
    # -----------------------------
    def style_layer(self, layer, idx):

        colors = [
            (0, 255, 255, 128),   # Cyan
            (255, 0, 255, 128),   # Magenta
            (255, 255, 0, 128)    # Yellow
        ]

        r, g, b, a = colors[idx % 3]

        symbol = QgsFillSymbol.createSimple({
            'color': f'{r},{g},{b},{a}',
            'outline_style': 'no'
        })

        layer.renderer().setSymbol(symbol)

    # -----------------------------
    # 実行
    # -----------------------------
    def execute(self):
        try:
            # cloud 追加
            before, after, threshold, brightness, veg, cloud, min_area = self.dlg.get_inputs()

            if not before or not after:
                QMessageBox.warning(None, "Error", "Before/After not set")
                return

            # compute_diff 追加
            diff, gt = compute_diff(
                before,
                after,
                brightness,
                veg,
                cloud
            )

            # 3段階
            thresholds = [
                threshold,
                min(threshold + 0.1, 1.0),
                min(threshold + 0.2, 1.0)
            ]

            print("=== DIFF INFO ===")
            print("min:", float(diff.min()))
            print("max:", float(diff.max()))
            print("mean:", float(diff.mean()))
            print("thresholds:", thresholds)

            for i, t in enumerate(thresholds):

                mask = diff > t

                print(f"threshold {t:.3f} → pixels:", int(mask.sum()))

                layer = mask_to_polygons(
                    mask,
                    gt,
                    f"change_thr_{i+1}",
                    min_area
                )

                if layer:
                    self.style_layer(layer, i)
                    QgsProject.instance().addMapLayer(layer)

            QMessageBox.information(None, "Done", "Polygons generated")

        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))