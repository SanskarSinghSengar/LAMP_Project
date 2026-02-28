import rasterio
import numpy as np


def compute_difference(raster_3d, raster_2d, output_path):

    print("Loading 3D visibility...")
    with rasterio.open(raster_3d) as src:
        prob3d = src.read(1)
        profile = src.profile.copy()

    print("Loading 2D visibility...")
    with rasterio.open(raster_2d) as src:
        prob2d = src.read(1)

    difference = prob3d - prob2d

    profile["dtype"] = "float32"
    profile["count"] = 1
    profile["compress"] = "lzw"
    profile["nodata"] = 0

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(difference.astype(np.float32), 1)

    print("Difference raster saved.")


if __name__ == "__main__":

    compute_difference(
        "data/processed/task2/visibility_probability.tif",
        "data/processed/task2/visibility_probability_2d.tif",
        "data/processed/task2/visibility_difference.tif"
    )