#!/usr/bin/env python3
"""Convert MRData ArcGrid (NAmag_origmrg) to GeoTIFF and subset to bbox.
Usage: python scripts/convert_mrdata_grid.py --input-dir magnetic_data/mrdata/NAmag_origmrg/namag_origmrg --out magnetic_data/grids/namag_origmrg.tif --bbox -92.5 41 -75 49
"""
from pathlib import Path
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--bbox', nargs=4, type=float, required=True, help='lonmin latmin lonmax latmax')
    args = p.parse_args()

    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    inp = Path(args.input_dir)
    out = Path(args.out)
    lonmin, latmin, lonmax, latmax = args.bbox

    # Open dataset
    with rasterio.open(str(inp)) as src:
        print('Source CRS:', src.crs)
        print('Source bounds:', src.bounds)
        # transform requested bbox from EPSG:4326 to src.crs
        from rasterio.warp import transform
        xs, ys = transform('EPSG:4326', src.crs, [lonmin, lonmax, lonmax, lonmin], [latmin, latmin, latmax, latmax])
        left = min(xs); right = max(xs); bottom = min(ys); top = max(ys)
        # ensure intersection with source bounds
        left = max(left, src.bounds.left)
        right = min(right, src.bounds.right)
        bottom = max(bottom, src.bounds.bottom)
        top = min(top, src.bounds.top)
        if left >= right or bottom >= top:
            raise RuntimeError('Requested bbox does not intersect source grid')
        window = from_bounds(left, bottom, right, top, src.transform)
        arr = src.read(1, window=window)
        transform = src.window_transform(window)
        meta = src.meta.copy()
        meta.update({'driver':'GTiff','height': arr.shape[0], 'width': arr.shape[1], 'transform': transform, 'count':1, 'dtype':'float32'})
        out.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(str(out), 'w', **meta) as dst:
            dst.write(arr.astype('float32'), 1)
    print('Wrote subset GeoTIFF to', out)

if __name__ == '__main__':
    main()
