"""
Wreck Hunter 2000 – BAG File Analysis Module
=============================================
End-to-end: Scan → Classify → Detect → Export KML/KMZ

GUI Application for Windows

Principles:
  - Uses REAL BAG file data only (no synthetic without approval)
  - Original files are NEVER modified
  - Restored data saved separately with full provenance
  - Min detection: 35 ft (adjustable)

Author: Wreck Hunter 2000 Team
Date: 2026-02-09
"""

import sys
import os
import json
import time
import struct
import zipfile
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from io import BytesIO
from typing import Optional, List, Dict, Tuple, Callable
import base64
import re
import threading

# ── Defensive imports ─────────────────────────────────────────────
try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False
    print("WARNING: h5py not available — cannot read BAG files")

try:
    from scipy.ndimage import gaussian_filter, binary_dilation, binary_erosion
    from scipy.ndimage import label as scipy_label
    from scipy.interpolate import griddata
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("WARNING: scipy not available — limited restoration capability")

try:
    # Suppress pyproj warnings about PROJ data
    import os
    os.environ.setdefault('PROJ_NETWORK', 'OFF')
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except (ImportError, Exception) as e:
    PYPROJ_AVAILABLE = False
    print(f"WARNING: pyproj not available — coordinate transforms limited ({e})")

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("ERROR: tkinter not available — GUI cannot start")


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════
DEFAULT_MIN_SIZE_FT = 35.0
DEFAULT_NODATA = 1_000_000.0
DEFAULT_PATCH_SIZE = 128
DEFAULT_MAX_GRID_DIM = 3000
DEFAULT_EXAGGERATION = 1.0
DEDUP_RADIUS_M = 200.0


# ═══════════════════════════════════════════════════════════════════════
# MASK CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════
class MaskClass:
    VALID = 0
    HARD_VOID = 1
    SMOOTHED = 2
    BLEND_ZONE = 3
    SMALL_GAP = 4

    NAMES = {0: 'Valid', 1: 'Hard Void', 2: 'Smoothed',
             3: 'Blend Zone', 4: 'Small Gap'}
    COLORS_RGB = {0: (0, 200, 0), 1: (255, 0, 0), 2: (255, 165, 0),
                  3: (255, 255, 0), 4: (128, 128, 128)}
    COLORS_HEX = {0: '#00c800', 1: '#ff0000', 2: '#ffa500',
                  3: '#ffff00', 4: '#808080'}


# ═══════════════════════════════════════════════════════════════════════
# QUICK COMPONENTS (simplified versions for speed)
# ═══════════════════════════════════════════════════════════════════════

