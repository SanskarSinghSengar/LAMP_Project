import rasterio
import numpy as np

def compute_difference(dsm_prob, dem_prob, output_path):

    with rasterio.open(dsm_prob) as src:
        dsm = src.read(1)
        profile = src.profile.copy()

    with rasterio.open(dem_prob) as src:
        dem = src.read(1)

    difference = dsm - dem

    profile["dtype"] = "float32"
    profile["nodata"] = 0

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(difference, 1)

    print("Difference map saved.")

if __name__ == "__main__":

    compute_difference(
        "data/processed/task2/visibility_probability.tif",
        "data/processed/task2/visibility_probability_2d.tif",
        "data/processed/task2/visibility_difference.tif"
    )