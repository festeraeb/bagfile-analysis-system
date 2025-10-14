# Advanced Wreck Detection System# Advanced Wreck Detection System



## Overview## Overview



This is a comprehensive system for detecting shipwrecks in NOAA bathymetric data using PDF intelligence extraction and machine learning. The system combines multiple approaches:This is a comprehensive system for detecting shipwrecks in NOAA bathymetric data using PDF intelligence extraction and machine learning. The system combines multiple approaches:



1. **PDF Redaction Analysis** - Extracts hidden wreck coordinates from redacted NOAA documents1. **PDF Redaction Analysis** - Extracts hidden wreck coordinates from redacted NOAA documents

2. **ML-Enhanced BAG Scanning** - Uses computer vision and machine learning for anomaly detection2. **ML-Enhanced BAG Scanning** - Uses computer vision and machine learning for anomaly detection

3. **Intelligence-Driven Refinement** - Trains models using extracted wreck coordinates3. **Intelligence-Driven Refinement** - Trains models using extracted wreck coordinates

4. **Automated Data Acquisition** - Downloads BAG files from NOAA archives4. **Automated Data Acquisition** - Downloads BAG files from NOAA archives



## Quick Start## Quick Start



### Option 1: Fastest Testing### Option 1: Fastest Testing

```bash```bash

python quick_start.pypython quick_start.py

``````

This provides an interactive menu to quickly test the system.This provides an interactive menu to quickly test the system.

# Advanced Wreck Detection System# Advanced Wreck Detection System



## Overview## Overview



This is a comprehensive system for detecting shipwrecks in NOAA bathymetric data using PDF intelligence extraction and machine learning. The system combines multiple approaches:This is a comprehensive system for detecting shipwrecks in NOAA bathymetric data using PDF intelligence extraction and machine learning. The system combines multiple approaches:



1. **PDF Redaction Analysis** - Extracts hidden wreck coordinates from redacted NOAA documents1. **PDF Redaction Analysis** - Extracts hidden wreck coordinates from redacted NOAA documents

2. **ML-Enhanced BAG Scanning** - Uses computer vision and machine learning for anomaly detection2. **ML-Enhanced BAG Scanning** - Uses computer vision and machine learning for anomaly detection

3. **Intelligence-Driven Refinement** - Trains models using extracted wreck coordinates3. **Intelligence-Driven Refinement** - Trains models using extracted wreck coordinates

4. **Automated Data Acquisition** - Downloads BAG files from NOAA archives4. **Automated Data Acquisition** - Downloads BAG files from NOAA archives



## Quick Start## Quick Start



### Option 1: Fastest Testing### Option 1: Fastest Testing

```bash```bash

python quick_start.pypython quick_start.py

``````

This provides an interactive menu to quickly test the system.This provides an interactive menu to quickly test the system.



### Option 2: Full Pipeline### Option 2: Full Pipeline

```bash```bash

python wreck_detection_orchestrator.py --max-files 10python wreck_detection_orchestrator.py --max-files 10

``````

Runs the complete detection pipeline with all features.Runs the complete detection pipeline with all features.



### Option 3: Individual Components### Option 3: Individual Components

```bash```bash

# PDF intelligence extraction# PDF intelligence extraction

python wreck_obstruction_extractor.pypython wreck_obstruction_extractor.py



# ML-enhanced scanning# ML-enhanced scanning

python ml_enhanced_bag_scanner.pypython ml_enhanced_bag_scanner.py



# Automated downloads# Automated downloads

python noaa_bag_downloader.pypython noaa_bag_downloader.py

``````



## System Architecture## System Architecture



### Core Components### Core Components



1. **wreck_detection_orchestrator.py** - Master orchestrator that runs the complete pipeline1. **wreck_detection_orchestrator.py** - Master orchestrator that runs the complete pipeline

2. **quick_start.py** - Interactive quick-start system for testing2. **quick_start.py** - Interactive quick-start system for testing

