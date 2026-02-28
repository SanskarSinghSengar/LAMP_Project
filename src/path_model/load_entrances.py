import geopandas as gpd
import rasterio
from pathlib import Path


ENTRANCES_PATH = Path("data/raw/task1/Marks_Brief1.shp")
DEM_PATH = Path("data/raw/task1/DEM_Subset-Original.tif")


if __name__ == "__main__":

    entrances = gpd.read_file(ENTRANCES_PATH)

    print("\n--- Entrance Data ---")
    print("CRS:", entrances.crs)
    print("Number of entrance points:", len(entrances))

    with rasterio.open(DEM_PATH) as dem:
        dem_crs = dem.crs
        transform = dem.transform

    # Ensure CRS match
    if entrances.crs != dem_crs:
        entrances = entrances.to_crs(dem_crs)

    print("\nConverting entrance coordinates to raster indices:")

raster_coords = []

for idx, row in entrances.iterrows():

    geom = row.geometry

    # Handle both Point and MultiPoint
    if geom.geom_type == "Point":
        points = [geom]
    elif geom.geom_type == "MultiPoint":
        points = list(geom.geoms)
    else:
        continue  # skip unexpected geometry

    for pt in points:
        x, y = pt.x, pt.y
        row_idx, col_idx = rasterio.transform.rowcol(transform, x, y)

        raster_coords.append((row_idx, col_idx))
        print(f"Entrance {idx}: Pixel -> ({row_idx}, {col_idx})")

print("\nTotal converted entrances:", len(raster_coords))