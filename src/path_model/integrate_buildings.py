import numpy as np
import rasterio
from rasterio.features import rasterize
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path


COST_PATH = Path("data/processed/cost_surface_task1.tif")
BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
OUTPUT_PATH = Path("data/processed/cost_surface_with_buildings.tif")

OBSTACLE_COST = 1000  # Very high cost to block movement


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

    # Load cost surface
    with rasterio.open(COST_PATH) as dataset:
        cost_surface = dataset.read(1)
        transform = dataset.transform
        reference = dataset
        out_shape = (dataset.height, dataset.width)

    # Load building footprints
    buildings = gpd.read_file(BUILDINGS_PATH)

    # Ensure CRS matches
    if buildings.crs != reference.crs:
        buildings = buildings.to_crs(reference.crs)

    print("Number of buildings:", len(buildings))

    # Rasterize buildings (1 = building, 0 = empty)
    building_raster = rasterize(
        [(geom, 1) for geom in buildings.geometry],
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype=np.uint8
    )

    # Integrate into cost surface
    cost_with_buildings = cost_surface.copy()
    cost_with_buildings[building_raster == 1] = OBSTACLE_COST

    print("Obstacle cells count:", np.sum(building_raster))

    save_raster(
        OUTPUT_PATH,
        reference,
        cost_with_buildings.astype(np.float32)
    )

    # Visualize
    plt.figure(figsize=(8, 6))
    plt.imshow(cost_with_buildings, cmap="viridis")
    plt.title("Cost Surface With Buildings")
    plt.colorbar(label="Movement Cost")
    plt.show()