class BAGReader:
    def __init__(self, max_dim=DEFAULT_MAX_GRID_DIM):
        self.max_dim = max_dim

    def read(self, bag_path: str) -> Dict:
        if not H5PY_AVAILABLE:
            raise ImportError("h5py required to read BAG files")

        bag_path = Path(bag_path)
        result = {
            'path': str(bag_path),
            'name': bag_path.stem,
            'grid': None,
            'resolution_m': 8.0,
            'crs_wkt': None,
            'crs_epsg': None,
            'origin_x': None,
            'origin_y': None,
            'nodata': DEFAULT_NODATA,
            'downsample_factor': 1,
        }

        with h5py.File(str(bag_path), 'r') as f:
            elev = f['BAG_root/elevation'][:]
            meta_bytes = f['BAG_root/metadata'][:]

        meta_xml = bytes(meta_bytes).decode('utf-8', errors='ignore')
        grid = elev.astype(np.float32)

        res_matches = re.findall(r'<resolution.*?>([\d.]+)</resolution>', meta_xml)
        if res_matches:
            result['resolution_m'] = min(float(r) for r in res_matches)

        wkt_match = re.search(
            r'<referenceSystemInfo>.*?<code>(.*?)</code>',
            meta_xml, re.DOTALL)
        if wkt_match:
            result['crs_wkt'] = wkt_match.group(1)

        if result['crs_wkt'] and PYPROJ_AVAILABLE:
            try:
                crs = CRS.from_wkt(result['crs_wkt'])
                result['crs_epsg'] = crs.to_epsg()
            except Exception:
                epsg_match = re.search(r'EPSG[:\s]+(\d{4,5})', meta_xml)
                if epsg_match:
                    result['crs_epsg'] = int(epsg_match.group(1))

        # Try multiple patterns for corner/origin coordinates
        # Pattern 1: <cornerPoints>...<pos>
        sw_matches = re.findall(
            r'<cornerPoints>.*?<pos>([\d.\-\s]+)</pos>',
            meta_xml, re.DOTALL)
        if sw_matches:
            coords = sw_matches[0].strip().split()
            if len(coords) >= 2:
                result['origin_x'] = float(coords[0])
                result['origin_y'] = float(coords[1])

        # Pattern 2: <gml:coordinates> (common in NOAA BAG files)
        if result['origin_x'] is None:
            gml_match = re.search(
                r'<gml:coordinates[^>]*>([^<]+)</gml:coordinates>',
                meta_xml)
            if gml_match:
                parts = gml_match.group(1).strip().split()
                if parts:
                    sw = parts[0].split(',')
                    if len(sw) >= 2:
                        result['origin_x'] = float(sw[0])
                        result['origin_y'] = float(sw[1])

        # Pattern 3: <westBoundLongitude>/<southBoundLatitude> (ISO metadata)
        if result['origin_x'] is None:
            west_match = re.search(
                r'<westBoundLongitude>([\d.\-]+)</westBoundLongitude>',
                meta_xml)
            south_match = re.search(
                r'<southBoundLatitude>([\d.\-]+)</southBoundLatitude>',
                meta_xml)
            if west_match and south_match:
                # These are lat/lon, need to handle differently
                result['origin_x'] = float(west_match.group(1))
                result['origin_y'] = float(south_match.group(1))
                result['origin_is_latlon'] = True

        # Pattern 4: Look for any coordinate-like pairs in cornerPoints
        if result['origin_x'] is None:
            corner_match = re.search(
                r'<cornerPoints[^>]*>\s*([\d.\-]+)\s+([\d.\-]+)',
                meta_xml, re.DOTALL)
            if corner_match:
                result['origin_x'] = float(corner_match.group(1))
                result['origin_y'] = float(corner_match.group(2))

        h, w = grid.shape
        if h > self.max_dim or w > self.max_dim:
            factor = max(h // self.max_dim, w // self.max_dim, 1) + 1
            grid = grid[::factor, ::factor]
            result['resolution_m'] *= factor
            result['downsample_factor'] = factor

        result['grid'] = grid
        return result


class MaskAnalyzer:
    def __init__(self, nodata=DEFAULT_NODATA):
        self.nodata = nodata

    def classify(self, grid: np.ndarray) -> np.ndarray:
        classes = np.full(grid.shape, MaskClass.VALID, dtype=np.uint8)
        mask = (grid >= self.nodata) | np.isnan(grid)
        classes[mask] = MaskClass.HARD_VOID
        return classes

    def stats(self, classes: np.ndarray) -> Dict:
        total = classes.size
        return {MaskClass.NAMES[k]: float(np.sum(classes == k) / total * 100)
                for k in range(5)}


class CoordTransformer:
    def __init__(self, bag_info: Dict):
        self.info = bag_info
        self._transformer = None
        if PYPROJ_AVAILABLE and bag_info.get('crs_wkt'):
            try:
                src_crs = CRS.from_wkt(bag_info['crs_wkt'])
                self._transformer = Transformer.from_crs(
                    src_crs, CRS.from_epsg(4326), always_xy=True)
            except Exception:
                if bag_info.get('crs_epsg'):
                    try:
                        self._transformer = Transformer.from_crs(
                            CRS.from_epsg(bag_info['crs_epsg']),
                            CRS.from_epsg(4326), always_xy=True)
                    except Exception:
                        pass

    def pixel_to_latlon(self, row: int, col: int) -> Tuple[float, float]:
        res = self.info['resolution_m']
        ds = self.info.get('downsample_factor') or 1
        ox = self.info.get('origin_x') or 0.0
        oy = self.info.get('origin_y') or 0.0
        is_latlon = self.info.get('origin_is_latlon', False)

        # If origin is already in lat/lon (from ISO metadata), handle differently
        if is_latlon:
            # Origin is lon, lat - convert pixel offset to degrees
            # Approximate: 1 degree lat ~ 111km, 1 degree lon ~ 85km at 45N
            lat = oy + row * res * ds / 111000.0
            lon = ox + col * res * ds / 85000.0
            return lat, lon

        easting = ox + col * res * ds
        northing = oy + row * res * ds

        if self._transformer:
            try:
                lon, lat = self._transformer.transform(easting, northing)
                if -95 < lon < -75 and 40 < lat < 50:
                    return lat, lon
                # Try swapped order (some CRS have axes swapped)
                lat2, lon2 = self._transformer.transform(northing, easting)
                if -95 < lon2 < -75 and 40 < lat2 < 50:
                    return lat2, lon2
            except Exception:
                pass  # Fall through to approximation

        # Fallback: approximate conversion assuming Great Lakes region
        lat = oy + row * res * ds / 111000.0
        lon = ox + col * res * ds / (111000.0 * np.cos(np.radians(45)))
        return lat, lon

    def grid_bounds_latlon(self, grid_shape) -> Dict:
        h, w = grid_shape
        sw = self.pixel_to_latlon(0, 0)
        ne = self.pixel_to_latlon(h - 1, w - 1)
        return {
            'south': min(sw[0], ne[0]),
            'north': max(sw[0], ne[0]),
            'west': min(sw[1], ne[1]),
            'east': max(sw[1], ne[1]),
        }


class AnomalyDetector:
    def __init__(self, min_size_ft=DEFAULT_MIN_SIZE_FT,
                 min_height_m=0.3, cluster_radius_px=15):
        self.min_size_ft = min_size_ft
        self.min_size_m = min_size_ft * 0.3048
        self.min_height_m = min_height_m

    def detect(self, grid: np.ndarray, classes: np.ndarray,
               resolution_m: float, transformer: CoordTransformer) -> List[Dict]:
        valid = classes == MaskClass.VALID
        if not np.any(valid):
            return []

        if SCIPY_AVAILABLE:
            filled = np.where(valid, grid, np.nanmean(grid[valid]))
            background = gaussian_filter(filled.astype(np.float32), sigma=15)
        else:
            background = np.full_like(grid, np.nanmean(grid[valid]))

        deviation = np.abs(grid - background)
        deviation[~valid] = 0

        if not np.any(deviation > 0) or not SCIPY_AVAILABLE:
            return []

        threshold = max(self.min_height_m, np.percentile(deviation[valid], 95))
        anomaly_mask = (deviation > threshold) & valid

        if not np.any(anomaly_mask):
            return []

        labeled, n_clusters = scipy_label(anomaly_mask)

        detections = []
        for i in range(1, n_clusters + 1):
            component = labeled == i
            n_pixels = component.sum()
            size_m = np.sqrt(n_pixels) * resolution_m
            size_ft = size_m / 0.3048

            if size_ft < self.min_size_ft:
                continue

            rows, cols = np.where(component)
            center_r = int(np.mean(rows))
            center_c = int(np.mean(cols))
            lat, lon = transformer.pixel_to_latlon(center_r, center_c)

            if not (40.0 < lat < 50.0 and -93.0 < lon < -75.0):
                continue

            heights = deviation[component]
            max_height = float(np.max(heights))
            mean_height = float(np.mean(heights))

            bbox_h = (rows.max() - rows.min() + 1) * resolution_m
            bbox_w = (cols.max() - cols.min() + 1) * resolution_m
            aspect = max(bbox_h, bbox_w) / max(min(bbox_h, bbox_w), 0.1)

            conf = min(0.95, 0.3 + 0.2 * min(max_height / 2.0, 1.0) +
                        0.2 * min(size_ft / 200.0, 1.0) +
                        0.3 * min(aspect / 5.0, 1.0))

            detections.append({
                'lat': float(lat),
                'lon': float(lon),
                'size_ft': float(size_ft),
                'size_m': float(size_m),
                'max_height_m': max_height,
                'mean_height_m': mean_height,
                'aspect_ratio': float(aspect),
                'confidence': float(conf),
                'bbox_m': [float(bbox_h), float(bbox_w)],
                'source_file': '',
                'n_pixels': int(n_pixels),
            })

        return detections


class KMLGenerator:
    def generate_kml(self, detections: List[Dict], output_path: str) -> str:
        kml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            '<Document>',
            f'<name>Wreck Hunter 2000 Analysis</name>',
            '',
            self._kml_styles(),
        ]

        for i, det in enumerate(detections):
            conf = det['confidence']
            style = 'highConf' if conf > 0.7 else 'mediumConf' if conf > 0.4 else 'lowConf'
            size_ft = det['size_ft']
            bbox = det.get('bbox_m', [0, 0])
            aspect = det.get('aspect_ratio', 1.0)
            shape = 'elongated (vessel?)' if aspect > 3.0 else \
                    'rectangular' if aspect > 1.5 else 'compact (debris?)'

            popup = (
                f'<![CDATA['
                f'<h3>Detection #{i+1}</h3>'
                f'<b>Position:</b> {det["lat"]:.5f}°N, {det["lon"]:.5f}°W<br/>'
                f'<b>Size:</b> {size_ft:.0f} ft ({det["size_m"]:.0f} m)<br/>'
                f'<b>Height:</b> {det["max_height_m"]:.1f} m<br/>'
                f'<b>Shape:</b> {shape}<br/>'
                f'<b>Confidence:</b> {conf*100:.0f}%<br/>'
                f'<b>Source:</b> {det.get("source_file", "?")}'
                f']]>'
            )

            kml_parts.append(
                f'<Placemark>'
                f'<name>#{i+1} ({size_ft:.0f}ft)</name>'
                f'<description>{popup}</description>'
                f'<styleUrl>#{style}</styleUrl>'
                f'<Point><coordinates>{det["lon"]},{det["lat"]},0</coordinates></Point>'
                f'</Placemark>'
            )

        kml_parts.extend(['</Document>', '</kml>'])
        kml_str = '\n'.join(kml_parts)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(kml_str)

        return str(output_path)

    def generate_kmz(self, detections: List[Dict], output_path: str) -> str:
        output_path = Path(output_path)
        kml_path = output_path.with_suffix('.kml')
        self.generate_kml(detections, str(kml_path))

        with zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(kml_path), 'doc.kml')

        return str(output_path)

    def _kml_styles(self):
        return '''<Style id="highConf">
  <IconStyle><scale>1.2</scale>
    <Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href></Icon>
  </IconStyle>
</Style>
<Style id="mediumConf">
  <IconStyle><scale>1.0</scale>
    <Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon>
  </IconStyle>
</Style>
<Style id="lowConf">
  <IconStyle><scale>0.8</scale>
    <Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon>
  </IconStyle>
</Style>'''


