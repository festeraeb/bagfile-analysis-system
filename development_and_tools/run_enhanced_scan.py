"""
Runner script for the enhanced wreck scanner focusing on the Straits of Mackinac.
This is a cleaned, deduplicated copy saved into development_and_tools.
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Local imports (assumes these modules are available in the workspace)
from enhanced_wreck_scanner import WreckSignatureDetector, ScanConfig
from scrub_detection_engine import ScrubDetectionEngine


def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def run_focused_scan():
    """Run a focused scan on the Straits of Mackinac using known training wrecks and patterns."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Enhanced Wreck Scanner for Straits of Mackinac")
    logger.info("=" * 60)

    # Configuration focusing on the area of interest
    config = ScanConfig(
        base_dir=r"c:\Temp\bagfilework",
        bag_dir=r"c:\Temp\bagfilework",
        output_dir=r"c:\Temp\bagfilework\enhanced_scan_results",
        bounds={
            'west': -85.50, 'east': -84.40,
            'south': 45.70, 'north': 46.00
        },
        # Optimized parameters
        tile_size_m=25,
        overlap_ratio=0.6,
        elevation_change_threshold=1.2,
        uncertainty_anomaly_threshold=500.0,
        smoothing_threshold=0.4,
        min_wreck_length_m=40,
        max_wreck_length_m=300,
        min_wreck_width_m=10,
        max_wreck_width_m=45,
        max_workers=2,
        chunk_size_mb=50
    )

    # Create detector with specialized configuration
    detector = WreckSignatureDetector(config)

    # Initialize scrub detection engine and attach
    scrub_engine = ScrubDetectionEngine()
    detector.scrub_engine = scrub_engine

    # Find BAG/TIF files
    bag_files = []
    bag_dir = Path(config.bag_dir)

    for pattern in ['*.bag', '*.tif']:
        found_files = list(bag_dir.glob(pattern))
        bag_files.extend(found_files)
        logger.info(f"Found {len(found_files)} {pattern} files")

    if not bag_files:
        logger.error(f"No BAG files found in {config.bag_dir}")
        logger.info("Available files:")
        for file in bag_dir.iterdir():
            if file.is_file():
                logger.info(f"  {file.name}")
        return

    logger.info(f"Total files to process: {len(bag_files)}")
    logger.info("Files found:")
    for f in bag_files:
        logger.info(f"  {f.name}")

    # Process files
    all_results = []

    for i, bag_file in enumerate(bag_files, 1):
        logger.info(f"\n[{i}/{len(bag_files)}] Processing: {bag_file.name}")
        try:
            results = detector.scan_bag_file(str(bag_file))
            if results:
                logger.info(f"  Generated {len(results)} analysis results")
                all_results.extend(results)
            else:
                logger.warning(f"  No results from {bag_file.name}")
        except Exception as e:
            logger.error(f"  Failed to process {bag_file.name}: {str(e)}")
            continue

    if not all_results:
        logger.error("No results generated from any files!")
        return

    logger.info(f"\nTotal analysis results: {len(all_results)}")

    # Train models
    logger.info("Training detection models...")
    detector.train_models(all_results)

    # Score results
    logger.info("Scoring results...")
    scored_results = detector.score_results(all_results)

    # Export results
    logger.info("Exporting results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    detector.export_results(scored_results, f"mackinac_enhanced_scan_{timestamp}")

    # Summary statistics
    high_anomaly = [r for r in scored_results if r.get('anomaly_score', -999) > -0.1]
    high_wreck_prob = [r for r in scored_results if r.get('wreck_probability', 0) > 0.3]
    near_known_wrecks = [r for r in scored_results if r.get('distance_to_nearest_wreck', float('inf')) < 200]

    logger.info("\n" + "=" * 60)
    logger.info("SCAN SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total tiles analyzed: {len(scored_results)}")
    logger.info(f"High anomaly tiles: {len(high_anomaly)} ({len(high_anomaly)/len(scored_results)*100:.1f}%)")
    logger.info(f"High wreck probability: {len(high_wreck_prob)} ({len(high_wreck_prob)/len(scored_results)*100:.1f}%)")
    logger.info(f"Near known wrecks (<200m): {len(near_known_wrecks)}")

    # Report on specific training areas
    elva_area = [r for r in scored_results if r.get('nearest_wreck') == 'Elva' and r.get('distance_to_nearest_wreck', 0) < 100]
    if elva_area:
        avg_anomaly = sum(r.get('anomaly_score', 0) for r in elva_area) / len(elva_area)
        logger.info(f"Elva training area: {len(elva_area)} tiles, avg anomaly score: {avg_anomaly:.3f}")

    logger.info(f"\nResults saved to: {config.output_dir}")
    logger.info("Check the KML file for high-confidence detections!")


if __name__ == "__main__":
    run_focused_scan()
