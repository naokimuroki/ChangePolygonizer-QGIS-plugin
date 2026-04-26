import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsProject

from .utils import capture_canvas_to_tiff


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "dialog.ui")
)


class ChangePolygonizerDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        super().__init__()
        self.setupUi(self)

        self.iface = iface

        # --- キャプチャパス ---
        self.before_path = None
        self.after_path = None

        # --- レイヤ初期化 ---
        self.populate_layers()

        # --- スライダー初期値 ---
        self.thresholdSlider.setValue(30)    # 0.3
        self.brightnessSlider.setValue(20)   # 0.2
        self.vegSlider.setValue(50)          # 0.5
        self.cloudSlider.setValue(10)        # 0.1

        # --- 面積初期値 ---
        self.areaSpin.setValue(10)

        # --- シグナル接続 ---
        self.captureBeforeButton.clicked.connect(self.capture_before)
        self.captureAfterButton.clicked.connect(self.capture_after)
        
        # --- レイヤ変更時にキャプチャ無効化 ---
        self.beforeCombo.currentIndexChanged.connect(self.reset_before_capture)
        self.afterCombo.currentIndexChanged.connect(self.reset_after_capture)

    # -----------------------------
    # レイヤ一覧更新
    # -----------------------------
    def populate_layers(self):
        self.beforeCombo.clear()
        self.afterCombo.clear()

        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == layer.RasterLayer:
                self.beforeCombo.addItem(layer.name(), layer)
                self.afterCombo.addItem(layer.name(), layer)
        
        # --- 更新時にキャプチャリセット ---
        self.reset_before_capture()
        self.reset_after_capture()

    # -----------------------------
    # キャプチャリセット
    # -----------------------------
    def reset_before_capture(self):
        self.before_path = None
        self.captureBeforeButton.setText("画像Aをキャプチャ")

    def reset_after_capture(self):
        self.after_path = None
        self.captureAfterButton.setText("画像Bをキャプチャ")

    # -----------------------------
    # キャプチャ処理
    # -----------------------------
    def capture_before(self):
        try:
            self.before_path = capture_canvas_to_tiff()
            self.captureBeforeButton.setText("Captured ✓")
        except Exception:
            self.captureBeforeButton.setText("Capture Failed")

    def capture_after(self):
        try:
            self.after_path = capture_canvas_to_tiff()
            self.captureAfterButton.setText("Captured ✓")
        except Exception:
            self.captureAfterButton.setText("Capture Failed")

    # -----------------------------
    # 入力取得
    # -----------------------------
    def get_inputs(self):

        before_layer = self.beforeCombo.currentData()
        after_layer = self.afterCombo.currentData()

        # --- キャプチャ優先 ---
        if self.before_path:
            before = self.before_path
        elif before_layer:
            before = before_layer.source()
        else:
            before = None

        if self.after_path:
            after = self.after_path
        elif after_layer:
            after = after_layer.source()
        else:
            after = None

        # --- パラメータ ---
        threshold = self.thresholdSlider.value() / 100.0
        brightness = self.brightnessSlider.value() / 100.0
        veg = self.vegSlider.value() / 100.0
        cloud = self.cloudSlider.value() / 100.0

        min_area = self.areaSpin.value()

        return before, after, threshold, brightness, veg, cloud, min_area