from rasterio.features import rasterize
import numpy as np
import rasterio
import geopandas as gpd
from pathlib import Path
from scipy.ndimage import distance_transform_edt
import matplotlib.pyplot as plt


# =====================================
# PATHS
# =====================================

# BASE_COST_PATH = Path("data/processed/cost_surface.tif")
BASE_COST_PATH = Path("data/processed/cost_surface_with_buildings.tif")
BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
OUTPUT_PATH = Path("data/processed/cost_surface_with_corridor_bias.tif")


# =====================================
# LOAD BASE COST
# =====================================

with rasterio.open(BASE_COST_PATH) as src:
    base_cost = src.read(1)
    transform = src.transform
    crs = src.crs


rows, cols = base_cost.shape


# =====================================
# CREATE BUILDING MASK
# =====================================

buildings = gpd.read_file(BUILDINGS_PATH)

if buildings.crs != crs:
    buildings = buildings.to_crs(crs)

mask = np.zeros((rows, cols), dtype=np.uint8)

for geom in buildings.geometry:
    shapes = [(geom, 1)]
    rasterized = rasterize(
        shapes,
        out_shape=(rows, cols),
        transform=transform,
        fill=0
    )
    mask = np.maximum(mask, rasterized)


# =====================================
# DISTANCE FROM BUILDINGS
# =====================================

# Invert mask: 1 = open space
open_space = 1 - mask

distance = distance_transform_edt(open_space)

# Normalize distance
if distance.max() > 0:
    distance = distance / distance.max()


# =====================================
# CREATE CORRIDOR PENALTY
# =====================================

# Penalize narrow areas slightly
corridor_penalty = 1 - distance

# Scale penalty (tune strength here)
# CORRIDOR_WEIGHT = 3.0
# corridor_penalty = corridor_penalty * CORRIDOR_WEIGHT
# Normalize distance
if distance.max() > 0:
    distance = distance / distance.max()

# Stronger corridor shaping
corridor_penalty = (1 - distance) ** 2

CORRIDOR_WEIGHT = 15.0
corridor_penalty = corridor_penalty * CORRIDOR_WEIGHT


# =====================================
# FINAL COST SURFACE
# =====================================

# Buildings remain completely blocked
final_cost = base_cost + corridor_penalty
final_cost[mask == 1] = 1000


# =====================================
# SAVE
# =====================================

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
    dst.write(final_cost.astype("float32"), 1)


print(f"\nSaved corridor-biased cost surface to {OUTPUT_PATH}")


# =====================================
# VISUALIZE
# =====================================

plt.imshow(final_cost, cmap="viridis")
plt.title("Corridor-Biased Cost Surface")
plt.colorbar()
plt.show()