3. **ml_enhanced_bag_scanner.py** - Advanced ML scanner using PDF intelligence3. **ml_enhanced_bag_scanner.py** - Advanced ML scanner using PDF intelligence

4. **wreck_obstruction_extractor.py** - PDF redaction analysis and coordinate extraction4. **wreck_obstruction_extractor.py** - PDF redaction analysis and coordinate extraction

5. **noaa_bag_downloader.py** - Automated BAG file acquisition from NOAA5. **noaa_bag_downloader.py** - Automated BAG file acquisition from NOAA



### Dependencies### Dependencies



Install required packages:Install required packages:

```bash```bash

pip install rasterio fiona opencv-python scikit-learn pandas numpy shapely pyproj PyMuPDF requests beautifulsoup4pip install rasterio fiona opencv-python scikit-learn pandas numpy shapely pyproj PyMuPDF requests beautifulsoup4

``````



### Data Requirements### Data Requirements



The system works with:The system works with:

- **PDF Files**: NOAA survey reports with redacted wreck information- **PDF Files**: NOAA survey reports with redacted wreck information

- **BAG Files**: NOAA bathymetric data files (.bag format)- **BAG Files**: NOAA bathymetric data files (.bag format)

- **Intelligence Files**: Extracted coordinates and classifications- **Intelligence Files**: Extracted coordinates and classifications



## Pipeline Workflow## Pipeline Workflow



### Phase 1: PDF Intelligence Extraction### Phase 1: PDF Intelligence Extraction

- Analyzes NOAA PDF documents for redacted content- Analyzes NOAA PDF documents for redacted content

- Extracts wreck vs obstruction classifications- Extracts wreck vs obstruction classifications

- Recovers coordinate information using morphological analysis- Recovers coordinate information using morphological analysis

- **Result**: 207 wreck references vs 2,287 obstruction references with 154 coordinates- **Result**: 207 wreck references vs 2,287 obstruction references with 154 coordinates



### Phase 2: Data Acquisition### Phase 2: Data Acquisition

- Downloads priority BAG files from NOAA archives- Downloads priority BAG files from NOAA archives

- Focuses on surveys with highest wreck density- Focuses on surveys with highest wreck density

- Creates comprehensive file catalog- Creates comprehensive file catalog



### Phase 3: ML Model Training### Phase 3: ML Model Training

- Trains Random Forest and Isolation Forest models- Trains Random Forest and Isolation Forest models

- Uses extracted wreck coordinates as positive examples- Uses extracted wreck coordinates as positive examples

- Incorporates depth, morphology, and pattern features- Incorporates depth, morphology, and pattern features



### Phase 4: BAG File Processing### Phase 4: BAG File Processing

- Applies multiple detection methods in parallel:- Applies multiple detection methods in parallel:

  - Morphological analysis (structural features)  - Morphological analysis (structural features)

  - ML-based anomaly detection  - ML-based anomaly detection

  - Pattern matching algorithms  - Pattern matching algorithms

  - Edge detection and clustering  - Edge detection and clustering

- Generates confidence scores for each detection- Generates confidence scores for each detection



### Phase 5: Results Analysis### Phase 5: Results Analysis

- Cross-references ML detections with PDF intelligence- Cross-references ML detections with PDF intelligence

- Generates priority target lists- Generates priority target lists

- Creates comprehensive reports and recommendations- Creates comprehensive reports and recommendations



## Detection Methods## Detection Methods



### 1. Morphological Analysis### 1. Morphological Analysis

- Identifies ship-like shapes and structures- Identifies ship-like shapes and structures

- Detects linear features and geometric patterns- Detects linear features and geometric patterns

- Analyzes depth gradients and anomalies- Analyzes depth gradients and anomalies



### 2. Machine Learning Detection### 2. Machine Learning Detection

- **Random Forest**: Classifies features as wreck/non-wreck- **Random Forest**: Classifies features as wreck/non-wreck

- **Isolation Forest**: Detects anomalous depth patterns- **Isolation Forest**: Detects anomalous depth patterns

