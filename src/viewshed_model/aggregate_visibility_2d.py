import os
import rasterio
import numpy as np


def aggregate_viewsheds(input_folder, output_count, output_probability):

    print("Reading 2D viewshed rasters...")

    files = sorted([
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.endswith(".tif")
    ])

    if len(files) == 0:
        print("No viewshed rasters found.")
        return

    print(f"Found {len(files)} viewsheds.")

    with rasterio.open(files[0]) as src:
        profile = src.profile.copy()
        rows, cols = src.shape
        visibility_sum = np.zeros((rows, cols), dtype=np.float32)

    for f in files:
        with rasterio.open(f) as src:
            visibility_sum += src.read(1)

    visibility_probability = visibility_sum / len(files)

    profile_count = profile.copy()
    profile_count["dtype"] = "float32"
    profile_count["count"] = 1
    profile_count["compress"] = "lzw"
    profile_count["nodata"] = 0

    profile_prob = profile_count.copy()

    with rasterio.open(output_count, "w", **profile_count) as dst:
        dst.write(visibility_sum, 1)

    with rasterio.open(output_probability, "w", **profile_prob) as dst:
        dst.write(visibility_probability, 1)

    print("2D aggregation complete.")


if __name__ == "__main__":

    aggregate_viewsheds(
        input_folder="data/processed/task2/viewsheds_2d/",
        output_count="data/processed/task2/visibility_count_2d.tif",
        output_probability="data/processed/task2/visibility_probability_2d.tif"
    )