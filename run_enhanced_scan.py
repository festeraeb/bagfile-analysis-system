""""""

Simple runner script for the enhanced wreck scannerSimple runner script for the enhanced wreck scanner

Focuses on Straits of Mackinac area with your known training wrecksFocuses on Straits of Mackinac area with your known training wrecks

""""""



import sysimport sys

import osimport os

from pathlib import Pathfrom pathlib import Path



# Add current directory to path# Add current directory to path

sys.path.append(str(Path(__file__).parent))sys.path.append(str(Path(__file__).parent))



from enhanced_wreck_scanner import WreckSignatureDetector, ScanConfigfrom enhanced_wreck_scanner import WreckSignatureDetector, ScanConfig

from scrub_detection_engine import ScrubDetectionEnginefrom scrub_detection_engine import ScrubDetectionEngine

import loggingimport logging



def setup_logging():def setup_logging():

    """Setup basic logging"""    """Setup basic logging"""

    logging.basicConfig(    logging.basicConfig(

        level=logging.INFO,        level=logging.INFO,

        format='%(asctime)s - %(levelname)s - %(message)s',        format='%(asctime)s - %(levelname)s - %(message)s',

        handlers=[        handlers=[

            logging.StreamHandler(sys.stdout)            logging.StreamHandler(sys.stdout)

        ]        ]

    )    )



