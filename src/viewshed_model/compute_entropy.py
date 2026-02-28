# src/viewshed_model/compute_entropy.py

import os
import numpy as np
import rasterio


def compute_entropy(probability_raster, output_path):

    print("Loading visibility probability raster...")

    with rasterio.open(probability_raster) as src:
        p = src.read(1).astype(np.float32)
        profile = src.profile.copy()
        nodata = src.nodata

    # Handle nodata mask
    if nodata is not None:
        nodata_mask = (p == nodata)
    else:
        nodata_mask = np.zeros_like(p, dtype=bool)

    # Initialize entropy array
    entropy = np.zeros_like(p, dtype=np.float32)

    # Compute entropy only where 0 < p < 1
    mask = (p > 0) & (p < 1) & (~nodata_mask)

    entropy[mask] = -(
        p[mask] * np.log(p[mask]) +
        (1 - p[mask]) * np.log(1 - p[mask])
    )

    # Preserve nodata pixels
    entropy[nodata_mask] = 0

    profile["dtype"] = "float32"
    profile["nodata"] = 0
    profile["count"] = 1
    profile["compress"] = "lzw"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(entropy, 1)

    print("Entropy raster saved successfully.")


if __name__ == "__main__":

    compute_entropy(
        "data/processed/task2/visibility_probability.tif",
        "data/processed/task2/visibility_entropy.tif"
    )