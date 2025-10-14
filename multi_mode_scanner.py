""""""

Multi-Mode Enhanced Wreck ScannerMulti-Mode Enhanced Wreck Scanner

Flexible scanning system with multiple detection strategiesFlexible scanning system with multiple detection strategies

""""""

from pathlib import Path

from typing import Dict, List, Tuple, Optional, Anyimport os

from dataclasses import dataclassimport sys

from enum import Enumfrom pathlib import Path

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutorfrom typing import Dict, List, Tuple, Optional, Any

from rasterio.windows import Windowfrom dataclasses import dataclass

from pyproj import Transformerfrom enum import Enum

import logging

# Import our existing modulesimport time

sys.path.append(str(Path(__file__).parent))import threading

from enhanced_wreck_scanner import WreckSignatureDetector, ScanConfigfrom concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from scrub_detection_engine import ScrubDetectionEngineimport multiprocessing as mp



try:import numpy as np

    from pdf_pattern_analyzer import PDFPatternAnalyzerimport pandas as pd

    PDF_AVAILABLE = Trueimport rasterio

except:from rasterio.windows import Window

    PDF_AVAILABLE = Falsefrom pyproj import Transformer

import cv2



class ScanMode(Enum):# Import our existing modules

    """Available scanning modes"""sys.path.append(str(Path(__file__).parent))

    FULL_SCAN = "full"           # Complete pixel-by-pixel analysisfrom enhanced_wreck_scanner import WreckSignatureDetector, ScanConfig

    QUICK_SCAN = "quick"         # Spot sampling at intervalsfrom scrub_detection_engine import ScrubDetectionEngine

    PDF_GUIDED = "pdf_guided"    # Use PDF analysis to focus areas

    HYBRID = "hybrid"            # Combine PDF guidance with spot samplingtry:

    TARGETED = "targeted"        # Scan specific coordinates only    from pdf_pattern_analyzer import PDFPatternAnalyzer

    PDF_AVAILABLE = True

except:

@dataclass    PDF_AVAILABLE = False

class ScanStrategy:

    """Configuration for different scanning strategies"""

    mode: ScanModeclass ScanMode(Enum):

    sample_interval_m: float = 15.0    # For quick scan - distance between samples    """Available scanning modes"""

    sample_size_m: float = 1.0         # Size of each sample area    FULL_SCAN = "full"           # Complete pixel-by-pixel analysis

    detection_box_m: float = 500.0     # Box size when anomaly detected    QUICK_SCAN = "quick"         # Spot sampling at intervals

    overlap_ratio: float = 0.3         # Overlap between detection boxes    PDF_GUIDED = "pdf_guided"    # Use PDF analysis to focus areas

    confidence_threshold: float = 0.6   # Minimum confidence to expand search    HYBRID = "hybrid"            # Combine PDF guidance with spot sampling

    max_workers: int = 4               # Parallel processing    TARGETED = "targeted"        # Scan specific coordinates only

    use_gpu: bool = False              # GPU acceleration if available



@dataclass

