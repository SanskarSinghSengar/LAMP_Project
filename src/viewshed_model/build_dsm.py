# src/viewshed_model/build_dsm.py

import os
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.features import rasterize
import geopandas as gpd


def load_raster(path):
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        profile = src.profile
    return data, profile


def save_raster(path, data, profile):
    profile.update(
        dtype="float32",
        count=1,
        compress="lzw"
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)


def compute_building_height_delta(dem_original, dem_with_buildings):
    delta = dem_with_buildings - dem_original
    delta[delta < 0] = 0  # Remove negative artifacts
    return delta


def clip_to_roi(raster_data, profile, roi_shapefile):
    roi = gpd.read_file(roi_shapefile)

    with rasterio.MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(raster_data, 1)
            out_image, out_transform = mask(dataset, roi.geometry, crop=True)

    profile.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })

    return out_image[0], profile


def rasterize_buildings(building_shp, reference_profile):
    gdf = gpd.read_file(building_shp)
    shapes = [(geom, 1) for geom in gdf.geometry]

    building_mask = rasterize(
        shapes,
        out_shape=(reference_profile["height"], reference_profile["width"]),
        transform=reference_profile["transform"],
        fill=0,
        dtype="float32"
    )

    return building_mask


def build_dsm(dem_original_path,
              dem_with_buildings_path,
              building_shp_path,
              output_dir,
              roi_shapefile=None):

    print("Loading DEMs...")
    dem_original, profile = load_raster(dem_original_path)
    dem_with_buildings, _ = load_raster(dem_with_buildings_path)

    print("Computing building height delta...")
    height_delta = compute_building_height_delta(dem_original, dem_with_buildings)

    print("Rasterizing building footprints...")
    building_mask = rasterize_buildings(building_shp_path, profile)

    print("Validating obstruction consistency...")
    obstruction_check = height_delta * building_mask

    if np.max(obstruction_check) == 0:
        print("Warning: No building height detected.")
    else:
        print("Building height successfully detected.")

    dsm = dem_with_buildings.copy()

    if roi_shapefile:
        print("Clipping to ROI...")
        dsm, profile = clip_to_roi(dsm, profile, roi_shapefile)

    os.makedirs(output_dir, exist_ok=True)

    print("Saving DSM...")
    save_raster(os.path.join(output_dir, "dsm_task2.tif"), dsm, profile)

    print("Saving building height delta...")
    save_raster(os.path.join(output_dir, "building_height_delta.tif"),
                height_delta,
                profile)

    print("DSM construction complete.")


if __name__ == "__main__":

    build_dsm(
        dem_original_path="data/raw/task2/DEM_Subset-Original.tif",
        dem_with_buildings_path="data/raw/task2/DEM_Subset-WithBuildings.tif",
        building_shp_path="data/raw/task2/BuildingFootprints.shp",
        output_dir="data/processed/task2/",
        roi_shapefile=None  # Provide ROI shapefile if available
    )