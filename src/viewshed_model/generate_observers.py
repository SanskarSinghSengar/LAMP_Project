# src/viewshed_model/generate_observers.py

import os
import rasterio
import geopandas as gpd
import numpy as np

EYE_HEIGHT = 1.65


def extract_coordinates(geometry):
    """
    Handles Point and MultiPoint geometries.
    Returns list of (x, y) tuples.
    """
    coords = []

    if geometry.geom_type == "Point":
        coords.append((geometry.x, geometry.y))

    elif geometry.geom_type == "MultiPoint":
        for point in geometry.geoms:
            coords.append((point.x, point.y))

    return coords


def sample_dsm_at_points(dsm_path, points_shp):

    print("Loading DSM...")
    with rasterio.open(dsm_path) as src:
        dsm = src.read(1)
        crs = src.crs

        print("Loading observer points...")
        gdf = gpd.read_file(points_shp)

        if gdf.crs != crs:
            print("Reprojecting observer points to match DSM CRS...")
            gdf = gdf.to_crs(crs)

        new_rows = []

        for _, row in gdf.iterrows():
            coords_list = extract_coordinates(row.geometry)

            for x, y in coords_list:
                try:
                    r, c = src.index(x, y)

                    if (0 <= r < dsm.shape[0]) and (0 <= c < dsm.shape[1]):
                        terrain_elev = dsm[r, c]
                        observer_elev = terrain_elev + EYE_HEIGHT

                        new_rows.append({
                            **row.drop("geometry"),
                            "terrain_z": terrain_elev,
                            "observer_z": observer_elev,
                            "geometry": gpd.points_from_xy([x], [y])[0]
                        })

                except Exception:
                    continue

    new_gdf = gpd.GeoDataFrame(new_rows, crs=crs)

    return new_gdf


def generate_3d_observers(dsm_path, marks_shp_path, output_path):

    gdf = sample_dsm_at_points(dsm_path, marks_shp_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("Saving 3D observer layer...")
    gdf.to_file(output_path)

    print("Observer generation complete.")
    print(f"Total valid observer points: {len(gdf)}")


if __name__ == "__main__":

    generate_3d_observers(
        dsm_path="data/processed/task2/dsm_task2.tif",
        marks_shp_path="data/raw/task2/Marks_Brief2.shp",
        output_path="data/processed/task2/observer_points_3d.shp"
    )