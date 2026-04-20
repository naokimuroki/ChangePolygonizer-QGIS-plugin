import os
import tempfile
from qgis.core import QgsProject
from qgis.utils import iface
from qgis.PyQt.QtGui import QImage
from osgeo import gdal


def capture_canvas_to_tiff():
    canvas = iface.mapCanvas()

    img = canvas.grab()  # QPixmap
    qimg = img.toImage()

    width = qimg.width()
    height = qimg.height()

    ptr = qimg.bits()
    ptr.setsize(height * width * 4)

    arr = bytes(ptr)

    # 一時ファイル
    tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    path = tmp.name
    tmp.close()

    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(path, width, height, 3, gdal.GDT_Byte)

    extent = canvas.extent()

    xmin = extent.xMinimum()
    xmax = extent.xMaximum()
    ymin = extent.yMinimum()
    ymax = extent.yMaximum()

    geotransform = (
        xmin,
        (xmax - xmin) / width,
        0,
        ymax,
        0,
        -(ymax - ymin) / height
    )

    ds.SetGeoTransform(geotransform)
    ds.SetProjection(QgsProject.instance().crs().toWkt())

    import numpy as np
    img_np = np.frombuffer(arr, dtype=np.uint8).reshape((height, width, 4))

    # RGBA → RGB
    ds.GetRasterBand(1).WriteArray(img_np[:, :, 0])
    ds.GetRasterBand(2).WriteArray(img_np[:, :, 1])
    ds.GetRasterBand(3).WriteArray(img_np[:, :, 2])

    ds = None

    return path