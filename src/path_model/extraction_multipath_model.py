import numpy as np
import itertools
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
import heapq


# =========================================================
# CONFIGURATION
# =========================================================

COST_PATH = Path("data/processed/cost_surface_multimodal.tif")
BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
EXTRACTION_PATH = Path("data/raw/task1/Marks_Brief1.shp")
OUTPUT_PATH = Path("outputs/extraction_multipath_probability_surface.tif")

K_PATHS = 3
PENALTY_WEIGHT = 5


# =========================================================
# DIJKSTRA WITH OBSTACLE MASK
# =========================================================

def dijkstra(cost, obstacle_mask, start, end):
    rows, cols = cost.shape
    visited = np.zeros_like(cost, dtype=bool)
    dist = np.full(cost.shape, np.inf)
    prev = {}

    dist[start] = 0
    pq = [(0, start)]

    neighbors = [
        (-1,0),(1,0),(0,-1),(0,1),
        (-1,-1),(-1,1),(1,-1),(1,1)
    ]

    while pq:
        current_dist,(r,c) = heapq.heappop(pq)

        if visited[r,c]:
            continue

        visited[r,c] = True

        if (r,c) == end:
            break

        for dr,dc in neighbors:
            nr,nc = r+dr, c+dc

            if 0 <= nr < rows and 0 <= nc < cols:

                if obstacle_mask[nr,nc]:
                    continue

                new_dist = current_dist + cost[nr,nc]

                if new_dist < dist[nr,nc]:
                    dist[nr,nc] = new_dist
                    prev[(nr,nc)] = (r,c)
                    heapq.heappush(pq,(new_dist,(nr,nc)))

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
# MULTI PATH
# =========================================================

def compute_k_paths(base_cost, obstacle_mask, start, end, k, penalty):
    paths = []
    working_cost = base_cost.copy()

    for _ in range(k):
        path = dijkstra(working_cost, obstacle_mask, start, end)

        if path is None:
            break

        paths.append(path)

        for r,c in path:
            working_cost[r,c] += penalty

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
obstacle_mask = cost_surface >= 1000


# =========================================================
# SNAP FUNCTION
# =========================================================

def snap_to_valid(r,c, obstacle_mask, radius=3):
    if not obstacle_mask[r,c]:
        return r,c

    for rad in range(1,radius+1):
        for dr in range(-rad,rad+1):
            for dc in range(-rad,rad+1):
                nr,nc = r+dr,c+dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if not obstacle_mask[nr,nc]:
                        return nr,nc
    return None


# =========================================================
# LOAD BUILDINGS
# =========================================================

buildings = gpd.read_file(BUILDINGS_PATH)
if buildings.crs != crs:
    buildings = buildings.to_crs(crs)

building_centroids = buildings.geometry.centroid

building_nodes = []

for pt in building_centroids:
    r,c = rasterio.transform.rowcol(transform, pt.x, pt.y)
    if 0 <= r < rows and 0 <= c < cols:
        snapped = snap_to_valid(r,c, obstacle_mask)
        if snapped is not None:
            building_nodes.append(snapped)

print("Building origins:", len(building_nodes))


# =========================================================
# LOAD EXTRACTION POINTS
# =========================================================

extractions = gpd.read_file(EXTRACTION_PATH)

if extractions.crs != crs:
    extractions = extractions.to_crs(crs)

extraction_nodes = []

for _,row in extractions.iterrows():
    geom = row.geometry

    if geom.geom_type == "MultiPoint":
        points = geom.geoms
    else:
        points = [geom]

    for pt in points:
        r,c = rasterio.transform.rowcol(transform, pt.x, pt.y)
        if 0 <= r < rows and 0 <= c < cols:
            snapped = snap_to_valid(r,c, obstacle_mask)
            if snapped is not None:
                extraction_nodes.append(snapped)

print("Extraction nodes:", len(extraction_nodes))


# =========================================================
# EXTRACTON FLOW MODEL
# =========================================================

prob_surface = np.zeros_like(cost_surface, dtype=float)

print("Computing building → extraction multipath routing\n")

for i, origin in enumerate(building_nodes):

    if i % 10 == 0:
        print(f"Processing building {i}/{len(building_nodes)}")

    for destination in extraction_nodes:

        k_paths = compute_k_paths(
            cost_surface,
            obstacle_mask,
            origin,
            destination,
            K_PATHS,
            PENALTY_WEIGHT
        )

        for path in k_paths:
            for r,c in path:
                prob_surface[r,c] += 1


# =========================================================
# NORMALIZE
# =========================================================

if prob_surface.max() > 0:
    prob_surface /= prob_surface.max()


# =========================================================
# SAVE OUTPUT
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
    dst.write(prob_surface.astype("float32"), 1)

print("\nSaved extraction flow surface to:", OUTPUT_PATH)


# =========================================================
# VISUALIZE
# =========================================================

plt.figure(figsize=(8,6))
plt.imshow(prob_surface, cmap="hot")
plt.title("Building → Extraction Multi-Path Flow Surface")
plt.colorbar(label="Relative Flow Likelihood")
plt.show()