class MultiModeScanner:class ScanStrategy:

    """Enhanced scanner with multiple detection strategies"""    """Configuration for different scanning strategies"""

        mode: ScanMode

    def __init__(self, base_config: ScanConfig):    sample_interval_m: float = 15.0    # For quick scan - distance between samples

        self.base_config = base_config    sample_size_m: float = 1.0         # Size of each sample area

        self.setup_logging()    detection_box_m: float = 500.0     # Box size when anomaly detected

            overlap_ratio: float = 0.3         # Overlap between detection boxes

        # Initialize detection engines    confidence_threshold: float = 0.6   # Minimum confidence to expand search

        self.detector = WreckSignatureDetector(base_config)    max_workers: int = 4               # Parallel processing

        self.scrub_engine = ScrubDetectionEngine()    use_gpu: bool = False              # GPU acceleration if available

        

        # PDF analyzer (if available)

        self.pdf_analyzer = PDFPatternAnalyzer() if PDF_AVAILABLE else Noneclass MultiModeScanner:

            """Enhanced scanner with multiple detection strategies"""

        # Results storage    

        self.scan_results = []    def __init__(self, base_config: ScanConfig):

        self.pdf_features = []        self.base_config = base_config

        self.detection_summary = {        self.setup_logging()

            'total_area_scanned_km2': 0.0,        

            'total_tiles_analyzed': 0,        # Initialize detection engines

            'wreck_detections': 0,        self.detector = WreckSignatureDetector(base_config)

            'obstruction_detections': 0,        self.scrub_engine = ScrubDetectionEngine()

            'redaction_detections': 0,        

            'high_confidence_areas': [],        # PDF analyzer (if available)

            'scan_time_seconds': 0.0,        self.pdf_analyzer = PDFPatternAnalyzer() if PDF_AVAILABLE else None

            'scan_mode_used': None        

        }        # Results storage

                self.scan_results = []

    def setup_logging(self):        self.pdf_features = []

        """Setup logging"""        self.detection_summary = {

        logging.basicConfig(level=logging.INFO)            'total_area_scanned_km2': 0.0,

        self.logger = logging.getLogger(__name__)            'total_tiles_analyzed': 0,

                'wreck_detections': 0,

    def run_comprehensive_scan(self, bag_files: List[str],             'obstruction_detections': 0,

                             strategy: ScanStrategy,            'redaction_detections': 0,

                             pdf_dir: Optional[str] = None) -> Dict[str, Any]:            'high_confidence_areas': [],

        """            'scan_time_seconds': 0.0,

        Run comprehensive scan using selected strategy            'scan_mode_used': None

        """        }

        self.logger.info(f"Starting {strategy.mode.value} scan of {len(bag_files)} files")        

        start_time = time.time()    def setup_logging(self):

                """Setup logging"""

        # Step 1: PDF Analysis (if available and requested)        logging.basicConfig(level=logging.INFO)

        if pdf_dir and self.pdf_analyzer and strategy.mode in [ScanMode.PDF_GUIDED, ScanMode.HYBRID]:        self.logger = logging.getLogger(__name__)

            pass  # omitted for brevity    

            def run_comprehensive_scan(self, bag_files: List[str], 

        # Step 2: Choose scanning approach                             strategy: ScanStrategy,

        if strategy.mode == ScanMode.FULL_SCAN:                             pdf_dir: Optional[str] = None) -> Dict[str, Any]:

            pass  # omitted for brevity        """

        elif strategy.mode == ScanMode.QUICK_SCAN:        Run comprehensive scan using selected strategy

            pass  # omitted for brevity        """

        elif strategy.mode == ScanMode.PDF_GUIDED:        self.logger.info(f"Starting {strategy.mode.value} scan of {len(bag_files)} files")

            pass  # omitted for brevity        start_time = time.time()

        elif strategy.mode == ScanMode.HYBRID:        

            pass  # omitted for brevity        # Step 1: PDF Analysis (if available and requested)

        elif strategy.mode == ScanMode.TARGETED:        if pdf_dir and self.pdf_analyzer and strategy.mode in [ScanMode.PDF_GUIDED, ScanMode.HYBRID]:

            pass  # omitted for brevity            self.logger.info("Analyzing PDFs for guidance...")

        else:            pdf_results = self.pdf_analyzer.analyze_pdf_directory(pdf_dir)

            pass  # omitted for brevity            self.pdf_features = self._extract_priority_areas(pdf_results)

                    self.logger.info(f"Found {len(self.pdf_features)} priority areas from PDFs")

        # Step 3: Compile final results        

        scan_time = time.time() - start_time        # Step 2: Choose scanning approach

        self.detection_summary.update({        if strategy.mode == ScanMode.FULL_SCAN:

            'scan_time_seconds': scan_time,            results = self._full_scan(bag_files, strategy)

            'scan_mode_used': strategy.mode.value,        elif strategy.mode == ScanMode.QUICK_SCAN:

            'total_tiles_analyzed': len([])  # placeholder            results = self._quick_scan(bag_files, strategy)

        })        elif strategy.mode == ScanMode.PDF_GUIDED:

                    results = self._pdf_guided_scan(bag_files, strategy)

        # Step 4: Classify detections        elif strategy.mode == ScanMode.HYBRID:

        classified_results = []  # placeholder            results = self._hybrid_scan(bag_files, strategy)

                elif strategy.mode == ScanMode.TARGETED:

        self.logger.info(f"Scan complete in {scan_time:.1f} seconds")            results = self._targeted_scan(bag_files, strategy)

        self.logger.info(f"Found {self.detection_summary['wreck_detections']} wreck signatures")        else:

        self.logger.info(f"Found {self.detection_summary['obstruction_detections']} obstruction signatures")            raise ValueError(f"Unknown scan mode: {strategy.mode}")

        self.logger.info(f"Found {self.detection_summary['redaction_detections']} redaction signatures")        

                # Step 3: Compile final results

        return {        scan_time = time.time() - start_time

            'results': classified_results,        self.detection_summary.update({

            'summary': self.detection_summary,            'scan_time_seconds': scan_time,

            'pdf_features': self.pdf_features            'scan_mode_used': strategy.mode.value,

        }            'total_tiles_analyzed': len(results)

            })

    # ...rest of the class omitted for brevity...        

        # Step 4: Classify detections

