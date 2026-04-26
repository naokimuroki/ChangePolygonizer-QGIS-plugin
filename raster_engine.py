import numpy as np
from osgeo import gdal
from scipy.ndimage import gaussian_filter


# -----------------------------
# GeoTransform保証
# -----------------------------
def ensure_georef(ds):
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()

    if gt is None or gt == (0, 1, 0, 0, 0, 1):
        gt = (0, 1, 0, 0, 0, -1)
        ds.SetGeoTransform(gt)

    if not proj:
        ds.SetProjection("EPSG:3857")

    return ds


# -----------------------------
# 3857へ再投影
# -----------------------------
def reproject_to_3857(path):
    src = gdal.Open(path)
    if src is None:
        raise Exception(f"Cannot open raster: {path}")

    src = ensure_georef(src)

    src_proj = src.GetProjection()
    gt = src.GetGeoTransform()

    xsize = src.RasterXSize
    ysize = src.RasterYSize
    bands = src.RasterCount

    dst = gdal.GetDriverByName("MEM").Create(
        "", xsize, ysize, bands, gdal.GDT_Float32
    )

    dst.SetGeoTransform(gt)
    dst.SetProjection("EPSG:3857")

    gdal.ReprojectImage(
        src,
        dst,
        src_proj,
        "EPSG:3857",
        gdal.GRA_Bilinear
    )

    arr = dst.ReadAsArray().astype(float)

    return arr, dst.GetGeoTransform()


# -----------------------------
# RGB整形
# -----------------------------
def to_rgb(arr):
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr])

    if arr.shape[0] >= 3:
        arr = arr[:3]

    return arr


# -----------------------------
# 正規化
# -----------------------------
def normalize_pair(a, b):
    vmin = min(a.min(), b.min())
    vmax = max(a.max(), b.max())

    a = (a - vmin) / (vmax - vmin + 1e-6)
    b = (b - vmin) / (vmax - vmin + 1e-6)

    return a, b


# -----------------------------
# サイズ一致（リサンプリング）
# -----------------------------
def resample_match(a, b):
    if a.shape == b.shape:
        return a, b

    _, ha, wa = a.shape
    _, hb, wb = b.shape

    h = min(ha, hb)
    w = min(wa, wb)

    a = a[:, :h, :w]
    b = b[:, :h, :w]

    return a, b


# -----------------------------
# 雲・雪マスク
# -----------------------------
def cloud_snow_mask(rgb):
    r, g, b = rgb[0], rgb[1], rgb[2]

    brightness = (r + g + b) / 3.0

    whiteness = 1.0 - (
        np.abs(r - g) +
        np.abs(r - b) +
        np.abs(g - b)
    ) / 3.0

    mask = (brightness > 0.6) & (whiteness > 0.7)

    return mask.astype(float)


# -----------------------------
# メイン処理
# -----------------------------
def compute_diff(
    before_path,
    after_path,
    brightness_w,
    veg_w,
    cloud_w
):

    # --- 読み込み＆3857統一 ---
    a, gt = reproject_to_3857(before_path)
    b, _ = reproject_to_3857(after_path)

    a = to_rgb(a)
    b = to_rgb(b)

    # --- サイズ一致 ---
    a, b = resample_match(a, b)

    # --- 正規化 ---
    a, b = normalize_pair(a, b)

    # --- RGB差分 ---
    dr = b[0] - a[0]
    dg = b[1] - a[1]
    db = b[2] - a[2]

    diff = np.sqrt(dr**2 + dg**2 + db**2)

    # --- 明るさ補正（広域的） ---
    brightness_a = a.mean(axis=0)
    brightness_b = b.mean(axis=0)

    brightness_change = brightness_b - brightness_a
    diff = diff - brightness_w * brightness_change

    # --- 影補正（局所的） ---
    blur_a = gaussian_filter(brightness_a, sigma=10) # 周囲10pixの影を考慮
    blur_b = gaussian_filter(brightness_b, sigma=10) # 周囲10pixの影を考慮

    local_dark_a = blur_a - brightness_a
    local_dark_b = blur_b - brightness_b

    shadow_new = np.maximum(0, local_dark_b - local_dark_a)
    shadow_old = np.maximum(0, local_dark_a - local_dark_b)

    shadow_like = shadow_new + 0.5 * shadow_old # 画像Bの影をより重視

    diff = diff - 0.5 * shadow_like

    # --- 植生補正（緑→茶のみ強調） ---
    veg_index_a = (a[1] - a[0]) / (a[1] + a[0] + 1e-6)
    veg_index_b = (b[1] - b[0]) / (b[1] + b[0] + 1e-6)

    veg_loss = np.maximum(0, veg_index_a - veg_index_b)

    diff = diff + veg_w * veg_loss

    # --- 雲・雪補正 ---
    mask_a = cloud_snow_mask(a)
    mask_b = cloud_snow_mask(b)

    cloud_mask = np.maximum(mask_a, mask_b)

    diff = diff * (1 - cloud_w * cloud_mask)

    # --- 正規化 ---
    diff = diff - diff.min()
    diff = diff / (diff.max() + 1e-6)

    return diff, gt