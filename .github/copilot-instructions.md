# AI Coding Assistant Instructions

## Project Overview
This is a multi-phase wreck detection system that extracts hidden shipwreck coordinates from redacted NOAA PDF documents and uses machine learning to scan bathymetric BAG files for anomalies. The system combines PDF intelligence extraction, ML-enhanced scanning, and Rust-accelerated processing.

## Architecture & Data Flow
- **Phase 1**: PDF redaction recovery using PyMuPDF vulnerabilities (morphological analysis, content stream parsing)
- **Phase 2**: ML model training on extracted coordinates (Random Forest, Isolation Forest)
- **Phase 3**: Parallel BAG file scanning with anomaly detection
- **Phase 4**: Cross-referencing results with PDF intelligence

## Key Components
- `comprehensive_recovery_system.py` - Main PDF redaction breaker
- `enhanced_recovery_system.py` - Advanced recovery with 10+ techniques
- `rust_ml_integration.py` - High-performance Rust-Python bridge
- `robust_bag_scanner.py` - BAG file processing with error recovery
- GUI interfaces: `comprehensive_bag_gui.py`, `enhanced_bag_gui.py`

## Build & Runtime Setup
```bash
# Environment setup (Windows batch files)
RedactionBreakerSetup.bat  # Creates venv and installs dependencies
run_bagfile_analysis_system.bat  # Full conda environment setup

# Rust extension build
maturin develop  # Build and install Rust module
cargo build --release  # Release build

# Key dependencies
pip install -r requirements.txt
conda install rasterio geopandas shapely  # GIS stack
```

## Coding Patterns & Conventions

### Configuration Management
- Use JSON files for vulnerability data, scan configs, and results
- Config classes with default dictionaries (see `run_enhanced_scan.py`)
- Path handling with `pathlib.Path` and raw strings for Windows paths

### Error Handling
- Progressive error recovery in scanners (try multiple methods)
- Logging with timestamps and structured output
- Graceful degradation when dependencies unavailable

### Coordinate Systems
- Geographic bounds for Great Lakes focus area:
  ```python
  bounds = {
      'west': -84.85, 'east': -84.40,
      'south': 45.70, 'north': 45.95
  }
  ```
- Lat/lon coordinates with NAD83 datum
- Pixel-to-coordinate conversion using GDAL transforms

### File Naming & Output
- Timestamped results: `mackinac_enhanced_scan_YYYYMMDD_HHMMSS.csv`
- Multiple export formats: CSV, KML, JSON, GeoJSON
- Organized output directories: `scan_results/`, `wreck_candidates/`

### ML Integration
- Scikit-learn models trained on PDF-extracted coordinates
- Feature engineering: depth statistics, gradients, texture analysis
- Confidence scoring for result prioritization

### Rust Acceleration
- PyO3 bindings for performance-critical functions
- Rayon for parallel processing
- Memory-efficient data structures

## Common Workflows

### Adding New Recovery Techniques
1. Extend `recovery_techniques` dict in `EnhancedRecoverySystem`
2. Implement method following pattern: `def recover_from_[technique](self, pdf_path: str) -> List[Dict]`
3. Add to vulnerability scan results JSON
4. Test on sample redacted PDFs

### BAG File Processing
1. Validate file with GDAL/rasterio
2. Extract elevation and uncertainty bands
3. Apply morphological filters and anomaly detection
4. Convert detections to geographic coordinates
5. Cross-reference with known wreck databases

### GUI Development
- Tkinter-based with progress bars and file dialogs
- Dependency checking in launchers
- Settings persistence in JSON configs
- Error display with user-friendly messages

## Testing & Validation
- Component-specific test files: `test_redaction_breaker_h13255.py`
- Validation against known wrecks (Elva, Elva Barge)
- Coordinate accuracy checking
- Performance benchmarking with `performance_comparison.py`

## External Dependencies
- NOAA BAG files (bathymetric data archives)
- Redacted PDF documents from hydrographic surveys
- GIS libraries for coordinate transformations
- ML models for anomaly detection</content>
<parameter name="filePath">c:\Temp\Garminjunk\HistoryofCESARSNIFFERBAGFILE\bagfilework\.github\copilot-instructions.md