# Convenience functions for different scan modes        classified_results = self._classify_detections(results)

        

def run_full_scan(bag_files: List[str], base_config: ScanConfig,         self.logger.info(f"Scan complete in {scan_time:.1f} seconds")

                 max_workers: int = 4) -> Dict[str, Any]:        self.logger.info(f"Found {self.detection_summary['wreck_detections']} wreck signatures")

    """Run complete pixel-by-pixel scan"""        self.logger.info(f"Found {self.detection_summary['obstruction_detections']} obstruction signatures")

    strategy = ScanStrategy(        self.logger.info(f"Found {self.detection_summary['redaction_detections']} redaction signatures")

        mode=ScanMode.FULL_SCAN,        

        max_workers=max_workers        return {

    )            'results': classified_results,

                'summary': self.detection_summary,

    scanner = MultiModeScanner(base_config)            'pdf_features': self.pdf_features

    return scanner.run_comprehensive_scan(bag_files, strategy)        }

    

    def _extract_priority_areas(self, pdf_results: Dict) -> List[Dict]:

def run_quick_scan(bag_files: List[str], base_config: ScanConfig,        """Extract priority areas from PDF analysis"""

                  sample_interval_m: float = 15.0) -> Dict[str, Any]:        priority_areas = []

    """Run quick spot sampling scan"""        

    strategy = ScanStrategy(        for pdf_name, features in pdf_results.items():

        mode=ScanMode.QUICK_SCAN,            for feature in features:

        sample_interval_m=sample_interval_m,                if feature.estimated_coords and feature.confidence > 0.5:

        sample_size_m=1.0,                    priority_area = {

        detection_box_m=500.0                        'lat': feature.estimated_coords[0],

    )                        'lon': feature.estimated_coords[1],

                            'type': feature.feature_type,

    scanner = MultiModeScanner(base_config)                        'confidence': feature.confidence,

    return scanner.run_comprehensive_scan(bag_files, strategy)                        'source_pdf': pdf_name,

                        'priority': 'high' if feature.feature_type == 'wreck' else 'medium'

                    }

