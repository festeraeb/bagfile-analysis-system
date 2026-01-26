#!/usr/bin/env python3
"""
Advanced BAG File Scanner Runner
Runs the enhanced scanner on Lake Erie BAG files with database coordination
"""

import os
import sys
import glob
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_bag_scanner import AdvancedBagScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bag_scan.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_bag_files(search_paths):
    """Find all BAG files in the specified paths"""
    bag_files = []

    for search_path in search_paths:
        if os.path.isdir(search_path):
            # Search recursively for .bag files
            pattern = os.path.join(search_path, '**', '*.bag')
            bag_files.extend(glob.glob(pattern, recursive=True))
        elif os.path.isfile(search_path) and search_path.lower().endswith('.bag'):
            bag_files.append(search_path)

    return sorted(list(set(bag_files)))  # Remove duplicates and sort

def run_advanced_scan(bag_files, output_dir, config_overrides=None):
    """Run the advanced scanner on BAG files"""

    # Default configuration
    config = {
        'min_wreck_size_sq_ft': 25.0,
        'max_wreck_size_sq_ft': 50000.0,
        'min_confidence': 0.3,
        'anomaly_threshold': 2.5,
        'skip_pattern': [3, 5, 8, 12],  # More granular multi-resolution
        'redaction_sensitivity': 0.6,
        'max_workers': min(4, len(bag_files)),  # Don't use more workers than files
        'database_path': 'wrecks.db',
        'output_kml': True,
        'output_kmz': True,
        'include_elevation_stats': True,
        'include_uncertainty_analysis': True
    }

    # Apply overrides
    if config_overrides:
        config.update(config_overrides)

    logger.info("Starting Advanced BAG File Scanner")
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    logger.info(f"Found {len(bag_files)} BAG files to process")

    # Initialize scanner
    scanner = AdvancedBagScanner(config)

    # Get database summary before scan
    pre_scan_summary = scanner.get_database_summary()
    logger.info(f"Database before scan: {pre_scan_summary['total_scans']} scans, "
               f"{pre_scan_summary['total_candidates']} candidates, "
               f"{pre_scan_summary['total_signatures']} signatures")

    # Run batch scan
    start_time = datetime.now()
    results = scanner.batch_scan(bag_files, output_dir)
    end_time = datetime.now()

    # Get database summary after scan
    post_scan_summary = scanner.get_database_summary()

    # Calculate statistics
    total_time = (end_time - start_time).total_seconds()
    successful_scans = results['successful_scans']
    total_files = results['total_files']

    logger.info("=" * 60)
    logger.info("SCAN COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Successful scans: {successful_scans}")
    logger.info(f"Success rate: {successful_scans/total_files*100:.1f}%" if total_files > 0 else "N/A")
    logger.info(f"Total processing time: {total_time:.1f} seconds")
    logger.info(f"Average time per file: {total_time/total_files:.1f} seconds" if total_files > 0 else "N/A")
    logger.info(f"New candidates found: {results['total_candidates']}")
    logger.info(f"Redaction signatures detected: {results['total_signatures']}")
    logger.info(f"Database growth: +{post_scan_summary['total_candidates'] - pre_scan_summary['total_candidates']} candidates")

    # Print top candidates
    if results['total_candidates'] > 0:
        logger.info("\nTop 5 Candidates by Confidence:")
        all_candidates = []
        for result in results['results']:
            if result.get('success') and 'candidates' in result:
                for candidate in result['candidates']:
                    candidate['file'] = result['file']
                    all_candidates.append(candidate)

        # Sort by confidence
        all_candidates.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        for i, candidate in enumerate(all_candidates[:5]):
            logger.info(f"  {i+1}. {candidate['file']}: "
                       f"({candidate['latitude']:.6f}, {candidate['longitude']:.6f}) "
                       f"conf={candidate['confidence']:.3f} "
                       f"size={candidate['size_sq_meters']:.1f}m²")

    # Print redaction signature summary
    if results['total_signatures'] > 0:
        logger.info("\nRedaction Signature Summary:")
        signature_types = {}
        redactor_ids = set()

        for result in results['results']:
            if result.get('success') and 'redaction_signatures' in result:
                for sig in result['redaction_signatures']:
                    sig_type = sig.get('signature_type', 'unknown')
                    signature_types[sig_type] = signature_types.get(sig_type, 0) + 1

                    if sig.get('redactor_id'):
                        redactor_ids.add(sig['redactor_id'])

        for sig_type, count in signature_types.items():
            logger.info(f"  {sig_type}: {count} detections")

        if redactor_ids:
            logger.info(f"  Identified redactors: {sorted(redactor_ids)}")

    return results

