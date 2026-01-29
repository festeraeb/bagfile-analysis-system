#!/usr/bin/env python3
"""Download and ingest EMAG2 magnetic anomaly data for the Great Lakes.

Behavior:
- Download EMAG2 (or use a local file) and extract points/grid
- Restrict to Great Lakes bbox (configurable)
- Grid the points to a regular lat/lon raster (2-arc-minute default) if needed
- Write a GeoTIFF subset for the bbox and optionally tile into patches for training

Usage examples:
  python scripts/ingest_emag2.py --download --out-dir magnetic_data/grids/emag2 --bbox -92.5 41.0 -75.0 49.0
  python scripts/ingest_emag2.py --input-file /path/to/emag2.csv.zip --out-dir magnetic_data/grids/emag2

Notes:
- Requires: requests, rasterio, scipy
- If the source is a CSV of lon,lat,anomaly the script will grid it via scipy.interpolate.griddata
"""
from pathlib import Path
import argparse
import zipfile
import sys
import tempfile
import shutil

DEFAULT_BBOX = (-92.5, 41.0, -75.0, 49.0)  # lonmin, latmin, lonmax, latmax (Great Lakes region)
DEFAULT_RES_DEG = 2.0 / 60.0  # 2 arc-minutes in degrees (~0.033333)

EMAG2_ZIP_URL = 'https://www.ngdc.noaa.gov/mgg/global/geomag/EMAG2/EMAG2v3/EMAG2v3.csv.zip'


def ensure_imports():
    try:
        import requests, numpy as np, rasterio
        from scipy.interpolate import griddata
    except Exception as e:
        print('Missing dependencies:', e)
        print('Install with: pip install requests numpy rasterio scipy')
        sys.exit(1)