def run_pdf_guided_scan(bag_files: List[str], base_config: ScanConfig,                    priority_areas.append(priority_area)

                       pdf_dir: str) -> Dict[str, Any]:        

    """Run PDF-guided focused scan"""        return priority_areas

    strategy = ScanStrategy(    

        mode=ScanMode.PDF_GUIDED,    def _full_scan(self, bag_files: List[str], strategy: ScanStrategy) -> List[Dict]:

        detection_box_m=500.0        """Traditional complete scanning approach"""

    )        self.logger.info("Running full pixel-by-pixel scan...")

            

    scanner = MultiModeScanner(base_config)        all_results = []

    return scanner.run_comprehensive_scan(bag_files, strategy, pdf_dir)        

        if strategy.max_workers > 1:

            # Parallel processing

def run_hybrid_scan(bag_files: List[str], base_config: ScanConfig,            with ThreadPoolExecutor(max_workers=strategy.max_workers) as executor:

                   pdf_dir: str, sample_interval_m: float = 20.0) -> Dict[str, Any]:                futures = [executor.submit(self.detector.scan_bag_file, bag_file) 

    """Run hybrid PDF + quick scan"""                          for bag_file in bag_files]

    strategy = ScanStrategy(                

        mode=ScanMode.HYBRID,                for future in futures:

        sample_interval_m=sample_interval_m,                    try:

        detection_box_m=500.0,                        results = future.result()

        max_workers=4                        all_results.extend(results)

    )                    except Exception as e:

                            self.logger.error(f"Error in parallel scan: {e}")

    scanner = MultiModeScanner(base_config)        else:

    return scanner.run_comprehensive_scan(bag_files, strategy, pdf_dir)            # Sequential processing

            for bag_file in bag_files:

                try:

