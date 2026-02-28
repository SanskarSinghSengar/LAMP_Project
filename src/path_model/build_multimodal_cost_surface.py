import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import rasterize
from rasterio.warp import reproject, Resampling
from scipy.ndimage import gaussian_filter
from pathlib import Path


# =========================================================
# PATH CONFIGURATION
# =========================================================

DEM_PATH = Path("data/raw/task1/DEM_Subset-Original.tif")
BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
SAR_PATH = Path("data/raw/task1/SAR-MS.tif")
ORTHO_PATH = Path("data/raw/task1/OrthoImage_Subset.tif")

OUTPUT_PATH = Path("data/processed/cost_surface_multimodal.tif")


# =========================================================
# HELPER FUNCTION: RESAMPLE TO MATCH DEM
# =========================================================

def resample_to_match(source_array, source_transform, source_crs,
                      target_shape, target_transform, target_crs):

    destination = np.zeros(target_shape, dtype=np.float32)

    reproject(
        source=source_array,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        dst_transform=target_transform,
        dst_crs=target_crs,
        resampling=Resampling.bilinear
    )

    return destination


# =========================================================
# LOAD DEM (MASTER GRID)
# =========================================================

with rasterio.open(DEM_PATH) as src:
    dem = src.read(1)
    transform = src.transform
    crs = src.crs

rows, cols = dem.shape


# =========================================================
# SLOPE COMPONENT
# =========================================================

dx, dy = np.gradient(dem)
slope = np.sqrt(dx**2 + dy**2)

slope_cost = slope / slope.max()


# =========================================================
# SAR COMPONENT (ROUGHNESS PROXY)
# =========================================================

with rasterio.open(SAR_PATH) as src:
    sar = src.read(1)
    sar_transform = src.transform
    sar_crs = src.crs

sar_resampled = resample_to_match(
    sar,
    sar_transform,
    sar_crs,
    dem.shape,
    transform,
    crs
)

sar_resampled = (sar_resampled - sar_resampled.min()) / (
    sar_resampled.max() - sar_resampled.min() + 1e-9
)

sar_cost = sar_resampled


# =========================================================
# ORTHO COMPONENT (PATH BIAS)
# =========================================================

with rasterio.open(ORTHO_PATH) as src:
    ortho = src.read(1)
    ortho_transform = src.transform
    ortho_crs = src.crs

ortho_resampled = resample_to_match(
    ortho,
    ortho_transform,
    ortho_crs,
    dem.shape,
    transform,
    crs
)

ortho_resampled = (ortho_resampled - ortho_resampled.min()) / (
    ortho_resampled.max() - ortho_resampled.min() + 1e-9
)

# Smooth and detect lighter regions
blur = gaussian_filter(ortho_resampled, sigma=2)
threshold = blur > np.percentile(blur, 70)

# Lower cost where likely paths are detected
ortho_bias = 1 - threshold.astype(float)


# =========================================================
# CORRIDOR BIAS (CENTRAL PREFERENCE)
# =========================================================

rr, cc = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
center_row = rows // 2
center_col = cols // 2

distance_to_center = np.sqrt((rr - center_row)**2 + (cc - center_col)**2)
corridor_bias = distance_to_center / distance_to_center.max()


# =========================================================
# CONSERVATIVE MULTIMODAL COST
# =========================================================

total_cost = (
    0.6  * slope_cost +
    0.15 * sar_cost +
    0.15 * ortho_bias +
    0.1  * corridor_bias
)

total_cost = total_cost / total_cost.max()


# =========================================================
# APPLY BUILDING OBSTACLES
# =========================================================

buildings = gpd.read_file(BUILDINGS_PATH)

if buildings.crs != crs:
    buildings = buildings.to_crs(crs)

shapes = ((geom, 1) for geom in buildings.geometry)

building_mask = rasterize(
    shapes,
    out_shape=dem.shape,
    transform=transform,
    fill=0,
    dtype="uint8"
)

# Hard barrier
total_cost[building_mask == 1] = 1000


# =========================================================
# SAVE COST SURFACE
# =========================================================

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with rasterio.open(
    OUTPUT_PATH,
    "w",
    driver="GTiff",
    height=rows,
    width=cols,
    count=1,
    dtype="float32",
    crs=crs,
    transform=transform,
) as dst:
    dst.write(total_cost.astype("float32"), 1)

print("Multimodal cost surface saved to:", OUTPUT_PATH)


print("Shape:", total_cost.shape)