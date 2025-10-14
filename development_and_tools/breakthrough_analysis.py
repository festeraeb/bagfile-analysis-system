#!/usr/bin/env python3
"""
Redaction Breakthrough Summary
Extract and summarize the discovered hidden content
"""

import json
import re

def extract_coordinates_from_breakthrough():
    """Extract coordinates and wreck data from redaction breakthrough"""
    
    print("🔓 REDACTION BREAKTHROUGH ANALYSIS")
    print("=" * 60)
    
    # Load the breakthrough results
    with open("redaction_breaker_results_20251009_022940.json", "r") as f:
        data = json.load(f)
    
    summary = data["summary"]
    findings = summary["blackout_breakthroughs"]
    
    print(f"📊 BREAKTHROUGH STATISTICS:")
    print(f"   Files analyzed: {len(summary['files_analyzed'])}")
    print(f"   Techniques used: {len(summary['techniques_used'])}")
    print(f"   Discoveries: {len(findings)}")
    print()
    
    # Extract coordinates and wreck data
    coordinates = []
    wrecks = []
    positions = []
    depths = []
    
    for finding in findings:
        context = finding["context"]
        target = finding["target"]
        
        if target == "wreck":
            wrecks.append(finding)
        elif target == "position":
            positions.append(finding)
        elif target == "depth":
            depths.append(finding)
        
        # Extract coordinates using regex
        coord_patterns = [
            r"(\d+°\s*\d+'\s*\d+\.?\d*\"\s*[NS])\s*(\d+°\s*\d+'\s*\d+\.?\d*\"\s*[EW])",
            r"(\d+\.\d+)[°\s]+([NS])[,\s]+(\d+\.\d+)[°\s]+([EW])"
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, context)
            for match in matches:
                if len(match) == 2:  # Lat/Long pair
                    coordinates.append({
                        "lat": match[0],
                        "lon": match[1], 
                        "source_file": finding["file"],
                        "page": finding["page"],
                        "context": context[:100] + "..."
                    })
    
    print(f"🗺️ EXTRACTED COORDINATES: {len(coordinates)}")
    for i, coord in enumerate(coordinates[:10], 1):  # Show first 10
        print(f"   {i}. {coord['lat']} {coord['lon']}")
        print(f"      Source: {coord['source_file']} (page {coord['page']})")
        print(f"      Context: {coord['context']}")
        print()
    
    print(f"🚢 WRECK REFERENCES: {len(wrecks)}")
    for i, wreck in enumerate(wrecks[:5], 1):  # Show first 5
        print(f"   {i}. File: {wreck['file']} (page {wreck['page']})")
        print(f"      Context: {wreck['context'][:150]}...")
        print()
    
    print(f"📍 POSITION DATA: {len(positions)}")
    print(f"🏊 DEPTH DATA: {len(depths)}")
    
    # Look for specific targets
    print(f"\n🎯 SEARCHING FOR SPECIFIC TARGETS:")
    
    elva_mentions = [f for f in findings if "elva" in f["context"].lower()]
    griffon_mentions = [f for f in findings if "griffon" in f["context"].lower()]
    
    print(f"   Elva mentions: {len(elva_mentions)}")
    print(f"   Griffon mentions: {len(griffon_mentions)}")
    
    if elva_mentions:
        print(f"\n🎉 ELVA REFERENCES FOUND:")
        for mention in elva_mentions:
            print(f"   • File: {mention['file']}")
            print(f"     Page: {mention['page']}")
            print(f"     Context: {mention['context']}")
            print()
    
    if griffon_mentions:
        print(f"\n🎉 GRIFFON REFERENCES FOUND:")
        for mention in griffon_mentions:
            print(f"   • File: {mention['file']}")
            print(f"     Page: {mention['page']}")
            print(f"     Context: {mention['context']}")
            print()
    
    # Create coordinate summary file
    coordinate_summary = {
        "extraction_timestamp": "2025-10-09T02:35:00",
        "source": "Redaction breakthrough analysis",
        "total_coordinates": len(coordinates),
        "total_wrecks": len(wrecks),
        "coordinates": coordinates,
        "wreck_references": wrecks,
        "elva_mentions": elva_mentions,
        "griffon_mentions": griffon_mentions
    }
    
    with open("extracted_coordinates_breakthrough.json", "w") as f:
        json.dump(coordinate_summary, f, indent=2)
    
    print(f"\n💾 COORDINATE DATA SAVED: extracted_coordinates_breakthrough.json")
    
    return coordinate_summary

def main():
    """Extract and summarize breakthrough findings"""
    
    print("🔓 ANALYZING REDACTION BREAKTHROUGH RESULTS")
    print("=" * 70)
    print("🎯 Extracting hidden coordinates and wreck data...")
    print()
    
    try:
        summary = extract_coordinates_from_breakthrough()
        
        print(f"\n✅ BREAKTHROUGH ANALYSIS COMPLETE!")
        print(f"🗺️ Extracted {summary['total_coordinates']} coordinate sets")
        print(f"🚢 Found {summary['total_wrecks']} wreck references")
        print(f"🎯 Elva mentions: {len(summary['elva_mentions'])}")
        print(f"🎯 Griffon mentions: {len(summary['griffon_mentions'])}")
        
        if summary['total_coordinates'] > 0:
            print(f"\n🎉 SUCCESS: Broke through PDF redactions!")
            print(f"📍 Hidden coordinates successfully extracted")
        
    except Exception as e:
        print(f"❌ Error analyzing breakthrough: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