if __name__ == "__main__":                    results = self.detector.scan_bag_file(bag_file)

    # Example usage                    all_results.extend(results)

    from pathlib import Path                except Exception as e:

                        self.logger.error(f"Error scanning {bag_file}: {e}")

    base_config = ScanConfig(        

        base_dir=r"c:\Temp\bagfilework",        return all_results

        bag_dir=r"c:\Temp\bagfilework",    

        bounds={'west': -85.50, 'east': -84.40, 'south': 45.70, 'north': 46.00}    def _quick_scan(self, bag_files: List[str], strategy: ScanStrategy) -> List[Dict]:

    )        """Quick spot sampling scan"""

            self.logger.info(f"Running quick scan with {strategy.sample_interval_m}m intervals...")

    bag_files = list(Path(r"c:\Temp\bagfilework").glob("*.bag"))        

    pdf_dir = r"c:\Temp\bagfilework\bathymetric_project"        all_results = []

            

    # Run hybrid scan (recommended)        for bag_file in bag_files:

    results = run_hybrid_scan(            self.logger.info(f"Quick scanning: {os.path.basename(bag_file)}")

        [str(f) for f in bag_files],            

        base_config,            try:

        pdf_dir,                with rasterio.open(bag_file) as src:

        sample_interval_m=15.0                    # Calculate sampling grid

    )                    bounds = src.bounds

                        transform = src.transform

    print(f"Scan complete: {results['summary']}")                    pixel_size = abs(transform.a)

                    
                    # Convert sample parameters to pixels
                    sample_interval_px = int(strategy.sample_interval_m / pixel_size)
                    sample_size_px = max(int(strategy.sample_size_m / pixel_size), 3)
                    
                    # Create sampling grid
                    for row in range(0, src.height, sample_interval_px):
                        for col in range(0, src.width, sample_interval_px):
                            
                            # Extract small sample
                            window = Window(col, row, sample_size_px, sample_size_px)
                            
                            if (window.col_off + window.width > src.width or
                                window.row_off + window.height > src.height):
                                continue
                            
                            # Quick analysis of sample
                            result = self._analyze_sample(src, window, bag_file, strategy)
                            
                            if result and result.get('suspicious', False):
                                # Expand analysis around suspicious area
                                expanded_results = self._expand_analysis(
                                    src, window, bag_file, strategy
                                )
                                all_results.extend(expanded_results)
                            elif result:
                                all_results.append(result)
            
            except Exception as e:
                self.logger.error(f"Error in quick scan of {bag_file}: {e}")
        
        return all_results
    
    def _analyze_sample(self, src: rasterio.DatasetReader, 
                       window: Window, 
                       bag_file: str, 
                       strategy: ScanStrategy) -> Optional[Dict]:
        """Analyze a small sample area quickly"""
        
        try:
            # Read data
            elevation = src.read(1, window=window)
            uncertainty = src.read(2, window=window) if src.count > 1 else None
            
            # Quick anomaly checks
            valid_mask = ~np.isnan(elevation)
            if np.sum(valid_mask) < 3:
                return None
            
            valid_elevation = elevation[valid_mask]
            
            # Basic suspicious indicators
            suspicious_indicators = 0
            
            # 1. Very low standard deviation (smoothing)
            if np.std(valid_elevation) < strategy.confidence_threshold * 0.5:
                suspicious_indicators += 1
            
            # 2. High uncertainty values
            if uncertainty is not None:
                valid_uncertainty = uncertainty[valid_mask]
                if len(valid_uncertainty) > 0 and np.max(valid_uncertainty) > 100:
                    suspicious_indicators += 1
            
            # 3. Elevation range consistent with wreck dimensions
            elevation_range = np.ptp(valid_elevation)
            if 1.0 <= elevation_range <= 8.0:  # Typical wreck height
                suspicious_indicators += 1
            
            # Get center coordinates
            center_col = window.col_off + window.width / 2
            center_row = window.row_off + window.height / 2
            center_x, center_y = src.xy(center_row, center_col)
            
            # Convert to lat/lon if needed
            if src.crs and src.crs != rasterio.crs.CRS.from_epsg(4326):
                transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(center_x, center_y)
            else:
                lon, lat = center_x, center_y
            
            result = {
                'center_lat': lat,
                'center_lon': lon,
                'center_utm_x': center_x,
                'center_utm_y': center_y,
                'elevation_std': np.std(valid_elevation),
                'elevation_range': elevation_range,
                'max_uncertainty': np.max(uncertainty[valid_mask]) if uncertainty is not None else 0,
                'suspicious_indicators': suspicious_indicators,
                'suspicious': suspicious_indicators >= 2,
                'source_file': os.path.basename(bag_file),
                'window_col': window.col_off,
                'window_row': window.row_off,
                'scan_type': 'quick_sample'
            }
            
            return result
            
        except Exception as e:
            self.logger.debug(f"Error analyzing sample: {e}")
            return None
    
    def _expand_analysis(self, src: rasterio.DatasetReader,
                        center_window: Window,
                        bag_file: str,
                        strategy: ScanStrategy) -> List[Dict]:
        """Expand analysis around suspicious area"""
        
        self.logger.debug("Expanding analysis around suspicious area...")
        
        # Calculate expanded window
        pixel_size = abs(src.transform.a)
        expand_pixels = int(strategy.detection_box_m / pixel_size / 2)
        
        # Center the expansion on the suspicious sample
        center_col = center_window.col_off + center_window.width / 2
        center_row = center_window.row_off + center_window.height / 2
        
        expanded_window = Window(
            max(0, int(center_col - expand_pixels)),
            max(0, int(center_row - expand_pixels)),
            min(expand_pixels * 2, src.width),
            min(expand_pixels * 2, src.height)
        )
        
        # Ensure window doesn't exceed image bounds
        if (expanded_window.col_off + expanded_window.width > src.width):
            expanded_window = Window(
                expanded_window.col_off,
                expanded_window.row_off,
                src.width - expanded_window.col_off,
                expanded_window.height
            )
        
        if (expanded_window.row_off + expanded_window.height > src.height):
            expanded_window = Window(
                expanded_window.col_off,
                expanded_window.row_off,
                expanded_window.width,
                src.height - expanded_window.row_off
            )
        
        # Read expanded area
        try:
            elevation_data = src.read(1, window=expanded_window)
            uncertainty_data = src.read(2, window=expanded_window) if src.count > 1 else None
            window_transform = src.window_transform(expanded_window)
            
            # Run comprehensive analysis on expanded area
            result = self.detector.analyze_tile(
                elevation_data, uncertainty_data, window_transform, expanded_window
            )
            
            if result:
                result['source_file'] = os.path.basename(bag_file)
                result['scan_type'] = 'expanded_analysis'
                result['expansion_trigger'] = 'quick_scan_detection'
                
                # Run advanced scrubbing detection
                scrub_analysis = self.scrub_engine.comprehensive_scrub_analysis(
                    elevation_data, uncertainty_data, pixel_size
                )
                result.update(scrub_analysis)
                
                return [result]
        
        except Exception as e:
            self.logger.error(f"Error in expanded analysis: {e}")
        
        return []
    
    def _pdf_guided_scan(self, bag_files: List[str], strategy: ScanStrategy) -> List[Dict]:
        """Scan focused on PDF-identified areas"""
        self.logger.info("Running PDF-guided scan...")
        
        if not self.pdf_features:
            self.logger.warning("No PDF features available, falling back to quick scan")
            return self._quick_scan(bag_files, strategy)
        
        all_results = []
        
        for bag_file in bag_files:
            self.logger.info(f"PDF-guided scanning: {os.path.basename(bag_file)}")
            
            try:
                with rasterio.open(bag_file) as src:
                    
                    # For each PDF feature, check if it's in this file's bounds
                    for pdf_feature in self.pdf_features:
                        if self._point_in_file_bounds(src, pdf_feature['lat'], pdf_feature['lon']):
                            
                            # Convert to pixel coordinates
                            row, col = src.index(pdf_feature['lon'], pdf_feature['lat'])
                            
                            # Create analysis window around the point
                            pixel_size = abs(src.transform.a)
                            window_size = int(strategy.detection_box_m / pixel_size / 2)
                            
                            window = Window(
                                max(0, col - window_size),
                                max(0, row - window_size),
                                min(window_size * 2, src.width - max(0, col - window_size)),
                                min(window_size * 2, src.height - max(0, row - window_size))
                            )
                            
                            # Analyze area
                            result = self._analyze_pdf_guided_area(
                                src, window, bag_file, pdf_feature, strategy
                            )
                            
                            if result:
                                all_results.append(result)
            
            except Exception as e:
                self.logger.error(f"Error in PDF-guided scan of {bag_file}: {e}")
        
        return all_results
    
    def _point_in_file_bounds(self, src: rasterio.DatasetReader, lat: float, lon: float) -> bool:
        """Check if a lat/lon point is within the file's bounds"""
        
        bounds = src.bounds
        
        # Convert bounds to lat/lon if needed
        if src.crs and src.crs != rasterio.crs.CRS.from_epsg(4326):
            transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
            
            # Convert corner points
            min_lon, min_lat = transformer.transform(bounds.left, bounds.bottom)
            max_lon, max_lat = transformer.transform(bounds.right, bounds.top)
            
            return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
        else:
            return bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top
    
    def _analyze_pdf_guided_area(self, src: rasterio.DatasetReader,
                                window: Window,
                                bag_file: str,
                                pdf_feature: Dict,
                                strategy: ScanStrategy) -> Optional[Dict]:
        """Analyze area identified by PDF analysis"""
        
        try:
            elevation_data = src.read(1, window=window)
            uncertainty_data = src.read(2, window=window) if src.count > 1 else None
            window_transform = src.window_transform(window)
            
            # Full analysis of this area
            result = self.detector.analyze_tile(
                elevation_data, uncertainty_data, window_transform, window
            )
            
            if result:
                result.update({
                    'source_file': os.path.basename(bag_file),
                    'scan_type': 'pdf_guided',
                    'pdf_feature_type': pdf_feature['type'],
                    'pdf_confidence': pdf_feature['confidence'],
                    'pdf_source': pdf_feature['source_pdf']
                })
                
                # Enhanced analysis with scrub detection
                pixel_size = abs(src.transform.a)
                scrub_analysis = self.scrub_engine.comprehensive_scrub_analysis(
                    elevation_data, uncertainty_data, pixel_size
                )
                result.update(scrub_analysis)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing PDF-guided area: {e}")
            return None
    
    def _hybrid_scan(self, bag_files: List[str], strategy: ScanStrategy) -> List[Dict]:
        """Hybrid approach: PDF guidance + quick scanning"""
        self.logger.info("Running hybrid scan (PDF + quick sampling)...")
        
        # First, do PDF-guided scan
        pdf_results = self._pdf_guided_scan(bag_files, strategy) if self.pdf_features else []
        
        # Then, do quick scan of remaining areas
        # TODO: Modify quick scan to avoid already-scanned areas
        quick_results = self._quick_scan(bag_files, strategy)
        
        # Combine and deduplicate
        all_results = pdf_results + quick_results
        
        # Remove duplicates based on proximity
        deduplicated = self._deduplicate_results(all_results, min_distance_m=50)
        
        return deduplicated
    
    def _targeted_scan(self, bag_files: List[str], strategy: ScanStrategy) -> List[Dict]:
        """Scan specific target coordinates only"""
        self.logger.info("Running targeted coordinate scan...")
        
        # This would be used when you have specific coordinates to check
        # Implementation would be similar to PDF-guided but with user-provided coordinates
        
        target_coords = [
            # Add specific coordinates here
            # (lat, lon, description)
        ]
        
        # For now, fall back to PDF guidance or quick scan
        if self.pdf_features:
            return self._pdf_guided_scan(bag_files, strategy)
        else:
            return self._quick_scan(bag_files, strategy)
    
    def _deduplicate_results(self, results: List[Dict], min_distance_m: float = 50) -> List[Dict]:
        """Remove duplicate detections within minimum distance"""
        
        if not results:
            return results
        
        deduplicated = []
        
        for result in results:
            is_duplicate = False
            
            for existing in deduplicated:
                # Calculate distance
                lat1, lon1 = result.get('center_lat', 0), result.get('center_lon', 0)
                lat2, lon2 = existing.get('center_lat', 0), existing.get('center_lon', 0)
                
                # Simple distance calculation (approximate)
                dlat = abs(lat1 - lat2) * 111000  # meters per degree latitude
                dlon = abs(lon1 - lon2) * 111000 * np.cos(np.radians((lat1 + lat2) / 2))
                distance = np.sqrt(dlat**2 + dlon**2)
                
                if distance < min_distance_m:
                    is_duplicate = True
                    # Keep the result with higher confidence
                    if result.get('anomaly_score', 0) > existing.get('anomaly_score', 0):
                        deduplicated.remove(existing)
                        deduplicated.append(result)
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        return deduplicated
    
    def _classify_detections(self, results: List[Dict]) -> List[Dict]:
        """Classify detections as wreck/obstruction/redaction"""
        
        for result in results:
            # Default classification
            result['detection_class'] = 'unknown'
            result['class_confidence'] = 0.5
            
            # Classification logic based on your patterns
            
            # High wreck probability from ML model
            if result.get('wreck_probability', 0) > 0.7:
                result['detection_class'] = 'wreck'
                result['class_confidence'] = result.get('wreck_probability', 0.7)
            
            # Freighter signature detected
            elif result.get('freighter_likelihood', 0) > 0.6:
                result['detection_class'] = 'wreck'
                result['class_confidence'] = result.get('freighter_likelihood', 0.6)
            
            # High scrubbing likelihood
            elif result.get('overall_scrubbing_probability', 0) > 0.7:
                result['detection_class'] = 'redaction'
                result['class_confidence'] = result.get('overall_scrubbing_probability', 0.7)
            
            # PDF indicated wreck
            elif result.get('pdf_feature_type') == 'wreck':
                result['detection_class'] = 'wreck'
                result['class_confidence'] = result.get('pdf_confidence', 0.6)
            
            # PDF indicated obstruction
            elif result.get('pdf_feature_type') == 'obstruction':
                result['detection_class'] = 'obstruction'
                result['class_confidence'] = result.get('pdf_confidence', 0.6)
            
            # High anomaly but unclear type
            elif result.get('anomaly_score', -999) > 0:
                result['detection_class'] = 'anomaly'
                result['class_confidence'] = min(1.0, (result.get('anomaly_score', 0) + 1) / 2)
        
        # Update summary counts
        self.detection_summary.update({
            'wreck_detections': len([r for r in results if r['detection_class'] == 'wreck']),
            'obstruction_detections': len([r for r in results if r['detection_class'] == 'obstruction']),
            'redaction_detections': len([r for r in results if r['detection_class'] == 'redaction'])
        })
        
        return results