# ═══════════════════════════════════════════════════════════════════════
# GUI APPLICATION
# ═══════════════════════════════════════════════════════════════════════

class WreckHunterGui:
    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter required for GUI")

        self.root = tk.Tk()
        self.root.title("Wreck Hunter 2000 – BAG File Analysis")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a2e')

        self.bag_files = []
        self.running = False

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ── Title ────────────────────────────────────────────────────
        title = ttk.Label(main, text="🚢 Wreck Hunter 2000",
                          font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))

        # ── File Selection ───────────────────────────────────────────
        file_frame = ttk.LabelFrame(main, text="📂 File Selection", padding=10)
        file_frame.pack(fill=tk.X, pady=5)

        btn_row = ttk.Frame(file_frame)
        btn_row.pack(fill=tk.X)

        ttk.Button(btn_row, text="📄 Single File",
                   command=self._pick_single).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row, text="📁 Multiple Files",
                   command=self._pick_multiple).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row, text="🔄 Scan Directory",
                   command=self._pick_directory).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row, text="❌ Clear",
                   command=self._clear_files).pack(side=tk.LEFT, padx=3)

        self.file_count_var = tk.StringVar(value="No files selected")
        ttk.Label(file_frame, textvariable=self.file_count_var).pack(anchor=tk.W, pady=5)

        self.file_listbox = tk.Listbox(file_frame, height=5)
        self.file_listbox.pack(fill=tk.X)

        # ── Settings ─────────────────────────────────────────────────
        settings = ttk.LabelFrame(main, text="⚙️ Settings", padding=10)
        settings.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(settings)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="Min Detection Size (ft):").pack(side=tk.LEFT)
        self.min_size_var = tk.DoubleVar(value=DEFAULT_MIN_SIZE_FT)
        ttk.Spinbox(row1, from_=10, to=500, textvariable=self.min_size_var,
                     width=8).pack(side=tk.LEFT, padx=10)

        row2 = ttk.Frame(settings)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="Exaggeration:").pack(side=tk.LEFT)
        self.exag_var = tk.DoubleVar(value=1.0)
        self.exag_scale = ttk.Scale(row2, from_=1.0, to=5.0,
                                     variable=self.exag_var, orient=tk.HORIZONTAL,
                                     length=300, command=self._update_exag_label)
        self.exag_scale.pack(side=tk.LEFT, padx=10)
        self.exag_label = ttk.Label(row2, text="1.0x (realistic)")
        self.exag_label.pack(side=tk.LEFT)

        # ── Run ──────────────────────────────────────────────────────
        self.run_btn = ttk.Button(main, text="▶️  START ANALYSIS",
                                   command=self._start_pipeline)
        self.run_btn.pack(pady=10)

        # ── Progress ─────────────────────────────────────────────────
        prog_frame = ttk.Frame(main)
        prog_frame.pack(fill=tk.X, pady=5)

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(prog_frame, variable=self.progress_var,
                        maximum=100).pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(prog_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=3)

        # ── Log ──────────────────────────────────────────────────────
        log_frame = ttk.LabelFrame(main, text="📋 Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=20, font=('Consolas', 9))
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _update_exag_label(self, val):
        v = float(val)
        desc = 'realistic' if v < 1.5 else \
               'enhanced' if v < 2.5 else 'extreme'
        self.exag_label.configure(text=f"{v:.1f}x ({desc})")

    def _pick_single(self):
        f = filedialog.askopenfilename(
            title="Select BAG File",
            filetypes=[("BAG Files", "*.bag"), ("All Files", "*.*")])
        if f:
            self.bag_files = [f]
            self._update_file_list()

    def _pick_multiple(self):
        files = filedialog.askopenfilenames(
            title="Select BAG Files",
            filetypes=[("BAG Files", "*.bag"), ("All Files", "*.*")])
        if files:
            self.bag_files = list(files)
            self._update_file_list()

    def _pick_directory(self):
        d = filedialog.askdirectory(title="Select Directory")
        if d:
            self.bag_files = sorted(
                str(p) for p in Path(d).rglob('*.bag'))
            self._update_file_list()

    def _clear_files(self):
        self.bag_files = []
        self._update_file_list()

    def _update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for f in self.bag_files:
            self.file_listbox.insert(tk.END, Path(f).name)
        self.file_count_var.set(f"{len(self.bag_files)} files selected")

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _progress(self, cur, total, msg=''):
        pct = cur / max(total, 1) * 100
        self.progress_var.set(pct)
        self.status_var.set(msg)
        self.root.update_idletasks()

    def _start_pipeline(self):
        if not self.bag_files:
            messagebox.showwarning("No Files", "Select BAG files first.")
            return
        if self.running:
            return

        self.running = True
        self.run_btn.configure(state='disabled')
        self.log_text.delete(1.0, tk.END)

        def run():
            try:
                output_dir = str(Path(self.bag_files[0]).parent.parent /
                                  'outputs' / 'pipeline_run')

                self._log("=" * 60)
                self._log("Wreck Hunter 2000 – BAG Analysis Pipeline")
                self._log("=" * 60)
                self._log(f"Min size: {self.min_size_var.get():.0f} ft")
                self._log(f"Exaggeration: {self.exag_var.get():.1f}x")
                self._log(f"Files: {len(self.bag_files)}")
                self._log("")

                os.makedirs(output_dir, exist_ok=True)

                reader = BAGReader()
                analyzer = MaskAnalyzer()
                detector = AnomalyDetector(
                    min_size_ft=self.min_size_var.get())
                kml_gen = KMLGenerator()

                all_detections = []
                n_files = len(self.bag_files)

                for i, bag_path in enumerate(self.bag_files):
                    fname = Path(bag_path).name
                    self._progress(i, n_files, f'Scanning {fname}')
                    self._log(f"[{i+1}/{n_files}] {fname}")

                    try:
                        info = reader.read(bag_path)
                        grid = info['grid']
                        classes = analyzer.classify(grid)
                        transformer = CoordTransformer(info)
                        stats = analyzer.stats(classes)

                        self._log(f"  Grid: {grid.shape} | "
                                  f"Res: {info['resolution_m']:.1f}m")
                        self._log(f"  Valid: {stats['Valid']:.0f}%")

                        dets = detector.detect(
                            grid, classes, info['resolution_m'], transformer)
                        for d in dets:
                            d['source_file'] = fname
                        all_detections.extend(dets)
                        self._log(f"  Detections: {len(dets)}")

                    except Exception as e:
                        self._log(f"  ERROR: {e}")

                self._log("")
                self._log(f"Total detections: {len(all_detections)}")

                # Generate KML/KMZ
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                kml_path = output_dir + f'/detections_{timestamp}.kml'
                kmz_path = output_dir + f'/detections_{timestamp}.kmz'

                kml_gen.generate_kml(all_detections, kml_path)
                kml_gen.generate_kmz(all_detections, kmz_path)

                self._log(f"KML: {kml_path}")
                self._log(f"KMZ: {kmz_path}")
                self._log("")
                self._log("✅ COMPLETE")

                # Open results
                os.startfile(output_dir)

            except Exception as e:
                self._log(f"❌ ERROR: {e}")
                import traceback
                self._log(traceback.format_exc())
            finally:
                self.running = False
                self.run_btn.configure(state='normal')

        threading.Thread(target=run, daemon=True).start()

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if not TKINTER_AVAILABLE:
        print("ERROR: tkinter not available")
        sys.exit(1)

    app = WreckHunterGui()
    app.run()
