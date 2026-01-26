#!/usr/bin/env python3
"""
Unified Redaction Breaker - Combined Tool
Combines multiple redaction breaking techniques including image analysis
"""

import PyPDF2
import fitz  # PyMuPDF
import json
import os
import sys
from datetime import datetime
import re
import base64
from PIL import Image
import io
import cv2
import numpy as np

class UnifiedRedactionBreaker:
    """Unified redaction breaking tool combining all techniques"""

    def __init__(self):
        self.results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "techniques_used": [
                "text_extraction_bypass",
                "layered_content_analysis",
                "image_extraction_analysis",
                "metadata_mining",
                "font_analysis",
                "annotation_extraction",
                "form_field_analysis",
                "content_stream_analysis",
                "image_text_extraction",
                "image_feature_detection",
                "redaction_pattern_analysis",
                "enhanced_content_stream_mining",
                "ocr_analysis",
                "image_redaction_recovery",
                "image_analysis_redaction_recovery"
            ],
            "files_analyzed": [],
            "blackout_breakthroughs": [],
            "hidden_content_found": [],
            "metadata_discoveries": [],
            "image_analysis_results": []
        }

    def analyze_pdf_comprehensive(self, pdf_path):
        """Comprehensive analysis using all available techniques"""

        print(f"\n🔍 COMPREHENSIVE ANALYSIS: {os.path.basename(pdf_path)}")
        print("=" * 70)

        file_analysis = {
            "filename": os.path.basename(pdf_path),
            "path": pdf_path,
            "techniques_attempted": [],
            "discoveries": [],
            "blackout_bypasses": [],
            "hidden_text": [],
            "metadata": {},
            "image_analysis": []
        }

        # Technique 1: PyPDF2 Text Extraction (bypass visual blocks)
        try:
            text_content = self.extract_text_pypdf2(pdf_path)
            if text_content:
                file_analysis["techniques_attempted"].append("pypdf2_text_extraction")
                file_analysis["hidden_text"].extend(text_content)
                print(f"✅ PyPDF2 Text: {len(text_content)} text blocks extracted")
        except Exception as e:
            print(f"❌ PyPDF2 failed: {e}")

        # Technique 2: PyMuPDF Advanced Extraction
        try:
            mudf_results = self.extract_with_pymupdf(pdf_path)
            if mudf_results:
                file_analysis["techniques_attempted"].append("pymupdf_advanced")
                file_analysis.update(mudf_results)
                print(f"✅ PyMuPDF: Multiple content layers analyzed")
        except Exception as e:
            print(f"❌ PyMuPDF failed: {e}")

        # Technique 3: Metadata Mining
        try:
            metadata = self.extract_metadata(pdf_path)
            if metadata:
                file_analysis["techniques_attempted"].append("metadata_mining")
                file_analysis["metadata"] = metadata
                print(f"✅ Metadata: {len(metadata)} properties extracted")
        except Exception as e:
            print(f"❌ Metadata extraction failed: {e}")

        # Technique 4: Content Stream Analysis
        try:
            stream_content = self.analyze_content_streams(pdf_path)
            if stream_content:
                file_analysis["techniques_attempted"].append("content_stream_analysis")
                file_analysis["blackout_bypasses"].extend(stream_content)
                print(f"✅ Content Streams: {len(stream_content)} hidden elements found")
        except Exception as e:
            print(f"❌ Content stream analysis failed: {e}")

        # Technique 6: Redaction Pattern Analysis
        try:
            redaction_patterns = self.analyze_redaction_patterns(pdf_path)
            if redaction_patterns:
                file_analysis["techniques_attempted"].append("redaction_pattern_analysis")
                file_analysis["redaction_analysis"] = redaction_patterns
                print(f"✅ Redaction Patterns: {len(redaction_patterns)} potential redaction areas found")
        except Exception as e:
            print(f"❌ Redaction pattern analysis failed: {e}")

        # Technique 7: Enhanced Content Stream Mining
        try:
            enhanced_streams = self.enhanced_content_stream_mining(pdf_path)
            if enhanced_streams:
                file_analysis["techniques_attempted"].append("enhanced_content_stream_mining")
                file_analysis["enhanced_streams"] = enhanced_streams
                print(f"✅ Enhanced Streams: {len(enhanced_streams)} additional content elements found")
        except Exception as e:
            print(f"❌ Enhanced content stream mining failed: {e}")

        # Technique 8: Image Analysis and Redaction Recovery
        try:
            image_analysis = self.analyze_images_in_pdf(pdf_path)
            if image_analysis:
                file_analysis["techniques_attempted"].append("image_analysis_redaction_recovery")
                file_analysis["image_analysis"] = image_analysis
                print(f"✅ Image Analysis: {len(image_analysis)} images analyzed")
        except Exception as e:
            print(f"❌ Image analysis failed: {e}")

        return file_analysis

    def extract_text_pypdf2(self, pdf_path):
        """Extract text using PyPDF2 - often bypasses visual redactions"""
        text_blocks = []

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            # Split into meaningful blocks
                            blocks = [block.strip() for block in text.split('\n') if block.strip()]
                            for block in blocks:
                                if len(block) > 3:  # Filter out very short fragments
                                    text_blocks.append({
                                        "page": page_num + 1,
                                        "method": "pypdf2_text_extraction",
                                        "content": block,
                                        "confidence": "high"
                                    })
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"   PyPDF2 extraction error: {e}")

        return text_blocks

    def extract_with_pymupdf(self, pdf_path):
        """Advanced extraction with PyMuPDF"""
        results = {
            "fonts": [],
            "images": [],
            "annotations": [],
            "form_fields": []
        }

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Font analysis
                try:
                    fonts = page.get_fonts()
                    for font in fonts:
                        results["fonts"].append({
                            "page": page_num + 1,
                            "font_name": font[3],
                            "font_type": font[1],
                            "embedded": font[2]
                        })
                except Exception as e:
                    pass

                # Image extraction
                try:
                    images = page.get_images(full=True)
                    for img_index, img in enumerate(images):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        if base_image:
                            results["images"].append({
                                "page": page_num + 1,
                                "image_index": img_index,
                                "size": len(base_image["image"]),
                                "ext": base_image["ext"]
                            })
                except Exception as e:
                    pass

                # Annotation extraction
                try:
                    annotations = page.annots()
                    if annotations:
                        for annot in annotations:
                            results["annotations"].append({
                                "page": page_num + 1,
                                "type": annot.type[1] if hasattr(annot, 'type') else "unknown",
                                "rect": list(annot.rect) if hasattr(annot, 'rect') else None
                            })
                except Exception as e:
                    pass

            doc.close()

        except Exception as e:
            print(f"   PyMuPDF extraction error: {e}")

        return results

    def extract_metadata(self, pdf_path):
        """Extract all possible metadata"""
        metadata = {}

        try:
            # PyPDF2 metadata
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if pdf_reader.metadata:
                    metadata["pypdf2"] = {
                        str(key): str(value) for key, value in pdf_reader.metadata.items()
                    }
        except Exception as e:
            pass

        try:
            # PyMuPDF metadata
            doc = fitz.open(pdf_path)
            metadata["pymupdf"] = doc.metadata

            # XMP metadata if available
            try:
                xmp = doc.get_xml_metadata()
                if xmp:
                    metadata["xmp"] = xmp
            except:
                pass

            doc.close()

        except Exception as e:
            pass

        return metadata

    def analyze_content_streams(self, pdf_path):
        """Analyze PDF content streams for hidden/redacted content"""
        hidden_content = []

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        # Get page content stream
                        if '/Contents' in page:
                            contents = page['/Contents']
                            if hasattr(contents, 'get_object'):
                                content_obj = contents.get_object()
                                if hasattr(content_obj, 'get_data'):
                                    stream_data = content_obj.get_data()
                                    if stream_data:
                                        # Look for text operations in stream
                                        stream_str = stream_data.decode('latin-1', errors='ignore')

                                        # Search for text patterns
                                        text_patterns = [
                                            r'Tj\s*(.+?)\s*TJ',  # Text showing operations
                                            r'\(([^)]+)\)\s*Tj',  # Text in parentheses
                                            r'BT\s*(.+?)\s*ET',   # Text blocks
                                        ]

                                        for pattern in text_patterns:
                                            matches = re.findall(pattern, stream_str, re.DOTALL)
                                            for match in matches:
                                                if match.strip() and len(match.strip()) > 3:
                                                    hidden_content.append({
                                                        "page": page_num + 1,
                                                        "method": "content_stream_analysis",
                                                        "pattern": pattern,
                                                        "content": match.strip(),
                                                        "confidence": "medium"
                                                    })

                    except Exception as e:
                        pass

        except Exception as e:
            print(f"   Content stream analysis error: {e}")

        return hidden_content

    def analyze_images_in_pdf(self, pdf_path):
        """Analyze images within PDF for hidden content using enhanced techniques"""
        image_results = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                try:
                    images = page.get_images(full=True)

                    for img_index, img in enumerate(images):
                        xref = img[0]
                        base_image = doc.extract_image(xref)

                        if base_image:
                            image_data = base_image["image"]

                            # Convert to PIL Image for analysis
                            try:
                                pil_image = Image.open(io.BytesIO(image_data))

                                # Enhanced image analysis
                                analysis = {
                                    "page": page_num + 1,
                                    "image_index": img_index,
                                    "format": base_image["ext"],
                                    "size_bytes": len(image_data),
                                    "dimensions": pil_image.size,
                                    "mode": pil_image.mode,
                                    "potential_features": [],
                                    "ocr_attempts": []
                                }

                                # Convert to grayscale for analysis
                                if pil_image.mode != 'L':
                                    gray_image = pil_image.convert('L')
                                else:
                                    gray_image = pil_image

                                img_array = np.array(gray_image)

                                # Look for text-like patterns
                                contrast_ratio = np.std(img_array) / np.mean(img_array) if np.mean(img_array) > 0 else 0
                                if contrast_ratio > 0.3:  # Lower threshold for text detection
                                    analysis["potential_features"].append("potential_text_content")

                                # Check for geometric patterns that might be redacted text
                                height, width = img_array.shape
                                if height > 10 and width > 50:
                                    analysis["potential_features"].append("text-sized_dimensions")

                                # Attempt OCR if pytesseract is available
                                try:
                                    import pytesseract
                                    # Try OCR on the image
                                    ocr_text = pytesseract.image_to_string(gray_image)
                                    if ocr_text.strip():
                                        analysis["ocr_attempts"].append({
                                            "method": "tesseract_ocr",
                                            "text": ocr_text.strip(),
                                            "confidence": "unknown"
                                        })
                                        print(f"      📝 OCR found text on page {page_num + 1}, image {img_index}")
                                except ImportError:
                                    analysis["ocr_attempts"].append({
                                        "method": "tesseract_unavailable",
                                        "error": "pytesseract not installed"
                                    })
                                except Exception as e:
                                    analysis["ocr_attempts"].append({
                                        "method": "tesseract_failed",
                                        "error": str(e)
                                    })

                                # Try alternative OCR-like approach using OpenCV
                                try:
                                    # Simple text detection using contours
                                    _, thresh = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY_INV)
                                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                                    text_like_contours = 0
                                    for contour in contours:
                                        x, y, w, h = cv2.boundingRect(contour)
                                        aspect_ratio = w / float(h) if h > 0 else 0
                                        # Text-like aspect ratios (wider than tall)
                                        if 2 < aspect_ratio < 20 and w > 10 and h > 5:
                                            text_like_contours += 1

                                    if text_like_contours > 0:
                                        analysis["potential_features"].append(f"{text_like_contours}_text_like_contours")

                                except Exception as e:
                                    analysis["potential_features"].append(f"contour_analysis_failed: {str(e)}")

                                # NEW: Attempt to recover redacted images
                                recovered_images = self.attempt_image_redaction_recovery(pil_image, page_num, img_index, pdf_path)
                                if recovered_images:
                                    analysis["recovered_images"] = recovered_images
                                    print(f"      🖼️ Recovered {len(recovered_images)} images from page {page_num + 1}, image {img_index}")

                                image_results.append(analysis)

                            except Exception as e:
                                # If PIL fails, still record basic info
                                image_results.append({
                                    "page": page_num + 1,
                                    "image_index": img_index,
                                    "format": base_image["ext"],
                                    "size_bytes": len(image_data),
                                    "error": str(e)
                                })

                except Exception as e:
                    print(f"   Image extraction error on page {page_num + 1}: {e}")

            doc.close()

        except Exception as e:
            print(f"   PDF image analysis error: {e}")

        return image_results

    def attempt_image_redaction_recovery(self, pil_image, page_num, img_index, pdf_path):
        """Attempt to recover redacted content from images"""
        recovered_images = []

        try:
            # Convert to numpy array for processing
            img_array = np.array(pil_image)
            height, width = img_array.shape[:2]

            # Method 1: Detect and remove solid black rectangles (common redaction technique)
            if len(img_array.shape) == 3:  # Color image
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:  # Grayscale
                gray = img_array

            # Look for solid black regions that might be redactions
            _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)  # Detect very dark areas

            # Find contours of potential redaction areas
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            redaction_masks = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum size for redaction
                    # Check if this is a rectangular redaction
                    rect = cv2.boundingRect(contour)
                    x, y, w, h = rect

                    # Check if this region is mostly solid black/dark
                    roi = gray[y:y+h, x:x+w]
                    if roi.size > 0:
                        dark_pixels = np.sum(roi < 50)  # Count very dark pixels
                        if dark_pixels / roi.size > 0.8:  # 80% dark pixels
                            redaction_masks.append(rect)

            # If we found redaction masks, try to recover the image
            if redaction_masks:
                # Create a mask for inpainting
                mask = np.zeros_like(gray)
                for rect in redaction_masks:
                    x, y, w, h = rect
                    cv2.rectangle(mask, (x, y), (x+w, y+h), 255, -1)

                # Try inpainting to recover content under redaction
                try:
                    # Use OpenCV inpainting
                    inpainted = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)

                    # Convert back to PIL
                    recovered_pil = Image.fromarray(inpainted)

                    recovered_images.append({
                        "method": "redaction_removal_inpainting",
                        "page": page_num + 1,
                        "image_index": img_index,
                        "redaction_masks_removed": len(redaction_masks),
                        "recovered_image_data": self.image_to_base64(recovered_pil),
                        "format": "PNG"
                    })

                except Exception as e:
                    recovered_images.append({
                        "method": "redaction_detection_only",
                        "page": page_num + 1,
                        "image_index": img_index,
                        "redaction_masks_detected": len(redaction_masks),
                        "error": str(e)
                    })

            # Method 2: Look for layered content (text hidden under redaction)
            # This is common where text is rendered first, then redaction applied on top
            try:
                # Try to detect if there are multiple layers by looking at alpha channel or transparency
                if len(img_array.shape) == 3 and img_array.shape[2] == 4:  # RGBA
                    # Separate layers
                    rgb = img_array[:, :, :3]
                    alpha = img_array[:, :, 3]

                    # Look for areas where alpha indicates overlay
                    overlay_mask = alpha < 250  # Semi-transparent areas
                    if np.sum(overlay_mask) > 100:  # Significant overlay area
                        # Try to extract content from under the overlay
                        # This is a simplified approach - real implementation would need more sophisticated layer analysis
                        recovered_images.append({
                            "method": "layer_separation_alpha",
                            "page": page_num + 1,
                            "image_index": img_index,
                            "overlay_area_pixels": int(np.sum(overlay_mask)),
                            "recovered_image_data": self.image_to_base64(Image.fromarray(rgb)),
                            "format": "PNG"
                        })

            except Exception as e:
                pass

            # Method 3: Histogram analysis for unusual patterns
            try:
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist = hist.flatten()

                # Look for unusual histogram patterns that might indicate redaction
                # High concentration in dark areas with some light areas might indicate redaction
                dark_pixels = np.sum(hist[:50])  # Very dark pixels
                light_pixels = np.sum(hist[200:])  # Very light pixels
                total_pixels = np.sum(hist)

                if dark_pixels / total_pixels > 0.7 and light_pixels / total_pixels > 0.1:
                    # Unusual distribution - might have redaction
                    recovered_images.append({
                        "method": "histogram_anomaly_detection",
                        "page": page_num + 1,
                        "image_index": img_index,
                        "dark_pixel_ratio": float(dark_pixels / total_pixels),
                        "light_pixel_ratio": float(light_pixels / total_pixels),
                        "analysis": "Potential redaction pattern detected in histogram"
                    })

            except Exception as e:
                pass

        except Exception as e:
            recovered_images.append({
                "method": "image_recovery_failed",
                "page": page_num + 1,
                "image_index": img_index,
                "error": str(e)
            })

        return recovered_images

    def image_to_base64(self, pil_image):
        """Convert PIL image to base64 string"""
        try:
            import base64
            from io import BytesIO

            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception:
            return None

    def save_recovered_images(self, analysis_results):
        """Save any recovered images from redaction breaking to disk"""
        recovered_count = 0

        # Create output directory for recovered images
        output_dir = "recovered_images"
        os.makedirs(output_dir, exist_ok=True)

        for result in analysis_results:
            filename_base = os.path.splitext(os.path.basename(result["filename"]))[0]

            # Check image analysis results for recovered images
            for image_analysis in result.get("image_analysis", []):
                if "recovered_images" in image_analysis:
                    for recovered_img in image_analysis["recovered_images"]:
                        if "recovered_image_data" in recovered_img and recovered_img["recovered_image_data"]:
                            try:
                                # Decode base64 image data
                                import base64
                                from io import BytesIO

                                image_data = base64.b64decode(recovered_img["recovered_image_data"])
                                pil_image = Image.open(BytesIO(image_data))

                                # Save the recovered image
                                page = recovered_img["page"]
                                img_idx = recovered_img["image_index"]
                                method = recovered_img["method"].replace("_", "_")

                                filename = f"{output_dir}/{filename_base}_page{page}_img{img_idx}_{method}_recovered.png"
                                pil_image.save(filename)

                                print(f"      💾 Saved recovered image: {filename}")
                                recovered_count += 1

                            except Exception as e:
                                print(f"      ❌ Failed to save recovered image: {e}")

        if recovered_count > 0:
            print(f"\n🖼️ Successfully saved {recovered_count} recovered images to '{output_dir}/' directory")
        else:
            print(f"\n📷 No images were recovered from redaction breaking")

    def analyze_redaction_patterns(self, pdf_path):
        """Analyze PDF for redaction patterns and potential hidden content areas"""
        redaction_analysis = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Look for black rectangles that might be redactions
                try:
                    # Get page drawings (vector graphics)
                    drawings = page.get_drawings()

                    for drawing in drawings:
                        # Check for filled black rectangles
                        if hasattr(drawing, 'items') and 'fill' in drawing:
                            fill_color = drawing.get('fill')
                            if fill_color and len(fill_color) >= 3:
                                # Check if it's black or very dark
                                r, g, b = fill_color[:3]
                                if r < 0.1 and g < 0.1 and b < 0.1:  # Dark color
                                    rect = drawing.get('rect')
                                    if rect:
                                        redaction_analysis.append({
                                            "page": page_num + 1,
                                            "type": "potential_redaction",
                                            "rect": list(rect),
                                            "fill_color": fill_color,
                                            "method": "drawing_analysis"
                                        })

                except Exception as e:
                    pass

                # Look for text that's been painted over
                try:
                    text_blocks = page.get_text("dict")
                    for block in text_blocks.get("blocks", []):
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    # Check if text has unusual properties
                                    text = span.get("text", "").strip()
                                    if text and len(text) > 10:  # Substantial text
                                        # Check if text color is unusual (might indicate overlay)
                                        color = span.get("color", [0, 0, 0])
                                        if isinstance(color, (int, float)):
                                            color = [color, color, color]

                                        # If text is very light or has transparency, might be hidden
                                        if len(color) >= 3 and all(c > 0.8 for c in color[:3]):
                                            redaction_analysis.append({
                                                "page": page_num + 1,
                                                "type": "light_text_overlay",
                                                "text": text[:100],
                                                "bbox": span.get("bbox"),
                                                "color": color,
                                                "method": "text_overlay_analysis"
                                            })

                except Exception as e:
                    pass

            doc.close()

        except Exception as e:
            print(f"   Redaction pattern analysis error: {e}")

        return redaction_analysis

    def enhanced_content_stream_mining(self, pdf_path):
        """Enhanced mining of PDF content streams for hidden data"""
        enhanced_content = []

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        # Get all content streams
                        if '/Contents' in page:
                            contents = page['/Contents']
                            content_streams = []

                            # Handle both single and multiple content streams
                            if hasattr(contents, 'get_object'):
                                content_obj = contents.get_object()
                                if isinstance(content_obj, list):
                                    content_streams.extend(content_obj)
                                else:
                                    content_streams.append(content_obj)
                            elif isinstance(contents, list):
                                content_streams.extend(contents)

                            for stream_obj in content_streams:
                                if hasattr(stream_obj, 'get_data'):
                                    try:
                                        stream_data = stream_obj.get_data()
                                        if stream_data:
                                            stream_str = stream_data.decode('latin-1', errors='ignore')

                                            # More comprehensive text extraction patterns
                                            patterns = [
                                                # Standard text operations
                                                r'Tj\s*\(([^)]+)\)',  # Text in parentheses
                                                r'TJ\s*\[([^\]]+)\]',  # Text in arrays
                                                # Hidden text operations
                                                r'\/F\d+\s+\d+\s+Tf\s*\(([^)]+)\)\s*Tj',  # Font and text
                                                # Encoded text
                                                r'BT\s*(.+?)\s*ET',  # Text blocks
                                                # Coordinate and number patterns
                                                r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+m',  # Move operations
                                                r'(\d+)°\s*(\d+)\'\s*([\d.]+)\"?\s*([NS])\s*(\d+)°\s*(\d+)\'\s*([\d.]+)\"?\s*([EW])',  # Coordinates
                                            ]

                                            for pattern_name, pattern in [
                                                ("parentheses_text", patterns[0]),
                                                ("array_text", patterns[1]),
                                                ("font_text", patterns[2]),
                                                ("text_block", patterns[3]),
                                                ("coordinates", patterns[4]),
                                                ("dms_coordinates", patterns[5])
                                            ]:
                                                matches = re.findall(pattern, stream_str, re.DOTALL | re.IGNORECASE)
                                                for match in matches:
                                                    if isinstance(match, tuple):
                                                        match = ' '.join(str(m) for m in match if m)
                                                    if match.strip() and len(match.strip()) > 2:
                                                        enhanced_content.append({
                                                            "page": page_num + 1,
                                                            "method": f"enhanced_content_stream_{pattern_name}",
                                                            "pattern": pattern,
                                                            "content": match.strip(),
                                                            "confidence": "medium"
                                                        })

                                    except Exception as e:
                                        continue

                    except Exception as e:
                        continue

        except Exception as e:
            print(f"   Enhanced content stream mining error: {e}")

        return enhanced_content

    def search_for_targets(self, analysis_results, targets=None):
        """Search analysis results for specific targets"""

        if targets is None:
            targets = [
                "Elva", "ELVA", "elva",
                "Griffon", "GRIFFON", "griffon",
                "ship", "vessel", "wreck", "maritime",
                "coordinates", "location", "position",
                "depth", "sonar", "bathymetric",
                "H13364", "H13366", "H13367", "H13368", "H13369",
                "W00470", "W00555"
            ]

        findings = []

        for result in analysis_results:
            # Search in hidden text
            for text_block in result.get("hidden_text", []):
                content = text_block.get("content", "")
                for target in targets:
                    if target.lower() in content.lower():
                        findings.append({
                            "file": result["filename"],
                            "target": target,
                            "context": content[:200] + "..." if len(content) > 200 else content,
                            "method": text_block.get("method", "unknown"),
                            "page": text_block.get("page", "unknown")
                        })

            # Search in metadata
            metadata = result.get("metadata", {})
            for meta_source, meta_data in metadata.items():
                if isinstance(meta_data, dict):
                    for key, value in meta_data.items():
                        value_str = str(value).lower()
                        for target in targets:
                            if target.lower() in value_str:
                                findings.append({
                                    "file": result["filename"],
                                    "target": target,
                                    "context": f"{key}: {value}",
                                    "method": f"metadata_{meta_source}",
                                    "page": "metadata"
                                })

        return findings

    def process_all_pdfs_unified(self, pdf_directory="."):
        """Process all PDFs in directory using unified approach"""

        print("🔓 UNIFIED REDACTION BREAKER - ALL TECHNIQUES")
        print("=" * 60)
        print("🎯 Target: Break through ALL types of redactions")
        print("📁 Searching for: Elva, Griffon, coordinates, feature IDs, hidden content")
        print("⚙️ Methods: Text bypass, content streams, metadata, image analysis")
        print()

        # Find all PDFs
        pdf_files = []
        for root, dirs, files in os.walk(pdf_directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        print(f"📋 Found {len(pdf_files)} PDF files to analyze")

        all_results = []

        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {os.path.basename(pdf_path)}")

            try:
                result = self.analyze_pdf_comprehensive(pdf_path)
                all_results.append(result)
                self.results["files_analyzed"].append(pdf_path)

                # Quick summary for this file
                total_text = len(result.get("hidden_text", []))
                total_techniques = len(result.get("techniques_attempted", []))
                total_images = len(result.get("image_analysis", []))
                print(f"   📊 Summary: {total_text} text blocks, {total_images} images, {total_techniques} techniques successful")

            except Exception as e:
                print(f"   ❌ Failed to process: {e}")

        # Search for target content
        print("\n🔍 SEARCHING FOR TARGET CONTENT...")
        findings = self.search_for_targets(all_results)

        self.results["blackout_breakthroughs"] = findings
        self.results["total_files"] = len(pdf_files)
        self.results["successful_analyses"] = len(all_results)

        # Save recovered images if any were found
        self.save_recovered_images(all_results)

        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"unified_redaction_breaker_results_{timestamp}.json"

        # Create serializable version of results
        serializable_results = self._make_serializable(self.results)

        try:
            with open(results_file, "w") as f:
                json.dump(serializable_results, f, indent=2)
        except Exception as e:
            print(f"   ⚠️ JSON serialization failed: {e}")
            # Save partial results
            partial_file = f"partial_results_{timestamp}.txt"
            with open(partial_file, "w") as f:
                f.write(f"Total files: {len(pdf_files)}\n")
                f.write(f"Successful analyses: {len(all_results)}\n")
                f.write(f"Findings: {len(findings)}\n")
            results_file = partial_file

        # Print summary
        self.print_summary(findings)

        print(f"\n💾 Complete results saved to: {results_file}")

        return all_results, findings

    def _make_serializable(self, obj):
        """Make object JSON serializable by converting non-serializable types"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            # Convert non-serializable objects to strings
            return str(obj)

    def print_summary(self, findings):
        """Print analysis summary"""

        print("\n🎉 UNIFIED REDACTION BREAKING RESULTS")
        print("=" * 60)
        print(f"📁 Files analyzed: {self.results['successful_analyses']}/{self.results['total_files']}")
        print(f"🔓 Target matches found: {len(findings)}")

        if findings:
            print("\n🎯 TARGET DISCOVERIES:")
            target_counts = {}
            for finding in findings:
                target = finding["target"]
                target_counts[target] = target_counts.get(target, 0) + 1

            for target, count in sorted(target_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {target}: {count} occurrences")

            print("\n📋 SAMPLE FINDINGS:")
            for i, finding in enumerate(findings[:10], 1):  # Show first 10
                print(f"   {i}. File: {finding['file']}")
                print(f"      Target: {finding['target']} | Method: {finding['method']} | Page: {finding['page']}")
                print(f"      Context: {finding['context'][:100]}...")
                print()

            if len(findings) > 10:
                print(f"   ... and {len(findings) - 10} more findings")
        else:
            print("   No target matches found in visible content")
            print("   ℹ️ This could mean:")
            print("     • Redactions are effective")
            print("     • Content is in non-text format")
            print("     • Different search terms needed")

def main():
    """Main unified redaction breaking function"""

    print("🔓 STARTING UNIFIED REDACTION ANALYSIS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print("🎯 Mission: Break through ALL redaction types using combined techniques")
    print()

    # Create unified breaker instance
    breaker = UnifiedRedactionBreaker()

    # Process all PDFs
    try:
        results, findings = breaker.process_all_pdfs_unified()

        print("\n✅ UNIFIED REDACTION BREAKING COMPLETE!")
        print(f"📊 Results: {len(findings)} potential breakthroughs found")

        if findings:
            print("\n🎉 SUCCESS: Multiple redaction breaking techniques successful!")
        else:
            print("\n🔒 No breakthroughs found - redactions appear highly effective")

    except Exception as e:
        print(f"\n❌ Error in unified redaction breaking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()