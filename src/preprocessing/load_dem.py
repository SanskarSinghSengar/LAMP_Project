import rasterio
import matplotlib.pyplot as plt

# 👇 You define the DEM path here
DEM_PATH = "data/raw/task1/DEM_Subset-Original.tif"

with rasterio.open(DEM_PATH) as dataset:
    print("\n----- DEM METADATA -----")
    print("CRS:", dataset.crs)
    print("Width:", dataset.width)
    print("Height:", dataset.height)
    print("Bounds:", dataset.bounds)
    print("Resolution:", dataset.res)
    print("Bands:", dataset.count)

    dem = dataset.read(1)

plt.figure(figsize=(8,6))
plt.imshow(dem, cmap="terrain")
plt.colorbar(label="Elevation (m)")
plt.title("DEM")
plt.show()