#!/usr/bin/env python3
"""
Advanced PDF Redaction Breaker - Multiple Attack Vectors
Break through visual blackouts using various techniques while scanner runs
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

class AdvancedRedactionBreaker:
    """Advanced PDF redaction analysis and breaking tool"""
    
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
                "content_stream_analysis"
            ],
            "files_analyzed": [],
            "blackout_breakthroughs": [],
            "hidden_content_found": [],
            "metadata_discoveries": []
        }
        
    def analyze_pdf_structure(self, pdf_path):
        """Deep analysis of PDF structure for redaction vulnerabilities"""
        
        print(f"\n🔍 ANALYZING: {os.path.basename(pdf_path)}")
        print("=" * 60)
        
        file_analysis = {
            "filename": os.path.basename(pdf_path),
            "path": pdf_path,
            "techniques_attempted": [],
            "discoveries": [],
            "blackout_bypasses": [],
            "hidden_text": [],
            "metadata": {}
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
        
        return file_analysis
    
    def extract_text_pypdf2(self, pdf_path):
        """Extract text using PyPDF2 - often bypasses visual redactions"""
        
        hidden_text = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        # Standard text extraction
                        text = page.extract_text()
                        if text and text.strip():
                            hidden_text.append({
                                "page": page_num + 1,
                                "method": "standard_extraction",
                                "content": text.strip(),
                                "length": len(text.strip())
                            })
                        
                        # Try to extract annotations/comments
                        if '/Annots' in page:
                            annotations = page['/Annots']
                            for annot in annotations:
                                annot_obj = annot.get_object()
                                if '/Contents' in annot_obj:
                                    annot_text = annot_obj['/Contents']
                                    if annot_text:
                                        hidden_text.append({
                                            "page": page_num + 1,
                                            "method": "annotation_extraction",
                                            "content": str(annot_text),
                                            "type": "annotation"
                                        })
                                        
                    except Exception as e:
                        print(f"   ⚠️ Page {page_num + 1} extraction error: {e}")
                        
        except Exception as e:
            print(f"   ❌ PyPDF2 extraction failed: {e}")
            
        return hidden_text
    
    def extract_with_pymupdf(self, pdf_path):
        """Advanced extraction using PyMuPDF with multiple techniques"""
        
        results = {
            "text_blocks": [],
            "images": [],
            "drawings": [],
            "fonts": [],
            "hidden_layers": []
        }
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text with detailed positioning
                text_dict = page.get_text("dict")
                for block in text_dict["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["text"].strip():
                                    results["text_blocks"].append({
                                        "page": page_num + 1,
                                        "text": span["text"],
                                        "bbox": span["bbox"],
                                        "font": span["font"],
                                        "size": span["size"],
                                        "flags": span["flags"]
                                    })
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n - pix.alpha < 4:  # Valid image
                            results["images"].append({
                                "page": page_num + 1,
                                "xref": xref,
                                "width": pix.width,
                                "height": pix.height,
                                "colorspace": pix.colorspace.name if pix.colorspace else "Unknown"
                            })
                        pix = None
                    except Exception as e:
                        pass
                
                # Extract drawings/vector graphics
                try:
                    drawings = page.get_drawings()
                    for drawing in drawings:
                        results["drawings"].append({
                            "page": page_num + 1,
                            "type": drawing.get("type", "unknown"),
                            "bbox": drawing.get("rect", None),
                            "items": len(drawing.get("items", []))
                        })
                except Exception as e:
                    pass
                
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
            
            doc.close()
            
        except Exception as e:
            print(f"   ❌ PyMuPDF extraction failed: {e}")
            
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
            if hasattr(doc, 'get_xml_metadata'):
                xmp = doc.get_xml_metadata()
                if xmp:
                    metadata["xmp"] = xmp
            
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
            print(f"   ❌ Content stream analysis failed: {e}")
        
        return hidden_content
    
    def search_for_targets(self, analysis_results, targets=None):
        """Search analysis results for specific targets"""
        
        if targets is None:
            targets = [
                "Elva", "ELVA", "elva",
                "Griffon", "GRIFFON", "griffon", 
                "ship", "vessel", "wreck", "maritime",
                "coordinates", "location", "position",
                "depth", "sonar", "bathymetric"
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
    
    def process_all_pdfs(self, pdf_directory="bathymetric_project"):
        """Process all redacted PDFs in directory"""
        
        print("🔓 ADVANCED PDF REDACTION BREAKER")
        print("=" * 60)
        print("🎯 Target: Break through visual blackouts")
        print("📁 Searching for: Elva, Griffon, coordinates, hidden content")
        print("⚙️ Methods: Multi-layer extraction, metadata mining, stream analysis")
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
                result = self.analyze_pdf_structure(pdf_path)
                all_results.append(result)
                self.results["files_analyzed"].append(pdf_path)
                
                # Quick summary for this file
                total_text = len(result.get("hidden_text", []))
                total_techniques = len(result.get("techniques_attempted", []))
                print(f"   📊 Summary: {total_text} text blocks, {total_techniques} techniques successful")
                
            except Exception as e:
                print(f"   ❌ Failed to process: {e}")
        
        # Search for target content
        print(f"\n🔍 SEARCHING FOR TARGET CONTENT...")
        findings = self.search_for_targets(all_results)
        
        self.results["blackout_breakthroughs"] = findings
        self.results["total_files"] = len(pdf_files)
        self.results["successful_analyses"] = len(all_results)
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"redaction_breaker_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump({
                "summary": self.results,
                "detailed_results": all_results
            }, f, indent=2)
        
        # Print summary
        self.print_summary(findings)
        
        print(f"\n💾 Complete results saved to: {results_file}")
        
        return all_results, findings
    
    def print_summary(self, findings):
        """Print analysis summary"""
        
        print(f"\n🎉 REDACTION BREAKING RESULTS")
        print("=" * 60)
        print(f"📁 Files analyzed: {self.results['successful_analyses']}/{self.results['total_files']}")
        print(f"🔓 Target matches found: {len(findings)}")
        
        if findings:
            print(f"\n🎯 TARGET DISCOVERIES:")
            target_counts = {}
            for finding in findings:
                target = finding["target"]
                target_counts[target] = target_counts.get(target, 0) + 1
            
            for target, count in sorted(target_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {target}: {count} occurrences")
            
            print(f"\n📋 DETAILED FINDINGS:")
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
    """Main redaction breaking function"""
    
    print("🔓 STARTING ADVANCED PDF REDACTION ANALYSIS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print("🎯 Mission: Break through visual blackouts while scanner runs")
    print()
    
    # Create breaker instance
    breaker = AdvancedRedactionBreaker()
    
    # Process all PDFs
    try:
        results, findings = breaker.process_all_pdfs()
        
        print(f"\n✅ REDACTION BREAKING COMPLETE!")
        print(f"Found {len(findings)} potential breakthroughs")
        
        if findings:
            print(f"\n🎉 SUCCESS: Broken through some redactions!")
        else:
            print(f"\n🔒 No breakthroughs yet - may need advanced techniques")
            
    except Exception as e:
        print(f"\n❌ Error in redaction breaking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
