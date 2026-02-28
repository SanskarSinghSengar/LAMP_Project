import os
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np


def plot_single_observer_viewshed(
    ortho_path,
    viewshed_raster,
    observer_geom,
    output_png,
    title
):

    with rasterio.open(ortho_path) as ortho_src:
        ortho = ortho_src.read(1)
        ortho_transform = ortho_src.transform
        ortho_bounds = ortho_src.bounds

    with rasterio.open(viewshed_raster) as vs_src:
        viewshed = vs_src.read(1)
        vs_bounds = vs_src.bounds

    extent = [
        ortho_bounds.left,
        ortho_bounds.right,
        ortho_bounds.bottom,
        ortho_bounds.top
    ]

    plt.figure(figsize=(10, 8))

    # Plot orthophoto using spatial extent
    plt.imshow(ortho, cmap="gray", extent=extent)

    # Mask non-visible
    visible_mask = np.ma.masked_where(viewshed == 0, viewshed)

    plt.imshow(
        visible_mask,
        cmap="Reds",
        alpha=0.6,
        extent=extent
    )

    # Plot observer in real-world coordinates
    plt.scatter(
        observer_geom.x,
        observer_geom.y,
        c="cyan",
        edgecolors="black",
        s=150,
        zorder=5
    )

    plt.title(title)
    plt.xlabel("Easting")
    plt.ylabel("Northing")

    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.close()

    print(f"Saved: {output_png}")


if __name__ == "__main__":

    observers = gpd.read_file(
        "data/processed/task2/observer_points_3d.shp"
    )

    ortho_path = "data/raw/task2/OrthoImage_Subset.tif"
    viewshed_folder = "data/processed/task2/viewsheds/"

    os.makedirs("data/figures/individual/", exist_ok=True)

    for idx, row in observers.iterrows():

        vs_path = os.path.join(
            viewshed_folder,
            f"viewshed_observer_{idx}.tif"
        )

        output_path = f"data/figures/individual/observer_{idx}.png"

        plot_single_observer_viewshed(
            ortho_path,
            vs_path,
            row.geometry,
            output_path,
            f"Observer {idx} 3D Viewshed"
        )