#!/usr/bin/env python3
"""
Optimized BAG File Scanner & Feature Rebuilder
Uses rasterio for high-performance BAG file processing
Scans for masked/redacted features and attempts reconstruction
"""

import os
import sys
import logging
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.features import shapes
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from datetime import datetime
import json
from shapely.geometry import shape, Point
from scipy import ndimage
import warnings
warnings.filterwarnings('ignore')

# Try to import cv2, use fallback if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available, some features will be limited")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedBagScanner:
    """High-performance BAG file scanner with feature reconstruction"""

    def __init__(self, bag_directory="bagfiles"):
        self.bag_directory = Path(bag_directory)
        self.results = {
            "scan_timestamp": datetime.now().isoformat(),
            "files_processed": [],
            "features_detected": [],
            "masked_areas_found": [],
            "reconstruction_attempts": [],
            "visualizations_created": []
        }

    def scan_all_bag_files(self):
        """Scan all BAG files in the directory"""
        bag_files = list(self.bag_directory.glob("*.bag"))
        logger.info(f"Found {len(bag_files)} BAG files to process")

        for bag_file in bag_files:
            try:
                logger.info(f"Processing: {bag_file.name}")
                self.process_bag_file(bag_file)
            except Exception as e:
                logger.error(f"Failed to process {bag_file.name}: {e}")

        self.save_results()

    def process_bag_file(self, bag_path):
        """Process a single BAG file for masked features and reconstruction"""
        file_result = {
            "filename": bag_path.name,
            "path": str(bag_path),
            "dimensions": None,
            "crs": None,
            "masked_pixels": 0,
            "anomaly_regions": [],
            "reconstruction_data": []
        }

        try:
            with rasterio.open(bag_path) as dataset:
                # Get basic metadata
                file_result["dimensions"] = (dataset.height, dataset.width)
                file_result["crs"] = str(dataset.crs) if dataset.crs else None
                file_result["bounds"] = dataset.bounds
                file_result["resolution"] = dataset.res

                # Read the elevation data
                elevation_data = dataset.read(1)  # BAG files typically have elevation in band 1

                # Read uncertainty data if available (band 2)
                uncertainty_data = None
                if dataset.count >= 2:
                    uncertainty_data = dataset.read(2)

                logger.info(f"Data shape: {elevation_data.shape}, dtype: {elevation_data.dtype}")

                # Analyze for masked/redacted areas
                masked_analysis = self.analyze_masked_areas(elevation_data, uncertainty_data)

                # Look for anomaly patterns that might indicate redacted features
                anomaly_analysis = self.detect_anomaly_patterns(elevation_data, uncertainty_data)

                # Attempt reconstruction of masked areas
                reconstruction = self.attempt_reconstruction(elevation_data, masked_analysis)

                # Create visualization
                viz_path = self.create_visualization(bag_path, elevation_data, masked_analysis, anomaly_analysis)

                # Update results
                file_result.update({
                    "masked_pixels": masked_analysis["total_masked"],
                    "anomaly_regions": anomaly_analysis["regions"],
                    "reconstruction_data": reconstruction,
                    "visualization": viz_path
                })

                self.results["files_processed"].append(file_result)
                self.results["masked_areas_found"].extend(masked_analysis["regions"])
                self.results["features_detected"].extend(anomaly_analysis["regions"])
                self.results["reconstruction_attempts"].append(reconstruction)
                if viz_path:
                    self.results["visualizations_created"].append(viz_path)

        except Exception as e:
            logger.error(f"Error processing {bag_path.name}: {e}")
            file_result["error"] = str(e)
            self.results["files_processed"].append(file_result)

    def analyze_masked_areas(self, elevation_data, uncertainty_data=None):
        """Analyze data for masked or redacted areas"""
        analysis = {
            "total_masked": 0,
            "regions": [],
            "mask_types": []
        }

        # Check for NaN values (common mask indicator)
        nan_mask = np.isnan(elevation_data)
        analysis["total_masked"] += np.sum(nan_mask)

        if np.sum(nan_mask) > 0:
            analysis["mask_types"].append("NaN_values")
            # Find contiguous NaN regions
            labeled_nan, num_nan_regions = ndimage.label(nan_mask)
            for region_id in range(1, num_nan_regions + 1):
                region_mask = labeled_nan == region_id
                region_size = np.sum(region_mask)
                if region_size > 10:  # Only consider significant regions
                    y_coords, x_coords = np.where(region_mask)
                    analysis["regions"].append({
                        "type": "nan_region",
                        "size_pixels": int(region_size),
                        "bounds": [int(x_coords.min()), int(y_coords.min()), int(x_coords.max()), int(y_coords.max())],
                        "centroid": [int(x_coords.mean()), int(y_coords.mean())]
                    })

        # Check for extreme values that might indicate masking
        if uncertainty_data is not None:
            high_uncertainty = uncertainty_data > np.percentile(uncertainty_data[~np.isnan(uncertainty_data)], 95)
            analysis["total_masked"] += np.sum(high_uncertainty)

            if np.sum(high_uncertainty) > 0:
                analysis["mask_types"].append("high_uncertainty")
                labeled_uncertainty, num_uncertainty_regions = ndimage.label(high_uncertainty)
                for region_id in range(1, num_uncertainty_regions + 1):
                    region_mask = labeled_uncertainty == region_id
                    region_size = np.sum(region_mask)
                    if region_size > 50:
                        y_coords, x_coords = np.where(region_mask)
                        analysis["regions"].append({
                            "type": "high_uncertainty_region",
                            "size_pixels": int(region_size),
                            "bounds": [int(x_coords.min()), int(y_coords.min()), int(x_coords.max()), int(y_coords.max())],
                            "centroid": [int(x_coords.mean()), int(y_coords.mean())]
                        })

        # Check for uniform value regions that might be redacted
        unique_vals, counts = np.unique(elevation_data[~np.isnan(elevation_data)], return_counts=True)
        for val, count in zip(unique_vals, counts):
            if count > 1000:  # Large areas with same value
                uniform_mask = elevation_data == val
                labeled_uniform, num_uniform_regions = ndimage.label(uniform_mask)
                for region_id in range(1, num_uniform_regions + 1):
                    region_mask = labeled_uniform == region_id
                    region_size = np.sum(region_mask)
                    if region_size > 500:
                        y_coords, x_coords = np.where(region_mask)
                        analysis["regions"].append({
                            "type": "uniform_value_region",
                            "value": float(val),
                            "size_pixels": int(region_size),
                            "bounds": [int(x_coords.min()), int(y_coords.min()), int(x_coords.max()), int(y_coords.max())],
                            "centroid": [int(x_coords.mean()), int(y_coords.mean())]
                        })

        logger.info(f"Found {len(analysis['regions'])} potential masked/redacted regions")
        return analysis

    def detect_anomaly_patterns(self, elevation_data, uncertainty_data=None):
        """Detect patterns that might indicate redacted features"""
        analysis = {"regions": []}

        # Look for sharp elevation changes that might indicate feature boundaries
        if not np.all(np.isnan(elevation_data)):
            # Calculate gradients
            grad_y, grad_x = np.gradient(elevation_data)

            # Find high gradient areas (potential feature edges)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            high_gradient = gradient_magnitude > np.percentile(gradient_magnitude[~np.isnan(gradient_magnitude)], 90)

            # Look for rectangular patterns that might be redacted areas
            labeled_gradient, num_gradient_regions = ndimage.label(high_gradient)
            for region_id in range(1, num_gradient_regions + 1):
                region_mask = labeled_gradient == region_id
                region_size = np.sum(region_mask)
                if 100 < region_size < 10000:  # Medium-sized regions
                    y_coords, x_coords = np.where(region_mask)
                    width = x_coords.max() - x_coords.min()
                    height = y_coords.max() - y_coords.min()

                    # Check if roughly rectangular
                    if width > 10 and height > 10:
                        aspect_ratio = max(width, height) / min(width, height)
                        if aspect_ratio < 5:  # Not too elongated
                            analysis["regions"].append({
                                "type": "potential_feature_boundary",
                                "size_pixels": int(region_size),
                                "bounds": [int(x_coords.min()), int(y_coords.min()), int(x_coords.max()), int(y_coords.max())],
                                "dimensions": [int(width), int(height)],
                                "aspect_ratio": float(aspect_ratio)
                            })

        logger.info(f"Detected {len(analysis['regions'])} potential anomaly patterns")
        return analysis

    def attempt_reconstruction(self, elevation_data, masked_analysis):
        """Attempt to reconstruct masked/redacted areas"""
        reconstruction = {
            "attempts_made": 0,
            "successful_reconstructions": 0,
            "methods_used": [],
            "reconstructed_regions": []
        }

        for region in masked_analysis["regions"]:
            if region["type"] in ["nan_region", "uniform_value_region"]:
                reconstruction["attempts_made"] += 1

                # Try interpolation-based reconstruction
                bounds = region["bounds"]
                x1, y1, x2, y2 = bounds

                # Extract surrounding data for interpolation
                margin = 10
                context_x1 = max(0, x1 - margin)
                context_y1 = max(0, y1 - margin)
                context_x2 = min(elevation_data.shape[1], x2 + margin)
                context_y2 = min(elevation_data.shape[0], y2 + margin)

                context_data = elevation_data[context_y1:context_y2, context_x1:context_x2]

                if not np.all(np.isnan(context_data)):
                    # Simple interpolation
                    from scipy import interpolate

                    # Create mask for valid data in context
                    valid_mask = ~np.isnan(context_data)

                    if np.sum(valid_mask) > 10:  # Enough valid data for interpolation
                        y_valid, x_valid = np.where(valid_mask)
                        z_valid = context_data[valid_mask]

                        # Create interpolation function
                        try:
                            interp_func = interpolate.interp2d(x_valid, y_valid, z_valid, kind='linear')

                            # Interpolate missing values
                            y_missing, x_missing = np.where(np.isnan(context_data))
                            if len(y_missing) > 0:
                                interpolated_values = interp_func(x_missing, y_missing)

                                reconstruction["successful_reconstructions"] += 1
                                reconstruction["methods_used"].append("linear_interpolation")

                                reconstruction["reconstructed_regions"].append({
                                    "original_region": region,
                                    "interpolation_points": len(y_missing),
                                    "method": "linear_interpolation"
                                })

                        except Exception as e:
                            logger.debug(f"Interpolation failed for region: {e}")

        logger.info(f"Reconstruction attempts: {reconstruction['attempts_made']}, successful: {reconstruction['successful_reconstructions']}")
        return reconstruction

    def create_visualization(self, bag_path, elevation_data, masked_analysis, anomaly_analysis):
        """Create visualization of the BAG data with detected features"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'BAG File Analysis: {bag_path.name}', fontsize=16)

            # Original elevation data
            im1 = axes[0, 0].imshow(elevation_data, cmap='viridis', origin='upper')
            axes[0, 0].set_title('Original Elevation Data')
            plt.colorbar(im1, ax=axes[0, 0])

            # Masked areas overlay
            masked_overlay = np.zeros_like(elevation_data, dtype=float)
            for region in masked_analysis["regions"]:
                x1, y1, x2, y2 = region["bounds"]
                masked_overlay[y1:y2, x1:x2] = 1

            im2 = axes[0, 1].imshow(elevation_data, cmap='viridis', origin='upper')
            axes[0, 1].imshow(masked_overlay, cmap='Reds', alpha=0.3, origin='upper')
            axes[0, 1].set_title('Masked Areas (Red Overlay)')
            plt.colorbar(im2, ax=axes[0, 1])

            # Anomaly detection
            anomaly_overlay = np.zeros_like(elevation_data, dtype=float)
            for region in anomaly_analysis["regions"]:
                x1, y1, x2, y2 = region["bounds"]
                anomaly_overlay[y1:y2, x1:x2] = 1

            im3 = axes[1, 0].imshow(elevation_data, cmap='viridis', origin='upper')
            axes[1, 0].imshow(anomaly_overlay, cmap='Blues', alpha=0.3, origin='upper')
            axes[1, 0].set_title('Detected Anomalies (Blue Overlay)')
            plt.colorbar(im3, ax=axes[1, 0])

            # Combined view
            im4 = axes[1, 1].imshow(elevation_data, cmap='viridis', origin='upper')
            axes[1, 1].imshow(masked_overlay, cmap='Reds', alpha=0.3, origin='upper')
            axes[1, 1].imshow(anomaly_overlay, cmap='Blues', alpha=0.3, origin='upper')
            axes[1, 1].set_title('Combined Analysis')
            plt.colorbar(im4, ax=axes[1, 1])

            plt.tight_layout()

            # Save visualization
            viz_filename = f"{bag_path.stem}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            viz_path = self.bag_directory / viz_filename
            plt.savefig(viz_path, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Visualization saved: {viz_path}")
            return str(viz_path)

        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")
            return None

    def save_results(self):
        """Save comprehensive results to JSON"""
        results_file = self.bag_directory / f"bag_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"Results saved to: {results_file}")

        # Print summary
        print("\n" + "="*60)
        print("BAG FILE SCANNING & FEATURE RECONSTRUCTION RESULTS")
        print("="*60)
        print(f"Files Processed: {len(self.results['files_processed'])}")
        print(f"Total Masked Areas Found: {len(self.results['masked_areas_found'])}")
        print(f"Total Features Detected: {len(self.results['features_detected'])}")
        print(f"Reconstruction Attempts: {sum(r['attempts_made'] for r in self.results['reconstruction_attempts'])}")
        print(f"Successful Reconstructions: {sum(r['successful_reconstructions'] for r in self.results['reconstruction_attempts'])}")
        print(f"Visualizations Created: {len(self.results['visualizations_created'])}")
        print(f"Results saved to: {results_file}")
        print("="*60)

def main():
    """Main function to run the optimized BAG scanner"""
    print("🔍 OPTIMIZED BAG FILE SCANNER & FEATURE REBUILDER")
    print("=" * 60)
    print("🎯 Scanning BAG files for masked/redacted features")
    print("🔧 Attempting reconstruction using interpolation techniques")
    print("📊 Creating visualizations overlaid on bathymetric data")
    print()

    scanner = OptimizedBagScanner()
    scanner.scan_all_bag_files()

if __name__ == "__main__":
    main()