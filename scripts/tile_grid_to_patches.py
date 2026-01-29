#!/usr/bin/env python3
"""Tile a GeoTIFF into 256x256 numpy patches (default)"""
from pathlib import Path
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tif', required=True)
    p.add_argument('--out-dir', default='training/grids/namag_patches')
    p.add_argument('--patch', type=int, default=256)
    p.add_argument('--stride', type=int, default=256)
    args = p.parse_args()

    import rasterio
    from rasterio.windows import Window
    import numpy as np

    tif = Path(args.tif)
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(tif)) as src:
        h = src.height; w = src.width
        count = 0
        y = 0
        while y < h:
            x = 0
            while x < w:
                win_w = min(args.patch, w - x)
                win_h = min(args.patch, h - y)
                win = Window(x, y, win_w, win_h)
                arr = src.read(1, window=win, out_shape=(args.patch, args.patch))
                name = f'{tif.stem}_{y}_{x}.npy'
                np.save(outdir / name, arr.astype('float32'))
                count += 1
                x += args.stride
            y += args.stride
    print(f'Wrote {count} patches to', outdir)

if __name__ == '__main__':
    main()
