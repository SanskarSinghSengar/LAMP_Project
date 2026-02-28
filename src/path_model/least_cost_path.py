import numpy as np
import rasterio
import matplotlib.pyplot as plt
from heapq import heappush, heappop
from pathlib import Path


COST_PATH = Path("data/processed/cost_surface_with_buildings.tif")


def neighbors(y, x, shape):
    """8-direction neighbors"""
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dy == 0 and dx == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < shape[0] and 0 <= nx < shape[1]:
                yield ny, nx


def dijkstra(cost_surface, start, end):
    rows, cols = cost_surface.shape

    dist = np.full((rows, cols), np.inf)
    dist[start] = 0

    previous = {}

    pq = []
    heappush(pq, (0, start))

    while pq:
        current_cost, current = heappop(pq)

        if current == end:
            break

        for nbr in neighbors(*current, cost_surface.shape):
            move_cost = cost_surface[nbr]
            new_cost = current_cost + move_cost

            if new_cost < dist[nbr]:
                dist[nbr] = new_cost
                previous[nbr] = current
                heappush(pq, (new_cost, nbr))

    # Reconstruct path
    path = []
    node = end
    while node in previous:
        path.append(node)
        node = previous[node]
    path.append(start)
    path.reverse()

    return path


if __name__ == "__main__":

    with rasterio.open(COST_PATH) as dataset:
        cost_surface = dataset.read(1)

    # 🔥 Temporary manual start/end (must be walkable pixels)
    # start = (5, 5)
    # end = (45, 60)
    start = (32, 2)    # Entrance 0
    end = (43, 52)     # Entrance 2

    path = dijkstra(cost_surface, start, end)

    print("Path length:", len(path))

    # Visualize
    plt.figure(figsize=(8, 6))
    plt.imshow(cost_surface, cmap="viridis")

    ys = [p[0] for p in path]
    xs = [p[1] for p in path]

    plt.plot(xs, ys, color="red", linewidth=2)
    plt.title("Least Cost Path")
    plt.show()