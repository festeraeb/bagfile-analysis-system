#!/usr/bin/env python3
"""Average multiple model probability GeoTIFFs into an ensemble probability raster."""
from pathlib import Path
import numpy as np
import rasterio


def main():
    outdir = Path('predictions')
    prob_files = sorted(outdir.glob('*_prob.tif'))
    if not prob_files:
        print('No _prob.tif files found in', outdir)
        return
    print('Found prob files:', [p.name for p in prob_files])

    sum_prob = None
    count = 0
    meta = None
    # Use the first raster as the target grid and resample others to it if necessary
    target_profile = None
    for i, f in enumerate(prob_files):
        with rasterio.open(str(f)) as src:
            arr = src.read(1).astype('float32')
            # Initialize target profile from the first file
            if i == 0:
                target_profile = src.profile.copy()
                meta = src.meta.copy()
                sum_prob = np.zeros_like(arr)
                arr = np.nan_to_num(arr, nan=0.0)
                sum_prob += arr
                count += 1
                continue

        # For subsequent files, open and reproject to target_profile
        with rasterio.open(str(f)) as src:
            from rasterio.warp import reproject, Resampling
            dst_arr = np.zeros((target_profile['height'], target_profile['width']), dtype='float32')
            reproject(
                source=src.read(1),
                destination=dst_arr,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=target_profile['transform'],
                dst_crs=target_profile['crs'],
                resampling=Resampling.bilinear,
                num_threads=2
            )
            dst_arr = np.nan_to_num(dst_arr, nan=0.0)
            sum_prob += dst_arr
            count += 1

    if count == 0:
        print('No probability rasters processed')
        return
    ensemble = sum_prob / float(count)

    out_path = outdir / 'ensemble_prob.tif'
    meta.update({'dtype':'float32','count':1})
    with rasterio.open(str(out_path), 'w', **meta) as dst:
        dst.write(ensemble.astype('float32'), 1)
    print('Wrote ensemble to', out_path)

if __name__ == '__main__':
    main()