# Convenience functions for different scan modes

def run_full_scan(bag_files: List[str], base_config: ScanConfig, 
                 max_workers: int = 4) -> Dict[str, Any]:
    """Run complete pixel-by-pixel scan"""
    strategy = ScanStrategy(
        mode=ScanMode.FULL_SCAN,
        max_workers=max_workers
    )
    
    scanner = MultiModeScanner(base_config)
    return scanner.run_comprehensive_scan(bag_files, strategy)


def run_quick_scan(bag_files: List[str], base_config: ScanConfig,
                  sample_interval_m: float = 15.0) -> Dict[str, Any]:
    """Run quick spot sampling scan"""
    strategy = ScanStrategy(
        mode=ScanMode.QUICK_SCAN,
        sample_interval_m=sample_interval_m,
        sample_size_m=1.0,
        detection_box_m=500.0
    )
    
    scanner = MultiModeScanner(base_config)
    return scanner.run_comprehensive_scan(bag_files, strategy)


def run_pdf_guided_scan(bag_files: List[str], base_config: ScanConfig,
                       pdf_dir: str) -> Dict[str, Any]:
    """Run PDF-guided focused scan"""
    strategy = ScanStrategy(
        mode=ScanMode.PDF_GUIDED,
        detection_box_m=500.0
    )
    
    scanner = MultiModeScanner(base_config)
    return scanner.run_comprehensive_scan(bag_files, strategy, pdf_dir)


