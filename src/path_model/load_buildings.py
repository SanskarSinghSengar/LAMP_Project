import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path


BUILDINGS_PATH = Path("data/raw/task1/BuildingFootprints.shp")
DEM_PATH = Path("data/raw/task1/DEM_Subset-Original.tif")


if __name__ == "__main__":

    buildings = gpd.read_file(BUILDINGS_PATH)

    print("\n--- Building Data ---")
    print("CRS:", buildings.crs)
    print("Number of buildings:", len(buildings))

    with rasterio.open(DEM_PATH) as dem:
        dem_crs = dem.crs

    print("DEM CRS:", dem_crs)

    # Reproject if needed
    if buildings.crs != dem_crs:
        buildings = buildings.to_crs(dem_crs)

    # Simple visualization
    fig, ax = plt.subplots(figsize=(6, 6))
    buildings.plot(ax=ax, facecolor="none", edgecolor="red")
    plt.title("Building Footprints")
    plt.show()
    