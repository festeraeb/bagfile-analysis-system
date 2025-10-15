#!/usr/bin/env python3
"""
Enhanced BAG Scanner with Feature Reconstruction
Scans corrected BAG files for masked features and rebuilds them
"""

import os
import sys
import logging
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.features import shapes
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from pathlib import Path
from datetime import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from scipy import ndimage
from scipy.interpolate import griddata
from shapely.geometry import shape, Polygon, MultiPolygon
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBagScanner:
    """Enhanced BAG scanner with feature reconstruction capabilities"""

    def __init__(self, bag_directory="bagfiles"):
        self.bag_directory = Path(bag_directory)
        self.corrected_directory = self.bag_directory / "corrected"
        self.reconstructed_directory = self.bag_directory / "reconstructed"
        self.reconstructed_directory.mkdir(exist_ok=True)

        # Define common BAG no-data values
        self.nodata_values = [-9999, -9999.0, np.nan, None]

        # Color scheme for visualization
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    def scan_corrected_files(self):
        """Scan all corrected BAG files for masked features"""
        logger.info("🔍 Scanning corrected BAG files for masked features")

        corrected_files = list(self.corrected_directory.glob("*.bag"))
        if not corrected_files:
            logger.warning("No corrected BAG files found. Run alignment corrector first.")
            return []

        scan_results = []
        for bag_file in corrected_files:
            logger.info(f"Scanning {bag_file.name}")
            result = self.scan_single_file(bag_file)
            if result:
                scan_results.append(result)

        return scan_results

    def scan_single_file(self, bag_path):
        """Scan a single BAG file for masked features"""
        try:
            with rasterio.open(bag_path) as src:
                # Read elevation data
                elevation = src.read(1)

                # Create mask for valid data (not nodata)
                valid_mask = self._create_valid_mask(elevation, src.nodata)

                # Find masked regions (holes in valid data)
                masked_regions = self._find_masked_regions(valid_mask)

                # Analyze each masked region
                features = []
                for region in masked_regions:
                    feature_info = self._analyze_masked_region(
                        region, elevation, src.transform, src.crs
                    )
                    if feature_info:
                        features.append(feature_info)

                return {
                    "file": bag_path.name,
                    "path": str(bag_path),
                    "features_found": len(features),
                    "features": features,
                    "metadata": {
                        "bounds": list(src.bounds),
                        "resolution": list(src.res),
                        "crs": str(src.crs),
                        "shape": list(elevation.shape)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to scan {bag_path.name}: {e}")
            return None

    def _create_valid_mask(self, elevation, nodata):
        """Create mask for valid (non-nodata) elevation values"""
        if nodata is not None:
            valid_mask = ~np.isnan(elevation) & (elevation != nodata)
        else:
            valid_mask = ~np.isnan(elevation)

        # Also mask out extreme values that might indicate masking
        valid_mask &= (elevation > -1000) & (elevation < 1000)

        return valid_mask.astype(bool)

    def _find_masked_regions(self, valid_mask):
        """Find contiguous masked regions in the data"""
        # Invert mask to find holes (masked areas)
        masked_mask = ~valid_mask

        # Label connected components
        labeled_mask, num_features = ndimage.label(masked_mask)

        regions = []
        for label in range(1, num_features + 1):
            region_mask = labeled_mask == label
            if np.sum(region_mask) > 10:  # Minimum size threshold
                regions.append(region_mask)

        return regions

    def _analyze_masked_region(self, region_mask, elevation, transform, crs):
        """Analyze a single masked region for reconstruction potential"""
        # Get region bounds
        rows, cols = np.where(region_mask)
        min_row, max_row = rows.min(), rows.max()
        min_col, max_col = cols.min(), cols.max()

        # Convert to geographic coordinates
        bounds = rasterio.transform.array_bounds(
            region_mask.shape[0], region_mask.shape[1], transform
        )

        # Calculate region properties
        area_pixels = np.sum(region_mask)
        region_shape = (max_row - min_row + 1, max_col - min_col + 1)

        # Check if region is reconstructible (has surrounding valid data)
        reconstructible = self._check_reconstruction_potential(
            region_mask, elevation, min_row, max_row, min_col, max_col
        )

        return {
            "bounds_pixels": [min_row, max_row, min_col, max_col],
            "bounds_geo": bounds,
            "area_pixels": int(area_pixels),
            "shape": list(region_shape),
            "reconstructible": reconstructible,
            "confidence": self._calculate_confidence(region_mask, elevation)
        }

    def _check_reconstruction_potential(self, region_mask, elevation, min_row, max_row, min_col, max_col):
        """Check if a masked region can be reconstructed from surrounding data"""
        # Expand region by 2 pixels to check surroundings
        expanded_min_row = max(0, min_row - 2)
        expanded_max_row = min(elevation.shape[0] - 1, max_row + 2)
        expanded_min_col = max(0, min_col - 2)
        expanded_max_col = min(elevation.shape[1] - 1, max_col + 2)

        # Extract surrounding data
        surrounding = elevation[expanded_min_row:expanded_max_row+1,
                               expanded_min_col:expanded_max_col+1]

        # Check if there's enough valid surrounding data
        valid_surrounding = ~np.isnan(surrounding) & (surrounding != -9999)
        surrounding_coverage = np.sum(valid_surrounding) / surrounding.size

        return surrounding_coverage > 0.3  # At least 30% valid surrounding data

    def _calculate_confidence(self, region_mask, elevation):
        """Calculate reconstruction confidence based on region characteristics"""
        # Simple confidence based on region size and shape
        area = np.sum(region_mask)
        perimeter = self._calculate_perimeter(region_mask)

        if perimeter == 0:
            return 0.0

        # Compactness ratio (circle would have highest compactness)
        compactness = 4 * np.pi * area / (perimeter ** 2)

        # Size factor (larger regions are harder to reconstruct accurately)
        size_factor = min(1.0, 1000 / area)

        confidence = (compactness + size_factor) / 2
        return min(1.0, max(0.0, confidence))

    def _calculate_perimeter(self, mask):
        """Calculate perimeter of a masked region"""
        # Use morphological operations to find boundary
        eroded = ndimage.binary_erosion(mask)
        boundary = mask & ~eroded
        return np.sum(boundary)

    def reconstruct_features(self, scan_results):
        """Reconstruct masked features using interpolation"""
        logger.info("🔄 Reconstructing masked features")

        reconstruction_results = []

        for result in scan_results:
            bag_path = Path(result["path"])
            logger.info(f"Reconstructing features in {bag_path.name}")

            try:
                with rasterio.open(bag_path) as src:
                    elevation = src.read(1)

                    # Create output array
                    reconstructed = elevation.copy()

                    # Process each feature
                    features_reconstructed = 0
                    for i, feature in enumerate(result["features"]):
                        if feature["reconstructible"] and feature["confidence"] > 0.3:
                            reconstructed = self._reconstruct_single_feature(
                                reconstructed, feature, elevation
                            )
                            features_reconstructed += 1

                    # Save reconstructed file
                    output_path = self.reconstructed_directory / f"{bag_path.stem}_reconstructed.bag"

                    profile = src.profile.copy()
                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(reconstructed, 1)
                        if src.count > 1:  # Copy uncertainty band if present
                            dst.write(src.read(2), 2)

                    reconstruction_results.append({
                        "file": bag_path.name,
                        "output_file": output_path.name,
                        "features_reconstructed": features_reconstructed,
                        "total_features": len(result["features"])
                    })

            except Exception as e:
                logger.error(f"Failed to reconstruct {bag_path.name}: {e}")

        return reconstruction_results

    def _reconstruct_single_feature(self, reconstructed, feature, original_elevation):
        """Reconstruct a single masked feature using interpolation"""
        min_row, max_row, min_col, max_col = feature["bounds_pixels"]

        # Extract region
        region = reconstructed[min_row:max_row+1, min_col:max_col+1]
        original_region = original_elevation[min_row:max_row+1, min_col:max_col+1]

        # Create mask for the specific feature within this region
        # This is a simplified approach - in practice you'd need more sophisticated
        # feature identification within the bounds
        masked_area = np.isnan(region) | (region == -9999)

        if not np.any(masked_area):
            return reconstructed

        # Get valid surrounding points for interpolation
        valid_mask = ~masked_area
        valid_points = np.array(np.where(valid_mask)).T
        valid_values = region[valid_mask]

        # Get points to interpolate
        masked_points = np.array(np.where(masked_area)).T

        if len(valid_points) < 3:
            # Not enough points for interpolation, use nearest neighbor
            for point in masked_points:
                distances = np.sqrt(np.sum((valid_points - point) ** 2, axis=1))
                nearest_idx = np.argmin(distances)
                region[tuple(point)] = valid_values[nearest_idx]
        else:
            # Use linear interpolation
            try:
                interpolated = griddata(
                    valid_points, valid_values, masked_points,
                    method='linear', fill_value=np.nan
                )

                # Fill any remaining NaNs with nearest neighbor
                nan_mask = np.isnan(interpolated)
                if np.any(nan_mask):
                    nearest = griddata(
                        valid_points, valid_values, masked_points[nan_mask],
                        method='nearest'
                    )
                    interpolated[nan_mask] = nearest

                # Apply interpolated values
                for i, point in enumerate(masked_points):
                    region[tuple(point)] = interpolated[i]

            except Exception:
                # Fallback to nearest neighbor
                for point in masked_points:
                    distances = np.sqrt(np.sum((valid_points - point) ** 2, axis=1))
                    nearest_idx = np.argmin(distances)
                    region[tuple(point)] = valid_values[nearest_idx]

        # Update the reconstructed array
        reconstructed[min_row:max_row+1, min_col:max_col+1] = region

        return reconstructed

    def create_visualization(self, scan_results, reconstruction_results):
        """Create visualization of scan and reconstruction results"""
        logger.info("📊 Creating visualization of results")

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('BAG File Feature Reconstruction Analysis', fontsize=16)

        # Plot 1: Feature distribution
        self._plot_feature_distribution(scan_results, axes[0, 0])

        # Plot 2: Reconstruction success
        self._plot_reconstruction_success(reconstruction_results, axes[0, 1])

        # Plot 3: Confidence distribution
        self._plot_confidence_distribution(scan_results, axes[1, 0])

        # Plot 4: Sample elevation profile
        self._plot_sample_elevation(scan_results, axes[1, 1])

        plt.tight_layout()

        # Save visualization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        viz_path = self.bag_directory / f"reconstruction_analysis_{timestamp}.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Visualization saved to {viz_path}")
        return str(viz_path)

    def _plot_feature_distribution(self, scan_results, ax):
        """Plot distribution of features found per file"""
        files = [r["file"] for r in scan_results]
        features = [r["features_found"] for r in scan_results]

        ax.bar(range(len(files)), features, color=self.colors[0])
        ax.set_xticks(range(len(files)))
        ax.set_xticklabels([f[:20] + "..." if len(f) > 20 else f for f in files], rotation=45, ha='right')
        ax.set_ylabel('Features Found')
        ax.set_title('Masked Features per File')
        ax.grid(True, alpha=0.3)

    def _plot_reconstruction_success(self, reconstruction_results, ax):
        """Plot reconstruction success rates"""
        if not reconstruction_results:
            ax.text(0.5, 0.5, 'No reconstruction data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Reconstruction Success')
            return

        files = [r["file"] for r in reconstruction_results]
        success_rates = [r["features_reconstructed"] / max(1, r["total_features"]) for r in reconstruction_results]

        ax.bar(range(len(files)), success_rates, color=self.colors[1])
        ax.set_xticks(range(len(files)))
        ax.set_xticklabels([f[:15] + "..." if len(f) > 15 else f for f in files], rotation=45, ha='right')
        ax.set_ylabel('Success Rate')
        ax.set_title('Reconstruction Success Rate')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

    def _plot_confidence_distribution(self, scan_results, ax):
        """Plot distribution of reconstruction confidence"""
        all_confidences = []
        for result in scan_results:
            all_confidences.extend([f["confidence"] for f in result["features"]])

        if all_confidences:
            ax.hist(all_confidences, bins=20, alpha=0.7, color=self.colors[2], edgecolor='black')
            ax.set_xlabel('Confidence Score')
            ax.set_ylabel('Frequency')
            ax.set_title('Reconstruction Confidence Distribution')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No confidence data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Reconstruction Confidence')

    def _plot_sample_elevation(self, scan_results, ax):
        """Plot sample elevation profile from first file"""
        if not scan_results:
            ax.text(0.5, 0.5, 'No elevation data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Sample Elevation Profile')
            return

        # Load first file for sample profile
        first_result = scan_results[0]
        bag_path = Path(first_result["path"])

        try:
            with rasterio.open(bag_path) as src:
                elevation = src.read(1)

                # Take a profile across the middle
                mid_row = elevation.shape[0] // 2
                profile = elevation[mid_row, :]

                # Mask nodata values
                valid = ~np.isnan(profile) & (profile != -9999)
                x_coords = np.arange(len(profile))[valid]
                y_values = profile[valid]

                ax.plot(x_coords, y_values, color=self.colors[3], linewidth=1)
                ax.set_xlabel('Pixel Position')
                ax.set_ylabel('Elevation (m)')
                ax.set_title(f'Elevation Profile: {first_result["file"][:20]}...')
                ax.grid(True, alpha=0.3)

        except Exception as e:
            ax.text(0.5, 0.5, f'Error loading data:\n{str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Sample Elevation Profile')

    def save_results(self, scan_results, reconstruction_results, visualization_path):
        """Save comprehensive results to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        results = {
            "timestamp": timestamp,
            "scan_results": scan_results,
            "reconstruction_results": reconstruction_results,
            "visualization": visualization_path,
            "summary": {
                "total_files_scanned": len(scan_results),
                "total_features_found": sum(r["features_found"] for r in scan_results),
                "total_features_reconstructed": sum(r["features_reconstructed"] for r in reconstruction_results),
                "reconstruction_success_rate": (
                    sum(r["features_reconstructed"] for r in reconstruction_results) /
                    max(1, sum(r["total_features"] for r in reconstruction_results))
                )
            }
        }

        results_path = self.bag_directory / f"reconstruction_results_{timestamp}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {results_path}")
        return str(results_path)

def main():
    """Main execution function"""
    print("🔍 ENHANCED BAG SCANNER WITH FEATURE RECONSTRUCTION")
    print("=" * 55)
    print("🎯 Scanning corrected BAG files for masked features")
    print("🔄 Reconstructing features using interpolation")
    print("📊 Creating comprehensive analysis and visualization")
    print()

    scanner = EnhancedBagScanner()

    # Scan corrected files
    scan_results = scanner.scan_corrected_files()

    if not scan_results:
        print("❌ No corrected BAG files found or scanning failed")
        return

    print(f"✅ Scanned {len(scan_results)} files")
    total_features = sum(r["features_found"] for r in scan_results)
    print(f"🔍 Found {total_features} masked features across all files")

    # Reconstruct features
    reconstruction_results = scanner.reconstruct_features(scan_results)

    print(f"🔄 Reconstructed features in {len(reconstruction_results)} files")

    # Create visualization
    viz_path = scanner.create_visualization(scan_results, reconstruction_results)

    # Save results
    results_path = scanner.save_results(scan_results, reconstruction_results, viz_path)

    print()
    print("📊 ANALYSIS SUMMARY")
    print("=" * 20)
    for result in scan_results:
        print(f"📁 {result['file']}: {result['features_found']} features")

    print()
    print("💾 OUTPUT FILES")
    print("=" * 15)
    print(f"🔄 Reconstructed BAGs: {scanner.reconstructed_directory}")
    print(f"📊 Visualization: {viz_path}")
    print(f"📋 Results JSON: {results_path}")

    print()
    print("✅ Enhanced BAG scanning and reconstruction completed!")

if __name__ == "__main__":
    main()