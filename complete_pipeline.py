#!/usr/bin/env python3
"""
Complete Wreck Detection Pipeline
Combines advanced scanning with database coordination for comprehensive results
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_bag_scanner_runner import run_advanced_scan, find_bag_files
from database_coordinator import DatabaseCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wreck_detection_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_complete_pipeline(bag_files, output_dir, config_overrides=None):
    """Run the complete wreck detection pipeline"""

    logger.info("=" * 80)
    logger.info("STARTING COMPLETE WRECK DETECTION PIPELINE")
    logger.info("=" * 80)

    pipeline_start = datetime.now()

    # Phase 1: Advanced BAG File Scanning
    logger.info("\n" + "="*50)
    logger.info("PHASE 1: ADVANCED BAG FILE SCANNING")
    logger.info("="*50)

    scan_results = run_advanced_scan(bag_files, output_dir, config_overrides)

    # Phase 2: Database Coordination
    logger.info("\n" + "="*50)
    logger.info("PHASE 2: DATABASE COORDINATION")
    logger.info("="*50)

    coordinator = DatabaseCoordinator()

    # Coordinate targets across scans
    coordination_results = coordinator.coordinate_targets(max_distance_meters=50.0)

    # Phase 3: Export Coordinated Results
    logger.info("\n" + "="*50)
    logger.info("PHASE 3: EXPORT COORDINATED RESULTS")
    logger.info("="*50)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Export KML
    kml_file = os.path.join(output_dir, f"coordinated_targets_{timestamp}.kml")
    coordinator.export_coordinated_targets(kml_file, format='kml')

    # Export KMZ
    kmz_file = os.path.join(output_dir, f"coordinated_targets_{timestamp}.kmz")
    coordinator.export_coordinated_targets(kmz_file, format='kmz')

    # Phase 4: Generate Summary Report
    logger.info("\n" + "="*50)
    logger.info("PHASE 4: GENERATE SUMMARY REPORT")
    logger.info("="*50)

    summary = generate_pipeline_summary(scan_results, coordination_results, output_dir, timestamp)

    # Final Statistics
    pipeline_end = datetime.now()
    total_time = (pipeline_end - pipeline_start).total_seconds()

    logger.info("\n" + "="*80)
    logger.info("PIPELINE COMPLETE")
    logger.info("="*80)
    logger.info(f"Total execution time: {total_time:.1f} seconds")
    logger.info(f"Files processed: {scan_results['total_files']}")
    logger.info(f"Successful scans: {scan_results['successful_scans']}")
    logger.info(f"Candidates found: {scan_results['total_candidates']}")
    logger.info(f"Redaction signatures: {scan_results['total_signatures']}")
    logger.info(f"Coordinated targets: {coordination_results['coordinated_targets']}")
    logger.info(f"Target clusters: {coordination_results['clusters']}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Summary report: {summary['summary_file']}")

    return {
        'scan_results': scan_results,
        'coordination_results': coordination_results,
        'summary': summary,
        'total_time_seconds': total_time,
        'output_files': summary['output_files']
    }

def generate_pipeline_summary(scan_results, coordination_results, output_dir, timestamp):
    """Generate comprehensive pipeline summary"""

    summary_file = os.path.join(output_dir, f"pipeline_summary_{timestamp}.txt")

    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("COMPLETE WRECK DETECTION PIPELINE SUMMARY\n")
        f.write("="*80 + "\n\n")

        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Scan Phase Summary
        f.write("PHASE 1: ADVANCED BAG FILE SCANNING\n")
        f.write("-" * 40 + "\n")
        f.write(f"Files processed: {scan_results['total_files']}\n")
        f.write(f"Successful scans: {scan_results['successful_scans']}\n")
        f.write(f"Success rate: {scan_results['successful_scans']/scan_results['total_files']*100:.1f}%\n" if scan_results['total_files'] > 0 else "Success rate: N/A\n")
        f.write(f"Total candidates: {scan_results['total_candidates']}\n")
        f.write(f"Redaction signatures: {scan_results['total_signatures']}\n\n")

        # Individual file results
        f.write("Individual File Results:\n")
        for result in scan_results['results']:
            status = "✅" if result.get('success') else "❌"
            candidates = result.get('total_candidates', 0)
            signatures = result.get('total_signatures', 0)
            f.write(f"  {status} {result['file']}: {candidates} candidates, {signatures} signatures\n")
        f.write("\n")

        # Coordination Phase Summary
        f.write("PHASE 2: DATABASE COORDINATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Coordinated targets: {coordination_results['coordinated_targets']}\n")
        f.write(f"Target clusters: {coordination_results['clusters']}\n")

        cluster_summary = coordination_results.get('cluster_summary', {})
        if cluster_summary.get('total_clusters', 0) > 0:
            f.write(f"Cluster types: {cluster_summary.get('cluster_types', {})}\n")
            f.write(f"Largest cluster: {cluster_summary.get('largest_cluster', 0)} targets\n")
        f.write("\n")

        # Target Priority Breakdown
        if coordination_results.get('targets'):
            priorities = {'high': 0, 'medium': 0, 'low': 0}
            for target in coordination_results['targets']:
                priorities[target['priority_level']] += 1

            f.write("Target Priority Breakdown:\n")
            f.write(f"  High Priority: {priorities['high']}\n")
            f.write(f"  Medium Priority: {priorities['medium']}\n")
            f.write(f"  Low Priority: {priorities['low']}\n\n")

        # Top Targets
        if coordination_results.get('targets'):
            f.write("Top 5 Coordinated Targets by Confidence:\n")
            sorted_targets = sorted(coordination_results['targets'],
                                  key=lambda x: x['confidence_score'], reverse=True)

            for i, target in enumerate(sorted_targets[:5]):
                f.write(f"  {i+1}. Target {target['target_id']}: "
                       f"({target['latitude']:.6f}, {target['longitude']:.6f}) "
                       f"conf={target['confidence_score']:.3f} "
                       f"detections={target['detection_count']}\n")
            f.write("\n")

        # Redaction Analysis
        if scan_results['total_signatures'] > 0:
            f.write("REDACTION SIGNATURE ANALYSIS\n")
            f.write("-" * 40 + "\n")

            # Aggregate signature types across all scans
            signature_types = {}
            redactor_ids = set()

            for result in scan_results['results']:
                if result.get('success') and 'redaction_signatures' in result:
                    for sig in result['redaction_signatures']:
                        sig_type = sig.get('signature_type', 'unknown')
                        signature_types[sig_type] = signature_types.get(sig_type, 0) + 1

                        if sig.get('redactor_id'):
                            redactor_ids.add(sig['redactor_id'])

            f.write("Signature Types Detected:\n")
            for sig_type, count in sorted(signature_types.items()):
                f.write(f"  {sig_type}: {count} instances\n")

            if redactor_ids:
                f.write(f"\nIdentified Redactors: {sorted(redactor_ids)}\n")

            f.write("\nRedaction signatures indicate potential data manipulation.\n")
            f.write("High concentrations may suggest systematic redaction efforts.\n\n")

        # Output Files
        f.write("GENERATED OUTPUT FILES\n")
        f.write("-" * 40 + "\n")

        output_files = []

        # Scan result files
        for result in scan_results['results']:
            if result.get('success') and 'outputs' in result:
                for output_type, output_path in result['outputs'].items():
                    f.write(f"  {output_path} ({output_type.upper()} - {result['file']})\n")
                    output_files.append(output_path)

        # Coordinated output files
        kml_file = os.path.join(output_dir, f"coordinated_targets_{timestamp}.kml")
        kmz_file = os.path.join(output_dir, f"coordinated_targets_{timestamp}.kmz")

        if os.path.exists(kml_file):
            f.write(f"  {kml_file} (KML - Coordinated Targets)\n")
            output_files.append(kml_file)

        if os.path.exists(kmz_file):
            f.write(f"  {kmz_file} (KMZ - Coordinated Targets)\n")
            output_files.append(kmz_file)

        f.write(f"  {summary_file} (TXT - This Summary)\n")
        output_files.append(summary_file)

        f.write("\n")

        # Recommendations
        f.write("INVESTIGATION RECOMMENDATIONS\n")
        f.write("-" * 40 + "\n")

        high_priority = sum(1 for t in coordination_results.get('targets', [])
                          if t.get('priority_level') == 'high')

        if high_priority > 0:
            f.write(f"🚨 {high_priority} HIGH PRIORITY targets require immediate investigation.\n")
            f.write("   These targets show strong confidence and multiple detections.\n\n")

        if coordination_results.get('clusters'):
            f.write(f"🎯 {coordination_results['clusters']} target clusters identified.\n")
            f.write("   Clustered targets may indicate wreck fields or systematic redaction.\n\n")

        if scan_results['total_signatures'] > 0:
            f.write(f"🔍 {scan_results['total_signatures']} redaction signatures detected.\n")
            f.write("   Areas with high signature density warrant special attention.\n\n")

        f.write("Next Steps:\n")
        f.write("1. Review high-priority targets in Google Earth using generated KML/KMZ files\n")
        f.write("2. Cross-reference with historical records and known wrecks\n")
        f.write("3. Plan field investigations for top candidates\n")
        f.write("4. Consider additional scanning with different parameters if needed\n")

    logger.info(f"Pipeline summary written to {summary_file}")

    return {
        'summary_file': summary_file,
        'output_files': output_files,
        'high_priority_targets': high_priority if 'high_priority' in locals() else 0
    }

def main():
    parser = argparse.ArgumentParser(
        description="Complete Wreck Detection Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Complete pipeline that runs advanced BAG file scanning with redaction signature detection,
coordinates results across multiple scans, and generates comprehensive outputs.

Examples:
  # Run on all Lake Erie BAG files
  python complete_pipeline.py "Lake Erie Bag Files"

  # Custom sensitivity settings
  python complete_pipeline.py F00864_MB_4m_LWD_1of1.bag --redaction-sensitivity 0.5 --min-confidence 0.4

  # High-performance scan
  python complete_pipeline.py "Lake Erie Bag Files" --max-workers 8 --anomaly-threshold 2.0
        """
    )

    parser.add_argument(
        'bag_files',
        nargs='+',
        help='BAG files or directories containing BAG files'
    )

    parser.add_argument(
        '--output-dir', '-o',
        default='complete_pipeline_results',
        help='Output directory (default: complete_pipeline_results)'
    )

    parser.add_argument(
        '--min-confidence', '-c',
        type=float,
        default=0.3,
        help='Minimum confidence threshold (default: 0.3)'
    )

    parser.add_argument(
        '--redaction-sensitivity',
        type=float,
        default=0.6,
        help='Redaction signature detection sensitivity (default: 0.6)'
    )

    parser.add_argument(
        '--anomaly-threshold',
        type=float,
        default=2.5,
        help='Z-score threshold for anomaly detection (default: 2.5)'
    )

    parser.add_argument(
        '--max-workers', '-w',
        type=int,
        default=None,
        help='Maximum worker threads (default: min(4, num_files))'
    )

    parser.add_argument(
        '--coordination-distance',
        type=float,
        default=50.0,
        help='Maximum distance (meters) for target coordination (default: 50.0)'
    )

    args = parser.parse_args()

    # Find BAG files
    bag_files = find_bag_files(args.bag_files)

    if not bag_files:
        logger.error("No BAG files found!")
        sys.exit(1)

    logger.info(f"Found {len(bag_files)} BAG files for complete pipeline")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Prepare configuration
    config_overrides = {
        'min_confidence': args.min_confidence,
        'redaction_sensitivity': args.redaction_sensitivity,
        'anomaly_threshold': args.anomaly_threshold,
    }

    if args.max_workers:
        config_overrides['max_workers'] = args.max_workers

    # Run the complete pipeline
    try:
        results = run_complete_pipeline(bag_files, str(output_dir), config_overrides)

        # Print final status
        print("\n" + "="*80)
        print("PIPELINE EXECUTION COMPLETE")
        print("="*80)
        print(f"📊 Results saved to: {args.output_dir}")
        print(f"📋 Summary: {results['summary']['summary_file']}")
        print(f"🎯 High-priority targets: {results['summary']['high_priority_targets']}")
        print(f"📁 Total output files: {len(results['output_files'])}")

        if results['output_files']:
            print("\n📂 Generated files:")
            for output_file in results['output_files']:
                print(f"   {output_file}")

    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()</content>
<parameter name="filePath">c:\Temp\Garminjunk\HistoryofCESARSNIFFERBAGFILE\bagfilework\complete_pipeline.py