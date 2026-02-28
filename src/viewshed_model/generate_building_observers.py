# src/viewshed_model/generate_building_observers.py

import os
import rasterio
import geopandas as gpd
import numpy as np

EYE_HEIGHT = 1.65


def generate_building_centroid_observers(
    building_shp,
    dsm_path,
    output_path
):

    print("Loading buildings...")
    buildings = gpd.read_file(building_shp)

    print("Computing centroids...")
    buildings["geometry"] = buildings.geometry.centroid

    print("Loading DSM...")
    with rasterio.open(dsm_path) as src:
        dsm = src.read(1)
        crs = src.crs

        if buildings.crs != crs:
            print("Reprojecting buildings to match DSM CRS...")
            buildings = buildings.to_crs(crs)

        observer_rows = []

        for idx, row in buildings.iterrows():

            x, y = row.geometry.x, row.geometry.y

            try:
                r, c = src.index(x, y)

                if 0 <= r < dsm.shape[0] and 0 <= c < dsm.shape[1]:

                    terrain_z = dsm[r, c]
                    observer_z = terrain_z + EYE_HEIGHT

                    observer_rows.append({
                        "building_id": idx,
                        "terrain_z": float(terrain_z),
                        "observer_z": float(observer_z),
                        "geometry": row.geometry
                    })

            except Exception:
                continue

    observers_gdf = gpd.GeoDataFrame(observer_rows, crs=crs)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    observers_gdf.to_file(output_path)

    print("Building centroid observers saved.")
    print(f"Total observers generated: {len(observers_gdf)}")


if __name__ == "__main__":

    generate_building_centroid_observers(
        building_shp="data/raw/task2/BuildingFootprints.shp",
        dsm_path="data/processed/task2/dsm_task2.tif",
        output_path="data/processed/task2/observer_building_centroids_3d.shp"
    )