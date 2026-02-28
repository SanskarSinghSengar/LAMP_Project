import numpy as np
import itertools
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
import heapq
from scipy.ndimage import gaussian_filter


# =========================================================
# CONFIGURATION
# =========================================================

# COST_PATH = Path("data/processed/cost_surface_with_buildings.tif")
COST_PATH = Path("data/processed/cost_surface_with_corridor_bias.tif")
BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
OUTPUT_PATH = Path("outputs/centroid_probability_surface.tif")

SMOOTHING_SIGMA = 2  # increase to 3–4 for stronger smoothing


# =========================================================
# DIJKSTRA LEAST COST PATH
# =========================================================

def dijkstra(cost, start, end):
    rows, cols = cost.shape
    visited = np.zeros_like(cost, dtype=bool)
    dist = np.full(cost.shape, np.inf)
    prev = {}

    dist[start] = 0
    pq = [(0, start)]

    neighbors = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    while pq:
        current_dist, (r, c) = heapq.heappop(pq)

        if visited[r, c]:
            continue

        visited[r, c] = True

        if (r, c) == end:
            break

        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc

            if 0 <= nr < rows and 0 <= nc < cols:

                # Skip very high-cost obstacles completely
                if cost[nr, nc] >= 1000:
                    continue

                new_dist = current_dist + cost[nr, nc]

                if new_dist < dist[nr, nc]:
                    dist[nr, nc] = new_dist
                    prev[(nr, nc)] = (r, c)
                    heapq.heappush(pq, (new_dist, (nr, nc)))

    # Reconstruct path
    path = []
    cur = end

    while cur in prev:
        path.append(cur)
        cur = prev[cur]

    path.append(start)
    path.reverse()

    return path


# =========================================================
# LOAD COST SURFACE
# =========================================================

with rasterio.open(COST_PATH) as src:
    cost_surface = src.read(1)
    transform = src.transform
    crs = src.crs

rows, cols = cost_surface.shape


# =========================================================
# LOAD BUILDINGS & COMPUTE CENTROIDS
# =========================================================

buildings = gpd.read_file(BUILDINGS_PATH)

if buildings.crs != crs:
    buildings = buildings.to_crs(crs)

centroids = buildings.geometry.centroid

raster_nodes = []

for pt in centroids:
    r, c = rasterio.transform.rowcol(transform, pt.x, pt.y)

    # Skip out-of-bounds nodes
    if 0 <= r < rows and 0 <= c < cols:
        raster_nodes.append((r, c))

print(f"\nTotal valid building nodes: {len(raster_nodes)}")


# =========================================================
# COMPUTE ALL BUILDING-TO-BUILDING PATHS
# =========================================================

prob_surface = np.zeros_like(cost_surface, dtype=float)

pairs = list(itertools.combinations(raster_nodes, 2))
total_pairs = len(pairs)

print(f"Computing {total_pairs} building-to-building paths...\n")

for i, (start, end) in enumerate(pairs):

    if i % 100 == 0:
        print(f"Progress: {i}/{total_pairs}")

    path = dijkstra(cost_surface, start, end)

    for r, c in path:
        prob_surface[r, c] += 1


# =========================================================
# NORMALIZE
# =========================================================

if prob_surface.max() > 0:
    prob_surface = prob_surface / prob_surface.max()


# =========================================================
# SMOOTHING
# =========================================================

smoothed = gaussian_filter(prob_surface, sigma=SMOOTHING_SIGMA)

if smoothed.max() > 0:
    smoothed = smoothed / smoothed.max()


# =========================================================
# SAVE AS GEOTIFF
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
    dst.write(smoothed.astype("float32"), 1)

print(f"\nSaved GeoTIFF to: {OUTPUT_PATH}")


# =========================================================
# VISUALIZATION
# =========================================================

plt.figure(figsize=(8, 6))
plt.imshow(smoothed, cmap="hot")
plt.title("Smoothed Centroid-Based Movement Probability Surface")
plt.colorbar(label="Relative Movement Likelihood")
plt.show()