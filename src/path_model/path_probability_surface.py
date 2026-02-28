import numpy as np
import itertools
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
import heapq


# -------------------------
# PATHS
# -------------------------

COST_PATH = Path("data/processed/cost_surface_with_buildings.tif")
ENTRANCES_PATH = Path("data/raw/task1/Marks_Brief1.shp")
DEM_PATH = Path("data/raw/task1/DEM_Subset-Original.tif")


# -------------------------
# DIJKSTRA
# -------------------------

def dijkstra(cost, start, end):
    rows, cols = cost.shape
    visited = np.zeros_like(cost, dtype=bool)
    dist = np.full_like(cost, np.inf)
    prev = {}

    dist[start] = 0
    pq = [(0, start)]

    neighbors = [(-1,0),(1,0),(0,-1),(0,1),
                 (-1,-1),(-1,1),(1,-1),(1,1)]

    while pq:
        current_dist, (r,c) = heapq.heappop(pq)

        if visited[r,c]:
            continue

        visited[r,c] = True

        if (r,c) == end:
            break

        for dr,dc in neighbors:
            nr, nc = r+dr, c+dc

            if 0 <= nr < rows and 0 <= nc < cols:

                new_dist = current_dist + cost[nr,nc]

                if new_dist < dist[nr,nc]:
                    dist[nr,nc] = new_dist
                    prev[(nr,nc)] = (r,c)
                    heapq.heappush(pq, (new_dist, (nr,nc)))

    path = []
    cur = end
    while cur in prev:
        path.append(cur)
        cur = prev[cur]

    path.append(start)
    path.reverse()

    return path


# -------------------------
# LOAD DATA
# -------------------------

with rasterio.open(COST_PATH) as src:
    cost_surface = src.read(1)
    transform = src.transform
    crs = src.crs

entrances = gpd.read_file(ENTRANCES_PATH)

if entrances.crs != crs:
    entrances = entrances.to_crs(crs)

# Convert entrances to pixel coords
raster_points = []

for _, row in entrances.iterrows():

    geom = row.geometry

    if geom.geom_type == "Point":
        pts = [geom]
    elif geom.geom_type == "MultiPoint":
        pts = list(geom.geoms)
    else:
        continue

    for pt in pts:
        r, c = rasterio.transform.rowcol(transform, pt.x, pt.y)
        raster_points.append((r,c))

print(f"\nTotal entrance nodes: {len(raster_points)}")

# -------------------------
# COMPUTE ALL PAIRS
# -------------------------

prob_surface = np.zeros_like(cost_surface, dtype=float)

pairs = list(itertools.combinations(raster_points, 2))
print(f"Computing {len(pairs)} paths...")

for start, end in pairs:
    print("Path:", start, "→", end)
    path = dijkstra(cost_surface, start, end)

    for r,c in path:
        prob_surface[r,c] += 1

# Normalize
prob_surface = prob_surface / prob_surface.max()

# -------------------------
# VISUALIZE
# -------------------------

plt.figure(figsize=(8,6))
plt.imshow(prob_surface, cmap="hot")
plt.title("Movement Probability Surface")
plt.colorbar(label="Relative Movement Likelihood")
plt.show()