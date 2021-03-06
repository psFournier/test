import rasterio
import numpy as np

# src = rasterio.open('/d/pfournie/Documents/ai4geo/data/SemcityTLS_DL/GT_3_4_7_8.tif')
src = rasterio.open('/home/pierre/Documents/ONERA/ai4geo/semcity_merged/GT_3_4_7_8.tif')
img = src.read(out_dtype=np.uint8)
print(np.unique(img.reshape(img.shape[0], -1), axis=1, return_counts=True))