def download_emag2(dest: Path):
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    print('Downloading EMAG2 from NCEI (this can be large, ~1-2 GB zipped)')
    r = requests.get(EMAG2_ZIP_URL, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as fh:
        for chunk in r.iter_content(1024*1024):
            fh.write(chunk)
    print('Downloaded to', dest)
    return dest


def extract_zip(zip_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(zip_path), 'r') as z:
        z.extractall(str(out_dir))
    print('Extracted zip to', out_dir)
    # try to find a csv inside
    candidates = list(out_dir.rglob('*.csv'))
    if candidates:
        print('Found CSV:', candidates[0])
        return candidates[0]
    # fall back to first file
    files = list(out_dir.iterdir())
    return files[0] if files else None


def grid_csv_to_geotiff(csv_path: Path, out_tif: Path, bbox, res_deg=DEFAULT_RES_DEG):
    import numpy as np
    from scipy.interpolate import griddata
    import csv
    import rasterio
    from rasterio.transform import from_origin

    lonmin, latmin, lonmax, latmax = bbox
    print(f'Gridding CSV {csv_path} to {out_tif} with resolution {res_deg} deg')

    lons = []
    lats = []
    vals = []
    with csv_path.open('r', encoding='utf-8', errors='replace') as fh:
        reader = csv.reader(fh)
        # try to detect header
        first = next(reader)
        # guess indices for lon/lat/val
        header = [c.lower() for c in first]
        if 'lon' in ''.join(header) or 'longitude' in ''.join(header):
            # it's a header row
            keys = header
            i_lon = next((i for i,k in enumerate(keys) if 'lon' in k or 'long' in k), 0)
            i_lat = next((i for i,k in enumerate(keys) if 'lat' in k), 1)
            i_val = next((i for i,k in enumerate(keys) if 'anom' in k or 'value' in k or 'mag' in k), 2)
            # read remaining
            for row in reader:
                try:
                    lon = float(row[i_lon]); lat = float(row[i_lat]); v = float(row[i_val])
                except Exception:
                    continue
                if lon < lonmin or lon > lonmax or lat < latmin or lat > latmax:
                    continue
                lons.append(lon); lats.append(lat); vals.append(v)
        else:
            # assume columns lon,lat,value
            try:
                lon = float(first[0]); lat = float(first[1]); v = float(first[2])
                if lon >= lonmin and lon <= lonmax and lat >= latmin and lat <= latmax:
                    lons.append(lon); lats.append(lat); vals.append(v)
            except Exception:
                pass
            for row in reader:
                try:
                    lon = float(row[0]); lat = float(row[1]); v = float(row[2])
                except Exception:
                    continue
                if lon < lonmin or lon > lonmax or lat < latmin or lat > latmax:
                    continue
                lons.append(lon); lats.append(lat); vals.append(v)

    if not vals:
        raise RuntimeError('No points found in CSV within bbox')

    pts = np.vstack([lons, lats]).T
    xi = np.arange(lonmin, lonmax + res_deg, res_deg)
    yi = np.arange(latmax, latmin - res_deg, -res_deg)  # top to bottom
    grid_x, grid_y = np.meshgrid(xi, yi)
    print(f'Gridding to size {grid_y.shape} (rows,cols)')

    grid_z = griddata(pts, np.array(vals), (grid_x, grid_y), method='linear')
    # fill nans with nearest
    nanmask = np.isnan(grid_z)
    if nanmask.any():
        grid_z[nanmask] = griddata(pts, np.array(vals), (grid_x[nanmask], grid_y[nanmask]), method='nearest')

    transform = from_origin(xi[0], yi[0], res_deg, res_deg)
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(str(out_tif), 'w', driver='GTiff', height=grid_z.shape[0], width=grid_z.shape[1], count=1, dtype='float32', crs='EPSG:4326', transform=transform) as dst:
        dst.write(grid_z.astype('float32'), 1)
    print('Wrote GeoTIFF', out_tif)
    return out_tif


def tile_geotiff_to_patches(tif_path: Path, out_dir: Path, patch_px=256, stride_px=256):
    import rasterio
    from rasterio.windows import Window
    out_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(str(tif_path)) as src:
        h = src.height; w = src.width
        print(f'Tiling {tif_path} ({w}x{h}) into patches {patch_px} px')
        count = 0
        y = 0
        while y < h:
            x = 0
            while x < w:
                win = Window(x, y, min(patch_px, w - x), min(patch_px, h - y))
                arr = src.read(1, window=win, out_shape=(patch_px, patch_px), resampling=1)
                # save npy patches as images and metadata
                import numpy as np
                name = f'{tif_path.stem}_{y}_{x}.npy'
                np.save(out_dir / name, arr.astype('float32'))
                count += 1
                x += stride_px
            y += stride_px
    print(f'Wrote {count} patches to', out_dir)
    return count


def main():
    ensure_imports()
    p = argparse.ArgumentParser()
    p.add_argument('--download', action='store_true', help='Download EMAG2 zip from NCEI')
    p.add_argument('--input-file', help='Local path to EMAG2 zip or CSV')
    p.add_argument('--out-dir', default='magnetic_data/grids/emag2')
    p.add_argument('--bbox', nargs=4, type=float, default=list(DEFAULT_BBOX), help='lonmin latmin lonmax latmax')
    p.add_argument('--res-deg', type=float, default=DEFAULT_RES_DEG, help='Grid resolution in degrees (default 2 arc-minutes)')
    p.add_argument('--tile-patches', action='store_true', help='Tile output GeoTIFF into numpy patches for training')
    args = p.parse_args()

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Determine source
    if args.input_file:
        src_path = Path(args.input_file)
        if not src_path.exists():
            print('Input file not found:', src_path)
            raise SystemExit(1)
    elif args.download:
        zip_dest = outdir / 'EMAG2v3.csv.zip'
        download_emag2(zip_dest)
        tempd = Path(tempfile.mkdtemp(prefix='emag2_'))
        try:
            csv_path = extract_zip(zip_dest, tempd)
            src_path = csv_path
        finally:
            # keep extracted until we finish
            pass
    else:
        print('Specify --download or --input-file')
        raise SystemExit(1)

    # If a zip or dir was provided, attempt to extract
    if src_path.suffix.lower() in ('.zip',):
        tempd = Path(tempfile.mkdtemp(prefix='emag2_'))
        src_path = extract_zip(src_path, tempd)

    # If it's a CSV, grid it
    if src_path.suffix.lower() in ('.csv', '.txt'):
        tif_out = Path(outdir) / 'emag2_glakes_subset.tif'
        grid_csv_to_geotiff(src_path, tif_out, bbox=tuple(args.bbox), res_deg=args.res_deg)
    else:
        print('Unsupported input file type:', src_path.suffix)
        print('If EMAG2 is provided as a gridded GeoTIFF or netCDF, consider converting it to GeoTIFF first and re-running with --input-file')
        raise SystemExit(1)

    if args.tile_patches:
        tile_out = Path('training/grids/emag2_patches')
        tile_geotiff_to_patches(tif_out, tile_out, patch_px=256, stride_px=256)

    print('Done. You can now add these patches to your training set or analyze the tif in', tif_out)


if __name__ == '__main__':
    main()