def main():
    parser = argparse.ArgumentParser(
        description="Advanced BAG File Scanner with Redaction Signature Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan all BAG files in Lake Erie directory
  python advanced_bag_scanner_runner.py "Lake Erie Bag Files"

  # Scan specific files with custom settings
  python advanced_bag_scanner_runner.py F00864_MB_4m_LWD_1of1.bag H13607_MB_50cm_LWD_1of1.bag --min-confidence 0.5 --output-dir results

  # High-sensitivity scan for redaction detection
  python advanced_bag_scanner_runner.py "Lake Erie Bag Files" --redaction-sensitivity 0.4 --anomaly-threshold 2.0
        """
    )

    parser.add_argument(
        'bag_files',
        nargs='+',
        help='BAG files or directories containing BAG files'
    )

    parser.add_argument(
        '--output-dir', '-o',
        default='advanced_scan_results',
        help='Output directory for results (default: advanced_scan_results)'
    )

    parser.add_argument(
        '--min-confidence', '-c',
        type=float,
        default=0.3,
        help='Minimum confidence threshold (default: 0.3)'
    )

    parser.add_argument(
        '--min-size',
        type=float,
        default=25.0,
        help='Minimum wreck size in square feet (default: 25.0)'
    )

    parser.add_argument(
        '--max-size',
        type=float,
        default=50000.0,
        help='Maximum wreck size in square feet (default: 50000.0)'
    )

    parser.add_argument(
        '--anomaly-threshold',
        type=float,
        default=2.5,
        help='Z-score threshold for anomaly detection (default: 2.5)'
    )

    parser.add_argument(
        '--redaction-sensitivity',
        type=float,
        default=0.6,
        help='Sensitivity for redaction signature detection (default: 0.6)'
    )

    parser.add_argument(
        '--max-workers', '-w',
        type=int,
        default=None,
        help='Maximum number of worker threads (default: min(4, num_files))'
    )

    parser.add_argument(
        '--no-kml',
        action='store_true',
        help='Skip KML output generation'
    )

    parser.add_argument(
        '--no-kmz',
        action='store_true',
        help='Skip KMZ output generation'
    )

    parser.add_argument(
        '--database',
        default='wrecks.db',
        help='Database file path (default: wrecks.db)'
    )

    args = parser.parse_args()

    # Find BAG files
    bag_files = find_bag_files(args.bag_files)

    if not bag_files:
        logger.error("No BAG files found!")
        sys.exit(1)

    logger.info(f"Found {len(bag_files)} BAG files:")
    for bag_file in bag_files:
        logger.info(f"  {bag_file}")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Prepare configuration overrides
    config_overrides = {
        'min_confidence': args.min_confidence,
        'min_wreck_size_sq_ft': args.min_size,
        'max_wreck_size_sq_ft': args.max_size,
        'anomaly_threshold': args.anomaly_threshold,
        'redaction_sensitivity': args.redaction_sensitivity,
        'database_path': args.database,
        'output_kml': not args.no_kml,
        'output_kmz': not args.no_kmz
    }

    if args.max_workers:
        config_overrides['max_workers'] = args.max_workers

    # Run the scan
    try:
        results = run_advanced_scan(bag_files, str(output_dir), config_overrides)

        # Save detailed results
        results_file = output_dir / f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\nDetailed results saved to: {results_file}")

        # Print output files
        logger.info("\nGenerated output files:")
        for result in results['results']:
            if result.get('success') and 'outputs' in result:
                for output_type, output_path in result['outputs'].items():
                    logger.info(f"  {output_path} ({output_type.upper()})")

    except KeyboardInterrupt:
        logger.info("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()</content>
<parameter name="filePath">c:\Temp\Garminjunk\HistoryofCESARSNIFFERBAGFILE\bagfilework\advanced_bag_scanner_runner.py