- **Feature Engineering**: Depth statistics, gradients, texture analysis- **Feature Engineering**: Depth statistics, gradients, texture analysis



### 3. PDF Intelligence Integration### 3. PDF Intelligence Integration

- Uses extracted coordinates to focus scanning- Uses extracted coordinates to focus scanning

- Applies wreck vs obstruction classification knowledge- Applies wreck vs obstruction classification knowledge

- Prioritizes areas with high redaction density- Prioritizes areas with high redaction density



### 4. Multi-Scale Analysis### 4. Multi-Scale Analysis

- Processes data at multiple resolutions- Processes data at multiple resolutions

- Combines local and regional anomaly detection- Combines local and regional anomaly detection

- Filters results by confidence thresholds- Filters results by confidence thresholds



## Key Results## Key Results



### PDF Intelligence Extraction### PDF Intelligence Extraction

- **207 wreck references** extracted from redacted documents- **207 wreck references** extracted from redacted documents

- **154 coordinate locations** recovered- **154 coordinate locations** recovered

- **9:1 to 44:1 obstruction:wreck ratios** indicating systematic redaction- **9:1 to 44:1 obstruction:wreck ratios** indicating systematic redaction

- **Geographic focus**: Great Lakes region (45°43'-45°47'N, 085°04'-085°11'W)- **Geographic focus**: Great Lakes region (45°43'-45°47'N, 085°04'-085°11'W)



### Detection Performance### Detection Performance

- **Multi-threaded processing** for speed optimization- **Multi-threaded processing** for speed optimization

- **Confidence scoring** for result prioritization- **Confidence scoring** for result prioritization

- **Export capabilities** to multiple formats (CSV, KML, JSON)- **Export capabilities** to multiple formats (CSV, KML, JSON)

- **Real-time progress tracking** with checkpoint/resume functionality- **Real-time progress tracking** with checkpoint/resume functionality



------



**Note**: This system is designed for research and archaeological purposes. Always comply with local maritime laws and regulations when conducting field investigations.**Note**: This system is designed for research and archaeological purposes. Always comply with local maritime laws and regulations when conducting field investigations.

Edit the configuration in `run_enhanced_scan.py`:Edit the configuration in `run_enhanced_scan.py`:



```python```python

config = ScanConfig(config = ScanConfig(

    base_dir=r"c:\Temp\bagfilework",    base_dir=r"c:\Temp\bagfilework",

    bag_dir=r"c:\Temp\bagfilework\bathymetric_project",    bag_dir=r"c:\Temp\bagfilework\bathymetric_project",

        

    # Focus area (Straits of Mackinac)    # Focus area (Straits of Mackinac)

    bounds={    bounds={

        'west': -84.85, 'east': -84.40,        'west': -84.85, 'east': -84.40,

        'south': 45.70, 'north': 45.95        'south': 45.70, 'north': 45.95

    },    },

        

    # Detection sensitivity    # Detection sensitivity

    uncertainty_anomaly_threshold=500.0,  # Lower = more sensitive    uncertainty_anomaly_threshold=500.0,  # Lower = more sensitive

    smoothing_threshold=0.4,              # Lower = more sensitive    smoothing_threshold=0.4,              # Lower = more sensitive

))

``````



## Your Insights Incorporated## Your Insights Incorporated



### From PDF Analysis### From PDF Analysis

- **Word Length Analysis**: You noted "wreck" vs "object" length differences in redacted PDFs- **Word Length Analysis**: You noted "wreck" vs "object" length differences in redacted PDFs

- **Pattern Recognition**: Scanner looks for the same smoothing patterns you identified- **Pattern Recognition**: Scanner looks for the same smoothing patterns you identified



### From Known Omitted Wrecks  ### From Known Omitted Wrecks  

- **Training Data**: Uses Elva and Elva Barge as positive training examples- **Training Data**: Uses Elva and Elva Barge as positive training examples

- **Size Filtering**: Focuses on Great Lakes freighter dimensions- **Size Filtering**: Focuses on Great Lakes freighter dimensions

