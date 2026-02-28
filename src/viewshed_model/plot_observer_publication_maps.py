import os
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np


def plot_observer_map(
    ortho_path,
    viewshed_path,
    buildings_path,
    observer_point,
    output_path,
    title
):

    with rasterio.open(ortho_path) as src:
        ortho = src.read(1)
        bounds = src.bounds

    with rasterio.open(viewshed_path) as src:
        viewshed = src.read(1)

    buildings = gpd.read_file(buildings_path)

    extent = [
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top
    ]

    # Normalize background
    ortho_norm = (ortho - ortho.min()) / (ortho.max() - ortho.min())

    fig, ax = plt.subplots(figsize=(8, 8))

    # Base
    ax.imshow(ortho_norm, cmap="gray", extent=extent)

    # Visible areas
    visible = np.ma.masked_where(viewshed == 0, viewshed)
    ax.imshow(visible, cmap="YlOrRd", alpha=0.75, extent=extent)

    # Building outlines
    buildings.boundary.plot(
        ax=ax,
        color="black",
        linewidth=0.5
    )

    # Observer marker
    ax.scatter(
        observer_point.x,
        observer_point.y,
        c="cyan",
        edgecolors="black",
        s=250,
        zorder=10
    )

    # Direction arrow (simple north arrow)
    arrow_x = bounds.left + (bounds.right - bounds.left) * 0.1
    arrow_y = bounds.top - (bounds.top - bounds.bottom) * 0.1

    ax.annotate(
        "N",
        xy=(arrow_x, arrow_y),
        xytext=(arrow_x, arrow_y - 20),
        arrowprops=dict(facecolor='black', width=2, headwidth=8),
        ha='center',
        fontsize=12,
        fontweight="bold"
    )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")


if __name__ == "__main__":

    ortho_path = "data/raw/task2/OrthoImage_Subset.tif"
    buildings_path = "data/raw/task2/BuildingFootprints.shp"
    observers = gpd.read_file(
        "data/processed/task2/observer_points_3d.shp"
    )

    viewshed_folder = "data/processed/task2/viewsheds/"
    os.makedirs("data/figures/observer_maps/", exist_ok=True)

    for idx, row in observers.iterrows():

        viewshed_path = os.path.join(
            viewshed_folder,
            f"viewshed_observer_{idx}.tif"
        )

        output_path = f"data/figures/observer_maps/Observer_{idx}_Map.png"

        plot_observer_map(
            ortho_path,
            viewshed_path,
            buildings_path,
            row.geometry,
            output_path,
            f"Observer {idx}: 3D Viewshed"
        )