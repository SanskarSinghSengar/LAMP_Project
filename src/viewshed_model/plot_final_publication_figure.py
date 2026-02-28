import rasterio
import matplotlib.pyplot as plt
import numpy as np


def read(path):
    with rasterio.open(path) as src:
        return src.read(1)


if __name__ == "__main__":

    ortho = read("data/raw/task2/OrthoImage_Subset.tif")
    prob3d = read("data/processed/task2/visibility_probability.tif")
    prob2d = read("data/processed/task2/visibility_probability_2d.tif")
    diff = read("data/processed/task2/visibility_difference.tif")

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel A - 3D
    axes[0].imshow(ortho, cmap="gray")
    axes[0].imshow(
        np.ma.masked_where(prob3d == 0, prob3d),
        cmap="Reds",
        alpha=0.75
    )
    axes[0].set_title("A) 3D Visibility (Terrain + Buildings)")
    axes[0].axis("off")

    # Panel B - 2D
    axes[1].imshow(ortho, cmap="gray")
    axes[1].imshow(
        np.ma.masked_where(prob2d == 0, prob2d),
        cmap="Blues",
        alpha=0.75
    )
    axes[1].set_title("B) 2D Visibility (Terrain Only)")
    axes[1].axis("off")

    # Panel C - Difference
    axes[2].imshow(ortho, cmap="gray")
    axes[2].imshow(
        diff,
        cmap="bwr",
        alpha=0.75
    )
    axes[2].set_title("C) Difference (3D − 2D)")
    axes[2].axis("off")

    plt.suptitle(
        "Figure 6: Comparative Viewshed Analysis at El Bagawat",
        fontsize=16,
        fontweight="bold"
    )

    plt.tight_layout()
    plt.savefig("data/figures/publication_figure.png", dpi=300)
    plt.close()

    print("Final publication figure saved.")