- **Spatial Context**: Considers proximity to known wreck locations- **Spatial Context**: Considers proximity to known wreck locations



### From BAG File Analysis### From BAG File Analysis

- **Freighter Box Detection**: Implements your "freighter-sized box" hypothesis- **Freighter Box Detection**: Implements your "freighter-sized box" hypothesis

- **Multi-Resolution**: Adapts tile size based on BAG file resolution- **Multi-Resolution**: Adapts tile size based on BAG file resolution

- **Comparative Analysis**: Can compare Ellipsoid vs LWD data (when both available)- **Comparative Analysis**: Can compare Ellipsoid vs LWD data (when both available)



## Output Files## Output Files



The scanner generates:The scanner generates:



1. **CSV Results**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS.csv`1. **CSV Results**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS.csv`

   - All tile analysis results with scores and coordinates   - All tile analysis results with scores and coordinates



2. **High-Confidence KML**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_high_confidence.kml`2. **High-Confidence KML**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_high_confidence.kml`

   - Only the most promising detections for review   - Only the most promising detections for review



3. **Summary Report**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_summary.txt`3. **Summary Report**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_summary.txt`

   - Statistics and overview of findings   - Statistics and overview of findings



4. **Log File**: `wreck_scanner.log`4. **Log File**: `wreck_scanner.log`

   - Detailed processing log for troubleshooting   - Detailed processing log for troubleshooting



## Interpreting Results## Interpreting Results



### Key Columns in CSV:### Key Columns in CSV:

- `anomaly_score`: Higher = more anomalous (look for > -0.1)- `anomaly_score`: Higher = more anomalous (look for > -0.1)

- `wreck_probability`: ML model confidence (look for > 0.3)- `wreck_probability`: ML model confidence (look for > 0.3)

- `freighter_likelihood`: Ship signature confidence (look for > 0.3)- `freighter_likelihood`: Ship signature confidence (look for > 0.3)

- `smoothing_confidence`: Artificial smoothing detected (look for > 0.5)- `smoothing_confidence`: Artificial smoothing detected (look for > 0.5)

- `scrubbing_likelihood`: Scrubbing box pattern (look for > 0.4)- `scrubbing_likelihood`: Scrubbing box pattern (look for > 0.4)



### KML Color Coding:### KML Color Coding:

- **Red**: High confidence detections (investigate first)- **Red**: High confidence detections (investigate first)

- **Yellow**: Medium confidence  - **Yellow**: Medium confidence  

- **Blue**: Lower confidence but worth noting- **Blue**: Lower confidence but worth noting



## Next Steps## Next Steps



1. **Review High-Confidence Results**: Start with red pins in the KML1. **Review High-Confidence Results**: Start with red pins in the KML

2. **Cross-Reference**: Compare with your known wreck databases2. **Cross-Reference**: Compare with your known wreck databases

3. **Ground Truth**: Use side-scan sonar or ROV to verify promising locations3. **Ground Truth**: Use side-scan sonar or ROV to verify promising locations

4. **Refine Training**: Add confirmed finds back as training data4. **Refine Training**: Add confirmed finds back as training data



## Troubleshooting## Troubleshooting



### Common Issues:### Common Issues:

- **No Results**: Check that BAG files are in the correct directory- **No Results**: Check that BAG files are in the correct directory

- **Memory Issues**: Reduce `chunk_size_mb` in configuration- **Memory Issues**: Reduce `chunk_size_mb` in configuration

- **Slow Performance**: Reduce `max_workers` or tile overlap- **Slow Performance**: Reduce `max_workers` or tile overlap



### File Format Support:### File Format Support:

- Primary: `.bag` files- Primary: `.bag` files

- Secondary: `.tif` bathymetric files- Secondary: `.tif` bathymetric files

- Requires proper georeferencing- Requires proper georeferencing



## Technical Notes## Technical Notes



The scanner combines several detection approaches:The scanner combines several detection approaches:



