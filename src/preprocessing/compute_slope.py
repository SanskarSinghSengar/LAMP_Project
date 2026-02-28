import numpy as np
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path


# Use relative paths (professional practice)
DEM_PATH = Path("data/raw/task1/DEM_Subset-Original.tif")
OUTPUT_PATH = Path("data/processed/slope_task1.tif")


def compute_slope(dem_array, resolution):
    """
    Compute slope in degrees from DEM using central difference method.
    """

    x_res, y_res = resolution

    dzdx = np.gradient(dem_array, axis=1) / x_res
    dzdy = np.gradient(dem_array, axis=0) / y_res

    slope_rad = np.arctan(np.sqrt(dzdx**2 + dzdy**2))
    slope_deg = np.degrees(slope_rad)

    return slope_deg


def save_raster(output_path, reference_dataset, data):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=reference_dataset.crs,
        transform=reference_dataset.transform,
    ) as dst:
        dst.write(data, 1)


if __name__ == "__main__":

    with rasterio.open(DEM_PATH) as dataset:
        dem = dataset.read(1)
        resolution = dataset.res
        reference = dataset

    slope = compute_slope(dem, resolution)

    print("\nSlope Statistics:")
    print("Min slope:", np.min(slope))
    print("Max slope:", np.max(slope))

    save_raster(OUTPUT_PATH, reference, slope.astype(np.float32))

    plt.figure(figsize=(8, 6))
    plt.imshow(slope, cmap="inferno")
    plt.colorbar(label="Slope (degrees)")
    plt.title("Slope Map")
    plt.show()