def run_hybrid_scan(bag_files: List[str], base_config: ScanConfig,
                   pdf_dir: str, sample_interval_m: float = 20.0) -> Dict[str, Any]:
    """Run hybrid PDF + quick scan"""
    strategy = ScanStrategy(
        mode=ScanMode.HYBRID,
        sample_interval_m=sample_interval_m,
        detection_box_m=500.0,
        max_workers=4
    )
    
    scanner = MultiModeScanner(base_config)
    return scanner.run_comprehensive_scan(bag_files, strategy, pdf_dir)


if __name__ == "__main__":
    # Example usage
    from pathlib import Path
    
    base_config = ScanConfig(
        base_dir=r"c:\Temp\bagfilework",
        bag_dir=r"c:\Temp\bagfilework",
        bounds={'west': -85.50, 'east': -84.40, 'south': 45.70, 'north': 46.00}
    )
    
    bag_files = list(Path(r"c:\Temp\bagfilework").glob("*.bag"))
    pdf_dir = r"c:\Temp\bagfilework\bathymetric_project"
    
    # Run hybrid scan (recommended)
    results = run_hybrid_scan(
        [str(f) for f in bag_files],
        base_config,
        pdf_dir,
        sample_interval_m=15.0
    )
    
    print(f"Scan complete: {results['summary']}")