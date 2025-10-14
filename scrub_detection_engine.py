""""""

Advanced Pattern Recognition for NOAA Data Scrubbing DetectionAdvanced Pattern Recognition for NOAA Data Scrubbing Detection

Specialized algorithms for detecting wreck redaction patternsSpecialized algorithms for detecting wreck redaction patterns

""""""



import numpy as npimport numpy as np

import cv2import cv2

from scipy import ndimagefrom scipy import ndimage

from scipy.signal import find_peaksfrom scipy.signal import find_peaks

from scipy.stats import zscorefrom scipy.stats import zscore

from skimage.feature import local_binary_patternfrom skimage.feature import local_binary_pattern

from skimage.morphology import disk, opening, closingfrom skimage.morphology import disk, opening, closing

from typing import Dict, List, Tuple, Optional, Anyfrom typing import Dict, List, Tuple, Optional, Any

import loggingimport logging





class ScrubDetectionEngine:class ScrubDetectionEngine:

    """    """

    Advanced detection engine for NOAA's wreck scrubbing/smoothing patterns    Advanced detection engine for NOAA's wreck scrubbing/smoothing patterns

    Based on analysis of redacted PDFs and known omitted wrecks    Based on analysis of redacted PDFs and known omitted wrecks

    """    """

        

    def __init__(self):    def __init__(self):

        self.logger = logging.getLogger(__name__)        self.logger = logging.getLogger(__name__)

                

        # Smoothing kernel patterns NOAA likely uses        # Smoothing kernel patterns NOAA likely uses

        self.smoothing_kernels = {        self.smoothing_kernels = {

            'gaussian': self._create_gaussian_kernel,            'gaussian': self._create_gaussian_kernel,

            'averaging': self._create_averaging_kernel,            'averaging': self._create_averaging_kernel,

            'median': self._create_median_kernel            'median': self._create_median_kernel

        }        }

        

    def _create_gaussian_kernel(self, size: int = 5, sigma: float = 1.0) -> np.ndarray:    def _create_gaussian_kernel(self, size: int = 5, sigma: float = 1.0) -> np.ndarray:

        """Create Gaussian smoothing kernel"""        """Create Gaussian smoothing kernel"""

        kernel = cv2.getGaussianKernel(size, sigma)        kernel = cv2.getGaussianKernel(size, sigma)

        return kernel @ kernel.T        return kernel @ kernel.T

        

    def _create_averaging_kernel(self, size: int = 5) -> np.ndarray:    def _create_averaging_kernel(self, size: int = 5) -> np.ndarray:

        """Create averaging/box kernel"""        """Create averaging/box kernel"""

        return np.ones((size, size)) / (size * size)        return np.ones((size, size)) / (size * size)

        

    def _create_median_kernel(self, size: int = 5) -> np.ndarray:    def _create_median_kernel(self, size: int = 5) -> np.ndarray:

        """Create median filter approximation"""        """Create median filter approximation"""

        return np.ones((size, size)) / (size * size)        return np.ones((size, size)) / (size * size)

        

    def detect_freighter_signature(self, elevation_data: np.ndarray,     def detect_freighter_signature(self, elevation_data: np.ndarray, 

                                 pixel_size_m: float = 2.0) -> Dict[str, float]:                                 pixel_size_m: float = 2.0) -> Dict[str, float]:

        """        """

        Detect signatures consistent with Great Lakes freighters        Detect signatures consistent with Great Lakes freighters

        Typical dimensions: 200-300m length, 20-35m width        Typical dimensions: 200-300m length, 20-35m width

        """        """

        results = {'freighter_likelihood': 0.0, 'estimated_length_m': 0, 'estimated_width_m': 0}        results = {'freighter_likelihood': 0.0, 'estimated_length_m': 0, 'estimated_width_m': 0}

                

        # Expected freighter dimensions in pixels        # Expected freighter dimensions in pixels

        min_length_px = int(200 / pixel_size_m)        min_length_px = int(200 / pixel_size_m)

        max_length_px = int(350 / pixel_size_m)        max_length_px = int(350 / pixel_size_m)

        min_width_px = int(18 / pixel_size_m)        min_width_px = int(18 / pixel_size_m)

        max_width_px = int(40 / pixel_size_m)        max_width_px = int(40 / pixel_size_m)

                

        # Apply morphological operations to enhance linear features        # Apply morphological operations to enhance linear features

        kernel_long = cv2.getStructuringElement(cv2.MORPH_RECT, (max_length_px//4, 3))        kernel_long = cv2.getStructuringElement(cv2.MORPH_RECT, (max_length_px//4, 3))

        kernel_wide = cv2.getStructuringElement(cv2.MORPH_RECT, (3, max_width_px//4))        kernel_wide = cv2.getStructuringElement(cv2.MORPH_RECT, (3, max_width_px//4))

                

        # Create binary mask from elevation anomalies        # Create binary mask from elevation anomalies

        valid_mask = ~np.isnan(elevation_data)        valid_mask = ~np.isnan(elevation_data)

        if np.sum(valid_mask) < 100:        if np.sum(valid_mask) < 100:

            return results            return results

                

        # Normalize elevation data        # Normalize elevation data

        valid_data = elevation_data[valid_mask]        valid_data = elevation_data[valid_mask]

        threshold = np.percentile(valid_data, 85)  # Top 15% for elevated features        threshold = np.percentile(valid_data, 85)  # Top 15% for elevated features

        binary_elevated = (elevation_data > threshold) & valid_mask        binary_elevated = (elevation_data > threshold) & valid_mask

                

        # Also check for depressions (scrubbed areas)        # Also check for depressions (scrubbed areas)

        depression_threshold = np.percentile(valid_data, 15)  # Bottom 15%        depression_threshold = np.percentile(valid_data, 15)  # Bottom 15%

        binary_depressed = (elevation_data < depression_threshold) & valid_mask        binary_depressed = (elevation_data < depression_threshold) & valid_mask

                

        for binary_mask, feature_type in [(binary_elevated.astype(np.uint8), 'elevated'),         for binary_mask, feature_type in [(binary_elevated.astype(np.uint8), 'elevated'), 

                                         (binary_depressed.astype(np.uint8), 'depressed')]:                                         (binary_depressed.astype(np.uint8), 'depressed')]:

                        

            # Morphological operations to connect ship-like features            # Morphological operations to connect ship-like features

            opened_long = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_long)            opened_long = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_long)

            opened_wide = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_wide)            opened_wide = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_wide)

                        

            # Find contours            # Find contours

            contours_long, _ = cv2.findContours(opened_long, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)            contours_long, _ = cv2.findContours(opened_long, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            contours_wide, _ = cv2.findContours(opened_wide, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)            contours_wide, _ = cv2.findContours(opened_wide, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                        

            # Analyze contours for ship-like dimensions            # Analyze contours for ship-like dimensions

            for contours in [contours_long, contours_wide]:            for contours in [contours_long, contours_wide]:

                for contour in contours:                for contour in contours:

                    if len(contour) < 5:                    if len(contour) < 5:

                        continue                        continue

                                        

                    # Fit ellipse to get orientation and dimensions                    # Fit ellipse to get orientation and dimensions

                    try:                    try:

                        ellipse = cv2.fitEllipse(contour)                        ellipse = cv2.fitEllipse(contour)

                        center, (minor_axis, major_axis), angle = ellipse                        center, (minor_axis, major_axis), angle = ellipse

                                                

                        # Convert to meters                        # Convert to meters

                        length_m = max(minor_axis, major_axis) * pixel_size_m                        length_m = max(minor_axis, major_axis) * pixel_size_m

                        width_m = min(minor_axis, major_axis) * pixel_size_m                        width_m = min(minor_axis, major_axis) * pixel_size_m

                                                

                        # Check if dimensions match freighter profile                        # Check if dimensions match freighter profile

                        length_match = 180 <= length_m <= 350                        length_match = 180 <= length_m <= 350

                        width_match = 15 <= width_m <= 40                        width_match = 15 <= width_m <= 40

                        aspect_ratio = length_m / width_m if width_m > 0 else 0                        aspect_ratio = length_m / width_m if width_m > 0 else 0

                        aspect_match = 4 <= aspect_ratio <= 20  # Ships are long and narrow                        aspect_match = 4 <= aspect_ratio <= 20  # Ships are long and narrow

                                                

                        if length_match and width_match and aspect_match:                        if length_match and width_match and aspect_match:

                            confidence = min(1.0, (length_m / 250.0) * (aspect_ratio / 10.0))                            confidence = min(1.0, (length_m / 250.0) * (aspect_ratio / 10.0))

                            if confidence > results['freighter_likelihood']:                            if confidence > results['freighter_likelihood']:

                                results.update({                                results.update({

                                    'freighter_likelihood': confidence,                                    'freighter_likelihood': confidence,

                                    'estimated_length_m': length_m,                                    'estimated_length_m': length_m,

                                    'estimated_width_m': width_m,                                    'estimated_width_m': width_m,

                                    'aspect_ratio': aspect_ratio,                                    'aspect_ratio': aspect_ratio,

                                    'feature_type': feature_type                                    'feature_type': feature_type

                                })                                })

                                        

                    except:                    except:

                        continue                        continue

                

        return results        return results

        

    def detect_smoothing_pattern(self, elevation_data: np.ndarray,    def detect_smoothing_pattern(self, elevation_data: np.ndarray,

                               window_size: int = 15) -> Dict[str, float]:                               window_size: int = 15) -> Dict[str, float]:

        """        """

        Detect NOAA's characteristic smoothing patterns        Detect NOAA's characteristic smoothing patterns

        Looks for telltale signs of Gaussian or median filtering        Looks for telltale signs of Gaussian or median filtering

        """        """

        results = {'smoothing_confidence': 0.0, 'smoothing_type': 'none'}        results = {'smoothing_confidence': 0.0, 'smoothing_type': 'none'}

                

        valid_mask = ~np.isnan(elevation_data)        valid_mask = ~np.isnan(elevation_data)

        if np.sum(valid_mask) < window_size * window_size:        if np.sum(valid_mask) < window_size * window_size:

            return results            return results

                

        # Calculate local statistics in sliding windows        # Calculate local statistics in sliding windows

        smoothness_scores = []        smoothness_scores = []

        gradient_consistencies = []        gradient_consistencies = []

                

        for i in range(0, elevation_data.shape[0] - window_size, window_size//2):        for i in range(0, elevation_data.shape[0] - window_size, window_size//2):

            for j in range(0, elevation_data.shape[1] - window_size, window_size//2):            for j in range(0, elevation_data.shape[1] - window_size, window_size//2):

                window = elevation_data[i:i+window_size, j:j+window_size]                window = elevation_data[i:i+window_size, j:j+window_size]

                window_valid = valid_mask[i:i+window_size, j:j+window_size]                window_valid = valid_mask[i:i+window_size, j:j+window_size]

                                

                if np.sum(window_valid) < window_size * window_size * 0.5:                if np.sum(window_valid) < window_size * window_size * 0.5:

                    continue                    continue

                                

                valid_window_data = window[window_valid]                valid_window_data = window[window_valid]

                                

                # 1. Smoothness measure (low variance indicates smoothing)                # 1. Smoothness measure (low variance indicates smoothing)

                smoothness = 1.0 / (1.0 + np.var(valid_window_data))                smoothness = 1.0 / (1.0 + np.var(valid_window_data))

                smoothness_scores.append(smoothness)                smoothness_scores.append(smoothness)

                                

                # 2. Gradient consistency (artificial smoothing creates too-regular gradients)                # 2. Gradient consistency (artificial smoothing creates too-regular gradients)

                grad_x = np.gradient(window, axis=1)                grad_x = np.gradient(window, axis=1)

                grad_y = np.gradient(window, axis=0)                grad_y = np.gradient(window, axis=0)

                grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)                grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)

                                

                # Natural seabed has irregular gradients, smoothed areas have consistent gradients                # Natural seabed has irregular gradients, smoothed areas have consistent gradients

                grad_valid = grad_magnitude[window_valid]                grad_valid = grad_magnitude[window_valid]

                if len(grad_valid) > 5:                if len(grad_valid) > 5:

                    grad_consistency = 1.0 - np.std(grad_valid) / (np.mean(grad_valid) + 1e-6)                    grad_consistency = 1.0 - np.std(grad_valid) / (np.mean(grad_valid) + 1e-6)

                    gradient_consistencies.append(max(0, grad_consistency))                    gradient_consistencies.append(max(0, grad_consistency))

                

        if not smoothness_scores:        if not smoothness_scores:

            return results            return results

                

        # Aggregate scores        # Aggregate scores

        avg_smoothness = np.mean(smoothness_scores)        avg_smoothness = np.mean(smoothness_scores)

        avg_grad_consistency = np.mean(gradient_consistencies)        avg_grad_consistency = np.mean(gradient_consistencies)

                

        # Detect specific smoothing patterns        # Detect specific smoothing patterns

        smoothing_confidence = 0.0        smoothing_confidence = 0.0

        smoothing_type = 'none'        smoothing_type = 'none'

                

        # High smoothness + high gradient consistency = likely artificial smoothing        # High smoothness + high gradient consistency = likely artificial smoothing

        if avg_smoothness > 0.7 and avg_grad_consistency > 0.6:        if avg_smoothness > 0.7 and avg_grad_consistency > 0.6:

            smoothing_confidence = min(1.0, avg_smoothness * avg_grad_consistency)            smoothing_confidence = min(1.0, avg_smoothness * avg_grad_consistency)

            smoothing_type = 'gaussian_or_median'            smoothing_type = 'gaussian_or_median'

                

        # Additional test: detect box filter patterns (averaging)        # Additional test: detect box filter patterns (averaging)

        # Box filters create characteristic "terracing" effects        # Box filters create characteristic "terracing" effects

        if self._detect_terracing(elevation_data):        if self._detect_terracing(elevation_data):

            smoothing_confidence = max(smoothing_confidence, 0.8)            smoothing_confidence = max(smoothing_confidence, 0.8)

            smoothing_type = 'box_filter'            smoothing_type = 'box_filter'

                

        results.update({        results.update({

            'smoothing_confidence': smoothing_confidence,            'smoothing_confidence': smoothing_confidence,

            'smoothing_type': smoothing_type,            'smoothing_type': smoothing_type,

            'avg_smoothness': avg_smoothness,            'avg_smoothness': avg_smoothness,

            'avg_gradient_consistency': avg_grad_consistency            'avg_gradient_consistency': avg_grad_consistency

        })        })

                

        return results        return results

        

    def _detect_terracing(self, elevation_data: np.ndarray) -> bool:    def _detect_terracing(self, elevation_data: np.ndarray) -> bool:

        """        """

        Detect terracing patterns characteristic of box/averaging filters        Detect terracing patterns characteristic of box/averaging filters

        """        """

        valid_mask = ~np.isnan(elevation_data)        valid_mask = ~np.isnan(elevation_data)

        if np.sum(valid_mask) < 100:        if np.sum(valid_mask) < 100:

            return False            return False

                

        # Look for flat areas (constant elevation) connected by sharp transitions        # Look for flat areas (constant elevation) connected by sharp transitions

        # This is characteristic of box filter artifacts        # This is characteristic of box filter artifacts

                

        valid_data = elevation_data[valid_mask]        valid_data = elevation_data[valid_mask]

        hist, bins = np.histogram(valid_data, bins=50)        hist, bins = np.histogram(valid_data, bins=50)

                

        # Look for unusually high peaks in histogram (indicating repeated values)        # Look for unusually high peaks in histogram (indicating repeated values)

        # Natural seabed rarely has many identical depth values        # Natural seabed rarely has many identical depth values

        hist_normalized = hist / np.sum(hist)        hist_normalized = hist / np.sum(hist)

        peak_threshold = 3.0 / len(bins)  # Expected frequency if uniform        peak_threshold = 3.0 / len(bins)  # Expected frequency if uniform

                

        suspicious_peaks = np.sum(hist_normalized > peak_threshold)        suspicious_peaks = np.sum(hist_normalized > peak_threshold)

                

        # If more than 10% of histogram bins have unusually high frequencies        # If more than 10% of histogram bins have unusually high frequencies

        return suspicious_peaks > len(bins) * 0.1        return suspicious_peaks > len(bins) * 0.1

        

    def detect_wreck_scrubbing_box(self, elevation_data: np.ndarray,    def detect_wreck_scrubbing_box(self, elevation_data: np.ndarray,

                                 uncertainty_data: np.ndarray = None,                                 uncertainty_data: np.ndarray = None,

                                 pixel_size_m: float = 2.0) -> Dict[str, Any]:                                 pixel_size_m: float = 2.0) -> Dict[str, Any]:

        """        """

        Detect the characteristic "freighter-sized box" pattern you mentioned        Detect the characteristic "freighter-sized box" pattern you mentioned

        Where NOAA may have replaced wreck data with interpolated seabed        Where NOAA may have replaced wreck data with interpolated seabed

        """        """

        results = {        results = {

            'scrubbing_likelihood': 0.0,            'scrubbing_likelihood': 0.0,

            'box_dimensions_m': (0, 0),            'box_dimensions_m': (0, 0),

            'indicators': []            'indicators': []

        }        }

                

        # Expected freighter box dimensions        # Expected freighter box dimensions

        expected_length_px = int(250 / pixel_size_m)  # ~250m typical freighter        expected_length_px = int(250 / pixel_size_m)  # ~250m typical freighter

        expected_width_px = int(25 / pixel_size_m)    # ~25m typical beam        expected_width_px = int(25 / pixel_size_m)    # ~25m typical beam

                

        # Look for rectangular areas with suspicious characteristics        # Look for rectangular areas with suspicious characteristics

        rectangular_masks = self._find_rectangular_regions(elevation_data,         rectangular_masks = self._find_rectangular_regions(elevation_data, 

                                                         min_length=expected_length_px//2,                                                         min_length=expected_length_px//2,

                                                         max_length=expected_length_px*2,                                                         max_length=expected_length_px*2,

                                                         min_width=expected_width_px//2,                                                         min_width=expected_width_px//2,

                                                         max_width=expected_width_px*2)                                                         max_width=expected_width_px*2)

                

        for mask in rectangular_masks:        for mask in rectangular_masks:

            indicators = []            indicators = []

                        

            # Test 1: Unnaturally smooth elevation within the box            # Test 1: Unnaturally smooth elevation within the box

            box_elevation = elevation_data[mask]            box_elevation = elevation_data[mask]

            box_elevation = box_elevation[~np.isnan(box_elevation)]            box_elevation = box_elevation[~np.isnan(box_elevation)]

                        

            if len(box_elevation) < 10:            if len(box_elevation) < 10:

                continue                continue

                        

            elevation_std = np.std(box_elevation)            elevation_std = np.std(box_elevation)

            if elevation_std < 0.3:  # Very smooth            if elevation_std < 0.3:  # Very smooth

                indicators.append('very_smooth_elevation')                indicators.append('very_smooth_elevation')

                        

            # Test 2: Elevation distribution doesn't match surroundings            # Test 2: Elevation distribution doesn't match surroundings

            # Get surrounding area            # Get surrounding area

            dilated_mask = ndimage.binary_dilation(mask, iterations=10)            dilated_mask = ndimage.binary_dilation(mask, iterations=10)

            surround_mask = dilated_mask & ~mask & ~np.isnan(elevation_data)            surround_mask = dilated_mask & ~mask & ~np.isnan(elevation_data)

                        

            if np.sum(surround_mask) > 10:            if np.sum(surround_mask) > 10:

                surround_elevation = elevation_data[surround_mask]                surround_elevation = elevation_data[surround_mask]

                                

                # Compare distributions                # Compare distributions

                box_mean = np.mean(box_elevation)                box_mean = np.mean(box_elevation)

                surround_mean = np.mean(surround_elevation)                surround_mean = np.mean(surround_elevation)

                                

                # Suspicious if box elevation is suspiciously close to surrounding mean                # Suspicious if box elevation is suspiciously close to surrounding mean

                # (indicates interpolation from surroundings)                # (indicates interpolation from surroundings)

                if abs(box_mean - surround_mean) < 0.2:                if abs(box_mean - surround_mean) < 0.2:

                    indicators.append('matches_surrounding_mean')                    indicators.append('matches_surrounding_mean')

                        

            # Test 3: High uncertainty values (if available)            # Test 3: High uncertainty values (if available)

            if uncertainty_data is not None:            if uncertainty_data is not None:

                box_uncertainty = uncertainty_data[mask]                box_uncertainty = uncertainty_data[mask]

                box_uncertainty = box_uncertainty[~np.isnan(box_uncertainty)]                box_uncertainty = box_uncertainty[~np.isnan(box_uncertainty)]

                                

                if len(box_uncertainty) > 0:                if len(box_uncertainty) > 0:

                    max_uncertainty = np.max(box_uncertainty)                    max_uncertainty = np.max(box_uncertainty)

                    if max_uncertainty > 100:  # Very high uncertainty                    if max_uncertainty > 100:  # Very high uncertainty

                        indicators.append('high_uncertainty')                        indicators.append('high_uncertainty')

                        

            # Test 4: Lack of natural texture            # Test 4: Lack of natural texture

            texture_score = self._calculate_texture_score(elevation_data[mask])            texture_score = self._calculate_texture_score(elevation_data[mask])

            if texture_score < 0.3:            if texture_score < 0.3:

                indicators.append('lacks_natural_texture')                indicators.append('lacks_natural_texture')

                        

            # Test 5: Sharp boundaries (unnatural edge definition)            # Test 5: Sharp boundaries (unnatural edge definition)

            edge_sharpness = self._calculate_edge_sharpness(elevation_data, mask)            edge_sharpness = self._calculate_edge_sharpness(elevation_data, mask)

            if edge_sharpness > 0.7:            if edge_sharpness > 0.7:

                indicators.append('sharp_unnatural_edges')                indicators.append('sharp_unnatural_edges')

                        

            # Calculate overall likelihood            # Calculate overall likelihood

            likelihood = len(indicators) / 5.0  # 5 possible indicators            likelihood = len(indicators) / 5.0  # 5 possible indicators

                        

            if likelihood > results['scrubbing_likelihood']:            if likelihood > results['scrubbing_likelihood']:

                # Get box dimensions                # Get box dimensions

                y_coords, x_coords = np.where(mask)                y_coords, x_coords = np.where(mask)

                height_m = (np.max(y_coords) - np.min(y_coords) + 1) * pixel_size_m                height_m = (np.max(y_coords) - np.min(y_coords) + 1) * pixel_size_m

                width_m = (np.max(x_coords) - np.min(x_coords) + 1) * pixel_size_m                width_m = (np.max(x_coords) - np.min(x_coords) + 1) * pixel_size_m

                                

                results.update({                results.update({

                    'scrubbing_likelihood': likelihood,                    'scrubbing_likelihood': likelihood,

                    'box_dimensions_m': (height_m, width_m),                    'box_dimensions_m': (height_m, width_m),

                    'indicators': indicators                    'indicators': indicators

                })                })

                

        return results        return results

        

    def _find_rectangular_regions(self, elevation_data: np.ndarray,    def _find_rectangular_regions(self, elevation_data: np.ndarray,

                                min_length: int, max_length: int,                                min_length: int, max_length: int,

                                min_width: int, max_width: int) -> List[np.ndarray]:                                min_width: int, max_width: int) -> List[np.ndarray]:

        """        """

        Find rectangular regions in elevation data that could be scrubbed areas        Find rectangular regions in elevation data that could be scrubbed areas

        """        """

        valid_mask = ~np.isnan(elevation_data)        valid_mask = ~np.isnan(elevation_data)

                

        # Use morphological operations with rectangular kernels of various sizes        # Use morphological operations with rectangular kernels of various sizes

        masks = []        masks = []

                

        for length in range(min_length, max_length, max(1, (max_length - min_length) // 5)):        for length in range(min_length, max_length, max(1, (max_length - min_length) // 5)):

            for width in range(min_width, max_width, max(1, (max_width - min_width) // 3)):            for width in range(min_width, max_width, max(1, (max_width - min_width) // 3)):

                                

                # Create rectangular kernel                # Create rectangular kernel

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (length, width))                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (length, width))

                                

                # Apply to valid mask                # Apply to valid mask

                opened = cv2.morphologyEx(valid_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)                opened = cv2.morphologyEx(valid_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)

                                

                if np.sum(opened) > 0:                if np.sum(opened) > 0:

                    masks.append(opened.astype(bool))                    masks.append(opened.astype(bool))

                

        return masks        return masks

        

    def _calculate_texture_score(self, elevation_patch: np.ndarray) -> float:    def _calculate_texture_score(self, elevation_patch: np.ndarray) -> float:

        """        """

        Calculate texture score using local binary patterns        Calculate texture score using local binary patterns

        Natural seabed has more texture than artificially smoothed areas        Natural seabed has more texture than artificially smoothed areas

        """        """

        if np.all(np.isnan(elevation_patch)) or elevation_patch.size < 9:        if np.all(np.isnan(elevation_patch)) or elevation_patch.size < 9:

            return 0.0            return 0.0

                

        # Fill NaN values for LBP calculation        # Fill NaN values for LBP calculation

        filled_patch = elevation_patch.copy()        filled_patch = elevation_patch.copy()

        filled_patch[np.isnan(filled_patch)] = np.nanmean(elevation_patch)        filled_patch[np.isnan(filled_patch)] = np.nanmean(elevation_patch)

                

        # Normalize to 0-255 for LBP        # Normalize to 0-255 for LBP

        normalized = ((filled_patch - np.min(filled_patch)) /         normalized = ((filled_patch - np.min(filled_patch)) / 

                     (np.max(filled_patch) - np.min(filled_patch) + 1e-6) * 255).astype(np.uint8)                     (np.max(filled_patch) - np.min(filled_patch) + 1e-6) * 255).astype(np.uint8)

                

        # Calculate Local Binary Pattern        # Calculate Local Binary Pattern

        radius = 1        radius = 1

        n_points = 8 * radius        n_points = 8 * radius

        lbp = local_binary_pattern(normalized, n_points, radius, method='uniform')        lbp = local_binary_pattern(normalized, n_points, radius, method='uniform')

                

        # Calculate texture measure as entropy of LBP histogram        # Calculate texture measure as entropy of LBP histogram

        hist, _ = np.histogram(lbp, bins=n_points + 2, range=(0, n_points + 1))        hist, _ = np.histogram(lbp, bins=n_points + 2, range=(0, n_points + 1))

        hist = hist / np.sum(hist)  # Normalize        hist = hist / np.sum(hist)  # Normalize

                

        # Calculate entropy (high entropy = more texture)        # Calculate entropy (high entropy = more texture)

        entropy = -np.sum(hist * np.log(hist + 1e-10))        entropy = -np.sum(hist * np.log(hist + 1e-10))

                

        # Normalize to 0-1 scale        # Normalize to 0-1 scale

        max_entropy = np.log(n_points + 2)        max_entropy = np.log(n_points + 2)

        return entropy / max_entropy        return entropy / max_entropy

        

    def _calculate_edge_sharpness(self, elevation_data: np.ndarray, mask: np.ndarray) -> float:    def _calculate_edge_sharpness(self, elevation_data: np.ndarray, mask: np.ndarray) -> float:

        """        """

        Calculate how sharp the edges of a region are        Calculate how sharp the edges of a region are

        Artificial scrubbing often creates unnaturally sharp boundaries        Artificial scrubbing often creates unnaturally sharp boundaries

        """        """

        # Get edge pixels using morphological operations        # Get edge pixels using morphological operations

        eroded = ndimage.binary_erosion(mask)        eroded = ndimage.binary_erosion(mask)

        edge_mask = mask & ~eroded        edge_mask = mask & ~eroded

                

        if np.sum(edge_mask) == 0:        if np.sum(edge_mask) == 0:

            return 0.0            return 0.0

                

        # Calculate gradient magnitude at edge pixels        # Calculate gradient magnitude at edge pixels

        grad_x = np.gradient(elevation_data, axis=1)        grad_x = np.gradient(elevation_data, axis=1)

        grad_y = np.gradient(elevation_data, axis=0)        grad_y = np.gradient(elevation_data, axis=0)

        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)

                

        edge_gradients = grad_magnitude[edge_mask]        edge_gradients = grad_magnitude[edge_mask]

        edge_gradients = edge_gradients[~np.isnan(edge_gradients)]        edge_gradients = edge_gradients[~np.isnan(edge_gradients)]

                

        if len(edge_gradients) == 0:        if len(edge_gradients) == 0:

            return 0.0            return 0.0

                

        # High mean gradient at edges indicates sharp boundaries        # High mean gradient at edges indicates sharp boundaries

        mean_edge_gradient = np.mean(edge_gradients)        mean_edge_gradient = np.mean(edge_gradients)

                

        # Normalize based on typical seabed gradient values        # Normalize based on typical seabed gradient values

        # Natural seabed rarely has gradients > 0.5 m/pixel        # Natural seabed rarely has gradients > 0.5 m/pixel

        return min(1.0, mean_edge_gradient / 0.5)        return min(1.0, mean_edge_gradient / 0.5)

        

    def comprehensive_scrub_analysis(self, elevation_data: np.ndarray,    def comprehensive_scrub_analysis(self, elevation_data: np.ndarray,

                                   uncertainty_data: np.ndarray = None,                                   uncertainty_data: np.ndarray = None,

                                   pixel_size_m: float = 2.0) -> Dict[str, Any]:                                   pixel_size_m: float = 2.0) -> Dict[str, Any]:

        """        """

        Comprehensive analysis combining all detection methods        Comprehensive analysis combining all detection methods

        """        """

        results = {        results = {

            'overall_scrubbing_probability': 0.0,            'overall_scrubbing_probability': 0.0,

            'detected_patterns': []            'detected_patterns': []

        }        }

                

        # Run all detection methods        # Run all detection methods

        freighter_results = self.detect_freighter_signature(elevation_data, pixel_size_m)        freighter_results = self.detect_freighter_signature(elevation_data, pixel_size_m)

        smoothing_results = self.detect_smoothing_pattern(elevation_data)        smoothing_results = self.detect_smoothing_pattern(elevation_data)

        scrubbing_results = self.detect_wreck_scrubbing_box(elevation_data, uncertainty_data, pixel_size_m)        scrubbing_results = self.detect_wreck_scrubbing_box(elevation_data, uncertainty_data, pixel_size_m)

                

        # Combine results        # Combine results

        results.update({        results.update({

            'freighter_analysis': freighter_results,            'freighter_analysis': freighter_results,

            'smoothing_analysis': smoothing_results,            'smoothing_analysis': smoothing_results,

            'scrubbing_analysis': scrubbing_results            'scrubbing_analysis': scrubbing_results

        })        })

                

        # Calculate overall probability        # Calculate overall probability

        indicators = []        indicators = []

        weights = []        weights = []

                

        if freighter_results['freighter_likelihood'] > 0.3:        if freighter_results['freighter_likelihood'] > 0.3:

            indicators.append(freighter_results['freighter_likelihood'])            indicators.append(freighter_results['freighter_likelihood'])

            weights.append(0.4)  # High weight for ship-like signatures            weights.append(0.4)  # High weight for ship-like signatures

            results['detected_patterns'].append('freighter_signature')            results['detected_patterns'].append('freighter_signature')

                

        if smoothing_results['smoothing_confidence'] > 0.5:        if smoothing_results['smoothing_confidence'] > 0.5:

            indicators.append(smoothing_results['smoothing_confidence'])            indicators.append(smoothing_results['smoothing_confidence'])

            weights.append(0.3)  # Moderate weight for smoothing            weights.append(0.3)  # Moderate weight for smoothing

            results['detected_patterns'].append(f"smoothing_{smoothing_results['smoothing_type']}")            results['detected_patterns'].append(f"smoothing_{smoothing_results['smoothing_type']}")

                

        if scrubbing_results['scrubbing_likelihood'] > 0.4:        if scrubbing_results['scrubbing_likelihood'] > 0.4:

            indicators.append(scrubbing_results['scrubbing_likelihood'])            indicators.append(scrubbing_results['scrubbing_likelihood'])

            weights.append(0.5)  # High weight for scrubbing box pattern            weights.append(0.5)  # High weight for scrubbing box pattern

            results['detected_patterns'].append('scrubbing_box')            results['detected_patterns'].append('scrubbing_box')

                

        if indicators:        if indicators:

            weights = np.array(weights)            weights = np.array(weights)

            weights = weights / np.sum(weights)  # Normalize            weights = weights / np.sum(weights)  # Normalize

            results['overall_scrubbing_probability'] = np.average(indicators, weights=weights)            results['overall_scrubbing_probability'] = np.average(indicators, weights=weights)

                

        return results        return results
