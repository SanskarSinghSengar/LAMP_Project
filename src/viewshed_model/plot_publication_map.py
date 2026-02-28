import rasterio
import matplotlib.pyplot as plt
import numpy as np


def plot_overlay(base_raster, overlay_raster, output_png):

    with rasterio.open(base_raster) as src:
        base = src.read(1)

    with rasterio.open(overlay_raster) as src:
        overlay = src.read(1)

    plt.figure(figsize=(10, 8))

    plt.imshow(base, cmap="gray")
    plt.imshow(overlay, cmap="inferno", alpha=0.6)

    plt.colorbar(label="Visibility Probability")

    plt.title("3D Visibility Probability Overlay")
    plt.axis("off")

    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.close()


if __name__ == "__main__":

    plot_overlay(
        "data/raw/task2/OrthoImage_Subset.tif",
        "data/processed/task2/visibility_probability.tif",
        "data/figures/visibility_overlay.png"
    )