def run_focused_scan():def run_focused_scan():

    """    """

    Run a focused scan on Straits of Mackinac area    Run a focused scan on Straits of Mackinac area

    Using your identified training wrecks and known patterns    Using your identified training wrecks and known patterns

    """    """

    setup_logging()    setup_logging()

    logger = logging.getLogger(__name__)    logger = logging.getLogger(__name__)

        

    logger.info("Starting Enhanced Wreck Scanner for Straits of Mackinac")    logger.info("Starting Enhanced Wreck Scanner for Straits of Mackinac")

    logger.info("=" * 60)    logger.info("=" * 60)

        

    # Configuration focusing on your area of interest    # Configuration focusing on your area of interest

    config = ScanConfig(    config = ScanConfig(

        base_dir=r"c:\Temp\bagfilework",        base_dir=r"c:\Temp\bagfilework",

        bag_dir=r"c:\Temp\bagfilework",  # BAG files are in the main directory        bag_dir=r"c:\Temp\bagfilework",  # BAG files are in the main directory

        output_dir=r"c:\Temp\bagfilework\enhanced_scan_results",        output_dir=r"c:\Temp\bagfilework\enhanced_scan_results",

                

        # Straits of Mackinac bounds (expanded to cover available data)        # Straits of Mackinac bounds (expanded to cover available data)

        bounds={        bounds={

            'west': -85.50, 'east': -84.40,            'west': -85.50, 'east': -84.40,

            'south': 45.70, 'north': 46.00            'south': 45.70, 'north': 46.00

        },        },

                

        # Optimized parameters based on your experience        # Optimized parameters based on your experience

        tile_size_m=25,  # Slightly larger tiles for better ship detection        tile_size_m=25,  # Slightly larger tiles for better ship detection

        overlap_ratio=0.6,  # More overlap to catch partial features        overlap_ratio=0.6,  # More overlap to catch partial features

                

        # Adjusted thresholds based on Great Lakes conditions        # Adjusted thresholds based on Great Lakes conditions

        elevation_change_threshold=1.2,  # Slightly lower for subtle features        elevation_change_threshold=1.2,  # Slightly lower for subtle features

        uncertainty_anomaly_threshold=500.0,  # Lower threshold for more sensitivity        uncertainty_anomaly_threshold=500.0,  # Lower threshold for more sensitivity

        smoothing_threshold=0.4,  # Adjusted for your area        smoothing_threshold=0.4,  # Adjusted for your area

                

        # Ship size filters for Great Lakes vessels        # Ship size filters for Great Lakes vessels

        min_wreck_length_m=40,   # Smaller vessels included        min_wreck_length_m=40,   # Smaller vessels included

        max_wreck_length_m=300,  # Typical freighter max        max_wreck_length_m=300,  # Typical freighter max

        min_wreck_width_m=10,        min_wreck_width_m=10,

        max_wreck_width_m=45,        max_wreck_width_m=45,

                

        # Performance settings        # Performance settings

        max_workers=2,  # Conservative for stability        max_workers=2,  # Conservative for stability

        chunk_size_mb=50        chunk_size_mb=50

    )    )

        

    # Create detector with specialized configuration    # Create detector with specialized configuration

    detector = WreckSignatureDetector(config)    detector = WreckSignatureDetector(config)

        

    # Initialize scrub detection engine    # Initialize scrub detection engine

    scrub_engine = ScrubDetectionEngine()    scrub_engine = ScrubDetectionEngine()

        

    # Add the advanced scrub detection to the detector    # Add the advanced scrub detection to the detector

    detector.scrub_engine = scrub_engine    detector.scrub_engine = scrub_engine

        

    # Find BAG files    # Find BAG files

    bag_files = []    bag_files = []

    bag_dir = Path(config.bag_dir)    bag_dir = Path(config.bag_dir)

        

    for pattern in ['*.bag', '*.tif']:    for pattern in ['*.bag', '*.tif']:

        found_files = list(bag_dir.glob(pattern))        found_files = list(bag_dir.glob(pattern))

        bag_files.extend(found_files)        bag_files.extend(found_files)

        logger.info(f"Found {len(found_files)} {pattern} files")        logger.info(f"Found {len(found_files)} {pattern} files")

        

    if not bag_files:    if not bag_files:

        logger.error(f"No BAG files found in {config.bag_dir}")        logger.error(f"No BAG files found in {config.bag_dir}")

        logger.info("Available files:")        logger.info("Available files:")

        for file in bag_dir.iterdir():        for file in bag_dir.iterdir():

            if file.is_file():            if file.is_file():

                logger.info(f"  {file.name}")                logger.info(f"  {file.name}")

        return        return

        

    logger.info(f"Total files to process: {len(bag_files)}")    logger.info(f"Total files to process: {len(bag_files)}")

    logger.info("Files found:")    logger.info("Files found:")

    for f in bag_files:    for f in bag_files:

        logger.info(f"  {f.name}")        logger.info(f"  {f.name}")

        

    # Process files    # Process files

    all_results = []    all_results = []

        

    for i, bag_file in enumerate(bag_files, 1):    for i, bag_file in enumerate(bag_files, 1):

        logger.info(f"\n[{i}/{len(bag_files)}] Processing: {bag_file.name}")        logger.info(f"\n[{i}/{len(bag_files)}] Processing: {bag_file.name}")

                

        try:        try:

            results = detector.scan_bag_file(str(bag_file))            results = detector.scan_bag_file(str(bag_file))

                        

            if results:            if results:

                logger.info(f"  Generated {len(results)} analysis results")                logger.info(f"  Generated {len(results)} analysis results")

                all_results.extend(results)                all_results.extend(results)

            else:            else:

                logger.warning(f"  No results from {bag_file.name}")                logger.warning(f"  No results from {bag_file.name}")

                                

        except Exception as e:        except Exception as e:

            logger.error(f"  Failed to process {bag_file.name}: {str(e)}")            logger.error(f"  Failed to process {bag_file.name}: {str(e)}")

            continue            continue

        

    if not all_results:    if not all_results:

        logger.error("No results generated from any files!")        logger.error("No results generated from any files!")

        return        return

        

    logger.info(f"\nTotal analysis results: {len(all_results)}")    logger.info(f"\nTotal analysis results: {len(all_results)}")

        

    # Train models    # Train models

    logger.info("Training detection models...")    logger.info("Training detection models...")

    detector.train_models(all_results)    detector.train_models(all_results)

        

    # Score results    # Score results

    logger.info("Scoring results...")    logger.info("Scoring results...")

    scored_results = detector.score_results(all_results)    scored_results = detector.score_results(all_results)

        

    # Export results    # Export results

    logger.info("Exporting results...")    logger.info("Exporting results...")

    from datetime import datetime    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    detector.export_results(scored_results, f"mackinac_enhanced_scan_{timestamp}")    detector.export_results(scored_results, f"mackinac_enhanced_scan_{timestamp}")

        

    # Summary statistics    # Summary statistics

    high_anomaly = [r for r in scored_results if r.get('anomaly_score', -999) > -0.1]    high_anomaly = [r for r in scored_results if r.get('anomaly_score', -999) > -0.1]

    high_wreck_prob = [r for r in scored_results if r.get('wreck_probability', 0) > 0.3]    high_wreck_prob = [r for r in scored_results if r.get('wreck_probability', 0) > 0.3]

    near_known_wrecks = [r for r in scored_results if r.get('distance_to_nearest_wreck', float('inf')) < 200]    near_known_wrecks = [r for r in scored_results if r.get('distance_to_nearest_wreck', float('inf')) < 200]

        

    logger.info("\n" + "=" * 60)    logger.info("\n" + "=" * 60)

    logger.info("SCAN SUMMARY")    logger.info("SCAN SUMMARY")

    logger.info("=" * 60)    logger.info("=" * 60)

    logger.info(f"Total tiles analyzed: {len(scored_results)}")    logger.info(f"Total tiles analyzed: {len(scored_results)}")

    logger.info(f"High anomaly tiles: {len(high_anomaly)} ({len(high_anomaly)/len(scored_results)*100:.1f}%)")    logger.info(f"High anomaly tiles: {len(high_anomaly)} ({len(high_anomaly)/len(scored_results)*100:.1f}%)")

    logger.info(f"High wreck probability: {len(high_wreck_prob)} ({len(high_wreck_prob)/len(scored_results)*100:.1f}%)")    logger.info(f"High wreck probability: {len(high_wreck_prob)} ({len(high_wreck_prob)/len(scored_results)*100:.1f}%)")

    logger.info(f"Near known wrecks (<200m): {len(near_known_wrecks)}")    logger.info(f"Near known wrecks (<200m): {len(near_known_wrecks)}")

        

    # Report on specific training areas    # Report on specific training areas

    elva_area = [r for r in scored_results if r.get('nearest_wreck') == 'Elva' and r.get('distance_to_nearest_wreck', 0) < 100]    elva_area = [r for r in scored_results if r.get('nearest_wreck') == 'Elva' and r.get('distance_to_nearest_wreck', 0) < 100]

    if elva_area:    if elva_area:

        avg_anomaly = sum(r.get('anomaly_score', 0) for r in elva_area) / len(elva_area)        avg_anomaly = sum(r.get('anomaly_score', 0) for r in elva_area) / len(elva_area)

        logger.info(f"Elva training area: {len(elva_area)} tiles, avg anomaly score: {avg_anomaly:.3f}")        logger.info(f"Elva training area: {len(elva_area)} tiles, avg anomaly score: {avg_anomaly:.3f}")

        

    logger.info(f"\nResults saved to: {config.output_dir}")    logger.info(f"\nResults saved to: {config.output_dir}")

    logger.info("Check the KML file for high-confidence detections!")    logger.info("Check the KML file for high-confidence detections!")



if __name__ == "__main__":if __name__ == "__main__":

    run_focused_scan()    run_focused_scan()
