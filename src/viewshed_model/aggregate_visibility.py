# src/viewshed_model/aggregate_visibility.py

import os
import numpy as np
import rasterio


def aggregate_viewsheds(input_folder, output_folder):

    print("Reading viewshed rasters...")

    viewshed_files = sorted([
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.endswith(".tif")
    ])

    if len(viewshed_files) == 0:
        print("No viewshed rasters found.")
        return

    print(f"Found {len(viewshed_files)} viewsheds.")

    with rasterio.open(viewshed_files[0]) as src:
        profile = src.profile.copy()
        base_shape = src.read(1).shape

    visibility_stack = np.zeros(base_shape, dtype=np.float32)

    for vf in viewshed_files:
        with rasterio.open(vf) as src:
            data = src.read(1).astype(np.float32)
            visibility_stack += data

    visibility_count = visibility_stack
    visibility_probability = visibility_stack / len(viewshed_files)

    os.makedirs(output_folder, exist_ok=True)

    # ---- Save count ----
    count_profile = profile.copy()
    count_profile["dtype"] = "float32"
    count_profile["nodata"] = 0

    with rasterio.open(
        os.path.join(output_folder, "visibility_count.tif"),
        "w",
        **count_profile
    ) as dst:
        dst.write(visibility_count, 1)

    print("Saved visibility_count.tif")

    # ---- Save probability ----
    prob_profile = profile.copy()
    prob_profile["dtype"] = "float32"
    prob_profile["nodata"] = 0

    with rasterio.open(
        os.path.join(output_folder, "visibility_probability.tif"),
        "w",
        **prob_profile
    ) as dst:
        dst.write(visibility_probability, 1)

    print("Saved visibility_probability.tif")

    print("Aggregation complete.")


if __name__ == "__main__":

    aggregate_viewsheds(
        input_folder="data/processed/task2/viewsheds/",
        output_folder="data/processed/task2/"
    )