1. **Statistical Analysis**: Looks for unusual elevation distributions1. **Statistical Analysis**: Looks for unusual elevation distributions

2. **Morphological Operations**: Finds ship-shaped features2. **Morphological Operations**: Finds ship-shaped features

3. **Spectral Analysis**: Detects artificial smoothing signatures  3. **Spectral Analysis**: Detects artificial smoothing signatures  

4. **Machine Learning**: Learns patterns from your training data4. **Machine Learning**: Learns patterns from your training data



This multi-method approach increases confidence when multiple techniques agree on a detection.This multi-method approach increases confidence when multiple techniques agree on a detection.



## Your Contribution## Your Contribution



This tool incorporates your hard-won insights about NOAA's redaction methods. The combination of:The tool incorporates your hard-won insights about NOAA's redaction methods. The combination of:

- PDF word-counting analysis- PDF word-counting analysis

- Known omitted wrecks as training data  - Known omitted wrecks as training data  

- Understanding of their smoothing techniques- Understanding of their smoothing techniques

- Focus on Great Lakes shipping lanes- Focus on Great Lakes shipping lanes



...makes this much more targeted than a generic anomaly detector....makes this much more targeted than a generic anomaly detector.



Keep training it with new finds and it should get better over time!Keep training it with new finds and it should get better over time!

        

    # Focus area (Straits of Mackinac)    # Focus area (Straits of Mackinac)

    bounds={    bounds={

        'west': -84.85, 'east': -84.40,        'west': -84.85, 'east': -84.40,

        'south': 45.70, 'north': 45.95        'south': 45.70, 'north': 45.95

    },    },

        

    # Detection sensitivity    # Detection sensitivity

    uncertainty_anomaly_threshold=500.0,  # Lower = more sensitive    uncertainty_anomaly_threshold=500.0,  # Lower = more sensitive

    smoothing_threshold=0.4,              # Lower = more sensitive    smoothing_threshold=0.4,              # Lower = more sensitive

))

``````



## Your Insights Incorporated## Your Insights Incorporated



### From PDF Analysis### From PDF Analysis

- **Word Length Analysis**: You noted "wreck" vs "object" length differences in redacted PDFs- **Word Length Analysis**: You noted "wreck" vs "object" length differences in redacted PDFs

- **Pattern Recognition**: Scanner looks for the same smoothing patterns you identified- **Pattern Recognition**: Scanner looks for the same smoothing patterns you identified



### From Known Omitted Wrecks  ### From Known Omitted Wrecks  

- **Training Data**: Uses Elva and Elva Barge as positive training examples- **Training Data**: Uses Elva and Elva Barge as positive training examples

- **Size Filtering**: Focuses on Great Lakes freighter dimensions- **Size Filtering**: Focuses on Great Lakes freighter dimensions

- **Spatial Context**: Considers proximity to known wreck locations- **Spatial Context**: Considers proximity to known wreck locations



### From BAG File Analysis### From BAG File Analysis

- **Freighter Box Detection**: Implements your "freighter-sized box" hypothesis- **Freighter Box Detection**: Implements your "freighter-sized box" hypothesis

- **Multi-Resolution**: Adapts tile size based on BAG file resolution- **Multi-Resolution**: Adapts tile size based on BAG file resolution

- **Comparative Analysis**: Can compare Ellipsoid vs LWD data (when both available)- **Comparative Analysis**: Can compare Ellipsoid vs LWD data (when both available)



## Output Files## Output Files



The scanner generates:The scanner generates:



1. **CSV Results**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS.csv`1. **CSV Results**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS.csv`

   - All tile analysis results with scores and coordinates   - All tile analysis results with scores and coordinates



2. **High-Confidence KML**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_high_confidence.kml`2. **High-Confidence KML**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_high_confidence.kml`

   - Only the most promising detections for review   - Only the most promising detections for review



3. **Summary Report**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_summary.txt`3. **Summary Report**: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS_summary.txt`

   - Statistics and overview of findings   - Statistics and overview of findings



