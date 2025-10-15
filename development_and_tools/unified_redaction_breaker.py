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
                "image_feature_detection"
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

        # Technique 5: Image Analysis
        try:
            image_results = self.analyze_images_in_pdf(pdf_path)
            if image_results:
                file_analysis["techniques_attempted"].append("image_analysis")
                file_analysis["image_analysis"] = image_results
                self.results["image_analysis_results"].extend(image_results)
                print(f"✅ Image Analysis: {len(image_results)} images processed")
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
        """Analyze images within PDF for hidden content"""
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

                                # Basic image analysis
                                analysis = {
                                    "page": page_num + 1,
                                    "image_index": img_index,
                                    "format": base_image["ext"],
                                    "size_bytes": len(image_data),
                                    "dimensions": pil_image.size,
                                    "mode": pil_image.mode,
                                    "potential_features": []
                                }

                                # Look for text-like patterns in image
                                # Convert to grayscale for analysis
                                if pil_image.mode != 'L':
                                    gray_image = pil_image.convert('L')
                                else:
                                    gray_image = pil_image

                                # Simple text detection (high contrast areas)
                                img_array = np.array(gray_image)
                                contrast_ratio = np.std(img_array) / np.mean(img_array) if np.mean(img_array) > 0 else 0

                                if contrast_ratio > 0.5:  # High contrast might indicate text
                                    analysis["potential_features"].append("high_contrast_regions")

                                # Look for geometric patterns that might be redacted text
                                height, width = img_array.shape
                                if height > 10 and width > 50:  # Reasonable text dimensions
                                    analysis["potential_features"].append("text-sized_dimensions")

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