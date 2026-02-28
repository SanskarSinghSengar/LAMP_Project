# src/viewshed_model/compute_viewshed_2d.py

import os
import numpy as np
import rasterio
import geopandas as gpd
from math import sqrt


def compute_viewshed_for_observer(dem, observer_row, observer_col, observer_z, nodata_value):
    """
    Compute binary 2D terrain-only viewshed using DEM.
    Buildings are NOT included.
    """

    rows, cols = dem.shape
    viewshed = np.zeros((rows, cols), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):

            # Skip nodata
            if dem[r, c] == nodata_value:
                continue

            # Observer cell
            if r == observer_row and c == observer_col:
                viewshed[r, c] = 1
                continue

            dr = r - observer_row
            dc = c - observer_col
            distance = sqrt(dr**2 + dc**2)

            if distance == 0:
                continue

            target_z = dem[r, c]
            slope = (target_z - observer_z) / distance

            visible = True
            steps = int(max(abs(dr), abs(dc)))

            for step in range(1, steps):

                ir = int(observer_row + dr * step / steps)
                ic = int(observer_col + dc * step / steps)

                if ir < 0 or ir >= rows or ic < 0 or ic >= cols:
                    continue

                if dem[ir, ic] == nodata_value:
                    continue

                intermediate_distance = sqrt(
                    (ir - observer_row)**2 + (ic - observer_col)**2
                )

                expected_z = observer_z + slope * intermediate_distance

                if dem[ir, ic] > expected_z:
                    visible = False
                    break

            if visible:
                viewshed[r, c] = 1

    return viewshed


def run_viewshed_2d(dem_path, observers_path, output_dir):

    print("Loading DEM (terrain-only)...")

    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        profile = src.profile.copy()
        nodata_value = src.nodata

    print("Loading observers...")
    observers = gpd.read_file(observers_path)

    os.makedirs(output_dir, exist_ok=True)

    for idx, row in observers.iterrows():

        with rasterio.open(dem_path) as src:
            observer_row, observer_col = src.index(
                row.geometry.x,
                row.geometry.y
            )

        observer_z = row["observer_z"]

        print(f"Computing 2D viewshed for observer {idx}...")

        viewshed = compute_viewshed_for_observer(
            dem,
            observer_row,
            observer_col,
            observer_z,
            nodata_value
        )

        output_path = os.path.join(
            output_dir,
            f"viewshed_observer_{idx}.tif"
        )

        # Clean profile for binary output
        out_profile = profile.copy()
        out_profile["dtype"] = "uint8"
        out_profile["count"] = 1
        out_profile["compress"] = "lzw"
        out_profile["nodata"] = 0

        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(viewshed, 1)

        print(f"Saved: {output_path}")

    print("2D terrain-only viewsheds computed successfully.")


if __name__ == "__main__":

    run_viewshed_2d(
        dem_path="data/raw/task2/DEM_Subset-Original.tif",
        observers_path="data/processed/task2/observer_points_3d.shp",
        output_dir="data/processed/task2/viewsheds_2d/"
    )