4. **Log File**: `wreck_scanner.log`4. **Log File**: `wreck_scanner.log`

   - Detailed processing log for troubleshooting   - Detailed processing log for troubleshooting



## Interpreting Results## Interpreting Results



### Key Columns in CSV:### Key Columns in CSV:

- `anomaly_score`: Higher = more anomalous (look for > -0.1)- `anomaly_score`: Higher = more anomalous (look for > -0.1)

- `wreck_probability`: ML model confidence (look for > 0.3)- `wreck_probability`: ML model confidence (look for > 0.3)

- `freighter_likelihood`: Ship signature confidence (look for > 0.3)- `freighter_likelihood`: Ship signature confidence (look for > 0.3)

- `smoothing_confidence`: Artificial smoothing detected (look for > 0.5)- `smoothing_confidence`: Artificial smoothing detected (look for > 0.5)

- `scrubbing_likelihood`: Scrubbing box pattern (look for > 0.4)- `scrubbing_likelihood`: Scrubbing box pattern (look for > 0.4)



### KML Color Coding:### KML Color Coding:

- **Red**: High confidence detections (investigate first)- **Red**: High confidence detections (investigate first)

- **Yellow**: Medium confidence  - **Yellow**: Medium confidence  

- **Blue**: Lower confidence but worth noting- **Blue**: Lower confidence but worth noting



## Next Steps## Next Steps



1. **Review High-Confidence Results**: Start with red pins in the KML1. **Review High-Confidence Results**: Start with red pins in the KML

2. **Cross-Reference**: Compare with your known wreck databases2. **Cross-Reference**: Compare with your known wreck databases

3. **Ground Truth**: Use side-scan sonar or ROV to verify promising locations3. **Ground Truth**: Use side-scan sonar or ROV to verify promising locations

4. **Refine Training**: Add confirmed finds back as training data4. **Refine Training**: Add confirmed finds back as training data



## Troubleshooting## Troubleshooting



### Common Issues:### Common Issues:

- **No Results**: Check that BAG files are in the correct directory- **No Results**: Check that BAG files are in the correct directory

- **Memory Issues**: Reduce `chunk_size_mb` in configuration- **Memory Issues**: Reduce `chunk_size_mb` in configuration

- **Slow Performance**: Reduce `max_workers` or tile overlap- **Slow Performance**: Reduce `max_workers` or tile overlap



### File Format Support:### File Format Support:

- Primary: `.bag` files- Primary: `.bag` files

- Secondary: `.tif` bathymetric files- Secondary: `.tif` bathymetric files

- Requires proper georeferencing- Requires proper georeferencing



## Technical Notes## Technical Notes



The scanner combines several detection approaches:The scanner combines several detection approaches:



1. **Statistical Analysis**: Looks for unusual elevation distributions1. **Statistical Analysis**: Looks for unusual elevation distributions

2. **Morphological Operations**: Finds ship-shaped features2. **Morphological Operations**: Finds ship-shaped features

3. **Spectral Analysis**: Detects artificial smoothing signatures  3. **Spectral Analysis**: Detects artificial smoothing signatures  

4. **Machine Learning**: Learns patterns from your training data4. **Machine Learning**: Learns patterns from your training data



This multi-method approach increases confidence when multiple techniques agree on a detection.This multi-method approach increases confidence when multiple techniques agree on a detection.



## Your Contribution## Your Contribution



This tool incorporates your hard-won insights about NOAA's redaction methods. The combination of:This tool incorporates your hard-won insights about NOAA's redaction methods. The combination of:

- PDF word-counting analysis- PDF word-counting analysis

- Known omitted wrecks as training data  - Known omitted wrecks as training data  

- Understanding of their smoothing techniques- Understanding of their smoothing techniques

- Focus on Great Lakes shipping lanes- Focus on Great Lakes shipping lanes



...makes this much more targeted than a generic anomaly detector....makes this much more targeted than a generic anomaly detector.



Keep training it with new finds and it should get better over time!Keep training it with new finds and it should get better over time!
