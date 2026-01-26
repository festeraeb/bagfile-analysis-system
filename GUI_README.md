# Redaction Breaker GUI

A comprehensive graphical user interface for applying advanced redaction breaking techniques to PDF documents.

## Features

### 🔍 **Single File Processing**
- Select individual PDF files for processing
- Choose from multiple redaction breaking techniques:
  - Enhanced Table Extraction
  - ML Image Restoration (Stable Diffusion, LaMa GAN)
  - Multi-OCR Recovery (Tesseract, EasyOCR, PaddleOCR)
  - Database Validation
  - Vulnerability Scanning
  - Visual Comparison Creation

### 📁 **Batch Processing**
- Process entire directories of PDF files
- Recursive folder scanning
- Custom file patterns (e.g., `*.pdf`, `redacted_*.pdf`)
- Progress tracking for large batches

### 📊 **Results Viewer**
- Browse all output files
- View file details and metadata
- Open files directly from the interface
- Organized by file type (PDFs, JSON results, etc.)

### ⚙️ **Settings**
- Configure OCR engines
- ML processing settings (GPU memory, batch size)
- Database configuration
- Advanced options (threads, timeouts)

## Installation

### Prerequisites
- Python 3.8+
- Required packages: PyMuPDF, Pillow, tkinter (built-in)

### Optional Dependencies
- pytesseract (Tesseract OCR)
- easyocr (EasyOCR engine)
- opencv-python (image processing)
- torch, diffusers (ML restoration)

### Quick Start
1. Double-click `RedactionBreakerGUI.bat`
2. The launcher will check dependencies and launch the GUI

### Manual Launch
```bash
python launch_gui.py
```

## Usage

### Single File Processing
1. Go to the "Single File Processing" tab
2. Click "Add PDFs" to select files
3. Choose processing options
4. Set output directory
5. Click "Start Processing"

### Batch Processing
1. Go to the "Batch Processing" tab
2. Click "Browse Directory" to select input folder
3. Configure file patterns and options
4. Click "Start Batch Processing"

### Viewing Results
1. Go to the "Results Viewer" tab
2. Click "Refresh" to scan output directory
3. Select files to view details or open

## Output Files

The GUI creates several types of output files:

### Comparison PDFs
- **Side-by-side comparisons** showing original vs. reconstructed
- **Red-highlighted recovered text** in reconstructed versions
- **Restored images** placed in original positions

### Reconstructed PDFs
- **Clean reconstructed documents** with recovered content
- **Enhanced recovery versions** with additional processing

### Results Files
- **JSON files** containing extracted data and metadata
- **Log files** with processing details

## Processing Techniques

### Table Extraction
- Advanced coordinate parsing
- Pattern recognition for sequential numbers
- Wreck type and depth correlation

### ML Image Restoration
- Stable Diffusion Inpainting
- LaMa GAN restoration
- Steganography detection

### OCR Recovery
- Multi-engine text recognition
- Confidence scoring and validation
- Context-aware recovery

### Database Validation
- Cross-referencing with maritime databases
- Coordinate validation
- Feature type matching

## Troubleshooting

### Common Issues

**GUI won't launch:**
- Check Python installation
- Install missing dependencies
- Run dependency check: `python launch_gui.py`

**Processing fails:**
- Check file permissions
- Ensure output directory is writable
- Verify PDF files are not corrupted

**ML features not available:**
- Install PyTorch and diffusers
- Check GPU memory settings
- Reduce batch size if needed

### Logs
- Check the processing logs in the GUI for detailed error messages
- Logs are saved to the output directory

## Advanced Configuration

### Settings File
Settings are automatically saved to `gui_settings.json`:
```json
{
  "ocr_engines": {
    "tesseract": true,
    "easyocr": true,
    "paddleocr": false
  },
  "gpu_memory": "4",
  "batch_size": "1",
  "db_path": "wrecks.db",
  "threads": "4",
  "timeout": "300"
}
```

### Custom Processing
The GUI can be extended by modifying `redaction_breaker_gui.py` to add:
- New processing modules
- Custom file filters
- Additional output formats

## Security Note

This tool is designed for research and analysis of redaction techniques. Ensure you have proper authorization before processing sensitive documents.