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

COST_PATH = Path("data/processed/cost_surface_with_corridor_bias.tif")
BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
OUTPUT_PATH = Path("outputs/multipath_centroid_probability_surface.tif")

K_PATHS = 3
PENALTY_WEIGHT = 5
SMOOTHING_SIGMA = 2


# =========================================================
# DIJKSTRA (WITH TRUE OBSTACLE MASK)
# =========================================================

def dijkstra(cost, obstacle_mask, start, end):
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

                # TRUE obstacle detection
                if obstacle_mask[nr, nc]:
                    continue

                new_dist = current_dist + cost[nr, nc]

                if new_dist < dist[nr, nc]:
                    dist[nr, nc] = new_dist
                    prev[(nr, nc)] = (r, c)
                    heapq.heappush(pq, (new_dist, (nr, nc)))

    # Reconstruct path
    if dist[end] == np.inf:
        return None

    path = []
    cur = end

    while cur in prev:
        path.append(cur)
        cur = prev[cur]

    path.append(start)
    path.reverse()

    return path


# =========================================================
# MULTI-PATH FUNCTION
# =========================================================

def compute_k_paths(base_cost, obstacle_mask, start, end, k, penalty):
    paths = []
    working_cost = base_cost.copy()

    for _ in range(k):
        path = dijkstra(working_cost, obstacle_mask, start, end)

        if path is None:
            break

        paths.append(path)

        # Penalize path to encourage alternative routing
        for r, c in path:
            working_cost[r, c] += penalty

    return paths


# =========================================================
# LOAD COST SURFACE
# =========================================================

print("Using cost surface:", COST_PATH)

with rasterio.open(COST_PATH) as src:
    cost_surface = src.read(1)
    transform = src.transform
    crs = src.crs

rows, cols = cost_surface.shape

# TRUE obstacle mask (buildings only)
obstacle_mask = cost_surface >= 1000


# =========================================================
# LOAD BUILDINGS & CENTROIDS
# =========================================================

buildings = gpd.read_file(BUILDINGS_PATH)

if buildings.crs != crs:
    buildings = buildings.to_crs(crs)

centroids = buildings.geometry.centroid

raster_nodes = []

# for pt in centroids:
#     r, c = rasterio.transform.rowcol(transform, pt.x, pt.y)

#     if 0 <= r < rows and 0 <= c < cols:
#         raster_nodes.append((r, c))
def snap_to_valid_cell(r, c, obstacle_mask, max_radius=3):
    if not obstacle_mask[r, c]:
        return r, c

    for radius in range(1, max_radius + 1):
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < rows and
                    0 <= nc < cols and
                    not obstacle_mask[nr, nc]
                ):
                    return nr, nc

    return None  # no valid cell found


raster_nodes = []

for pt in centroids:
    r, c = rasterio.transform.rowcol(transform, pt.x, pt.y)

    if 0 <= r < rows and 0 <= c < cols:
        snapped = snap_to_valid_cell(r, c, obstacle_mask)

        if snapped is not None:
            raster_nodes.append(snapped)

print(f"\nTotal valid building nodes: {len(raster_nodes)}")


# =========================================================
# MULTI-PATH PROBABILITY SURFACE
# =========================================================

prob_surface = np.zeros_like(cost_surface, dtype=float)

pairs = list(itertools.combinations(raster_nodes, 2))
total_pairs = len(pairs)

print(f"Computing {total_pairs} building pairs")
print(f"{K_PATHS} paths per pair\n")

for i, (start, end) in enumerate(pairs):

    if i % 100 == 0:
        print(f"Progress: {i}/{total_pairs}")

    k_paths = compute_k_paths(
        cost_surface,
        obstacle_mask,
        start,
        end,
        K_PATHS,
        PENALTY_WEIGHT
    )

    for path in k_paths:
        for r, c in path:
            prob_surface[r, c] += 1


# =========================================================
# NORMALIZE
# =========================================================

if prob_surface.max() > 0:
    prob_surface /= prob_surface.max()


# =========================================================
# SMOOTH
# =========================================================

smoothed = gaussian_filter(prob_surface, sigma=SMOOTHING_SIGMA)

# if smoothed.max() > 0:
#     smoothed /= smoothed.max()
smoothed = prob_surface.copy()

if smoothed.max() > 0:
    smoothed /= smoothed.max()


# =========================================================
# SAVE GEOTIFF
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

print(f"\nSaved to: {OUTPUT_PATH}")


# =========================================================
# VISUALIZE
# =========================================================

plt.figure(figsize=(8, 6))
plt.imshow(smoothed, cmap="hot")
plt.title("Multi-Path Centroid-Based Movement Probability Surface")
plt.colorbar(label="Relative Movement Likelihood")
plt.show()