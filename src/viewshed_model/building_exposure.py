# src/viewshed_model/building_exposure.py

import os
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.mask import mask


def compute_building_exposure(building_shp, visibility_raster, output_shp):

    print("Loading buildings...")
    buildings = gpd.read_file(building_shp)

    print("Loading visibility raster...")
    with rasterio.open(visibility_raster) as src:
        visibility = src.read(1)
        raster_crs = src.crs

    if buildings.crs != raster_crs:
        print("Reprojecting buildings to raster CRS...")
        buildings = buildings.to_crs(raster_crs)

    exposure_values = []

    with rasterio.open(visibility_raster) as src:

        for idx, row in buildings.iterrows():

            try:
                out_image, out_transform = mask(
                    src,
                    [row.geometry],
                    crop=True
                )

                data = out_image[0]

                # valid_pixels = data[data > 0]

                # if len(valid_pixels) > 0:
                #     exposure = float(np.mean(valid_pixels))
                # else:
                #     exposure = 0.0

                valid_pixels = data[~np.isnan(data)]
                exposure = float(np.mean(valid_pixels)) if len(valid_pixels) > 0 else 0.0

                exposure_values.append(exposure)

            except Exception:
                exposure_values.append(0.0)

    buildings["exposure_index"] = exposure_values

    os.makedirs(os.path.dirname(output_shp), exist_ok=True)

    buildings.to_file(output_shp)

    print("Saved building exposure shapefile.")


if __name__ == "__main__":

    compute_building_exposure(
        building_shp="data/raw/task2/BuildingFootprints.shp",
        visibility_raster="data/processed/task2/visibility_probability.tif",
        output_shp="data/processed/task2/building_exposure.shp"
    )