# src/visualization/plot_results.py

import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt


def plot_raster(raster_path, title, output_png, cmap="viridis"):

    with rasterio.open(raster_path) as src:
        data = src.read(1)

    plt.figure(figsize=(8, 6))
    plt.imshow(data, cmap=cmap)
    plt.colorbar(label="Value")
    plt.title(title)
    plt.axis("off")

    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.close()

    print(f"Saved image: {output_png}")


if __name__ == "__main__":

    os.makedirs("data/figures/", exist_ok=True)

    plot_raster(
        "data/processed/task2/visibility_count.tif",
        "Visibility Count",
        "data/figures/visibility_count.png",
        cmap="inferno"
    )

    plot_raster(
        "data/processed/task2/visibility_probability.tif",
        "Visibility Probability Surface",
        "data/figures/visibility_probability.png",
        cmap="plasma"
    )

    plot_raster(
        "data/processed/task2/visibility_entropy.tif",
        "Visibility Entropy Surface",
        "data/figures/visibility_entropy.png",
        cmap="magma"
    )