import numpy as np
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path


SLOPE_PATH = Path("data/processed/slope_task1.tif")
OUTPUT_PATH = Path("data/processed/cost_surface_task1.tif")


def compute_cost(slope_array):
    """
    Convert slope to movement cost.
    Exponential penalty for steep areas.
    """
    normalized_slope = slope_array / 90.0
    cost = np.exp(3 * normalized_slope)
    return cost


def save_raster(output_path, reference_dataset, data):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=reference_dataset.crs,
        transform=reference_dataset.transform,
    ) as dst:
        dst.write(data, 1)


if __name__ == "__main__":

    with rasterio.open(SLOPE_PATH) as dataset:
        slope = dataset.read(1)
        reference = dataset

    cost_surface = compute_cost(slope)

    print("\nCost Surface Statistics:")
    print("Min cost:", np.min(cost_surface))
    print("Max cost:", np.max(cost_surface))

    save_raster(OUTPUT_PATH, reference, cost_surface.astype(np.float32))

    plt.figure(figsize=(8, 6))
    plt.imshow(cost_surface, cmap="viridis")
    plt.colorbar(label="Movement Cost")
    plt.title("Terrain Cost Surface")
    plt.show()