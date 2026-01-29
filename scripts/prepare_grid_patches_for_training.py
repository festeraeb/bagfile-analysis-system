#!/usr/bin/env python3
"""Convert tiled grid numpy patches into training image/label pairs.
- Finds files in `training/grids/<prefix>/*/*.npy` or `training/grids/<prefix>/*.npy`
- For each patch creates `{stem}_image.npy` and `{stem}_label.npy` where label is all zeros (background)
- Writes output into `training/grids/<prefix>_for_training/`
"""
from pathlib import Path
import numpy as np
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in-dir', required=True)
    p.add_argument('--out-dir', default=None)
    p.add_argument('--force', action='store_true')
    args = p.parse_args()

    indir = Path(args.in_dir)
    if not indir.exists():
        print('Input dir not found:', indir)
        return
    outdir = Path(args.out_dir) if args.out_dir else indir.parent / (indir.stem + '_for_training')
    outdir.mkdir(parents=True, exist_ok=True)

    files = sorted([f for f in indir.glob('*.npy') if f.is_file()])
    if not files:
        print('No .npy patches found in', indir)
        return

    count = 0
    for f in files:
        stem = f.stem
        img = np.load(f).astype(np.float32)
        # if single-channel, expand dims to (1,H,W) when saved as *_image.npy
        if img.ndim == 2:
            img_out = img.astype(np.float32)
        else:
            img_out = img.astype(np.float32)
        label = np.zeros((img_out.shape[-2], img_out.shape[-1]), dtype=np.uint8)
        # write with suffixes
        img_path = outdir / (stem + '_image.npy')
        lab_path = outdir / (stem + '_label.npy')
        if img_path.exists() and lab_path.exists() and not args.force:
            continue
        np.save(img_path, img_out)
        np.save(lab_path, label)
        count += 1
    print(f'Wrote {count} image/label pairs to', outdir)

if __name__ == '__main__':
    main()
