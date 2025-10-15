#!/usr/bin/env python3
"""
Display Unified Redaction Breaker Results
Parse and display the comprehensive findings from the unified analysis
"""

import json
import os

def display_unified_results():
    """Display the unified redaction breaker results"""

    print("🔓 UNIFIED REDACTION BREAKER RESULTS SUMMARY")
    print("=" * 70)

    # Find the most recent results file
    results_files = [f for f in os.listdir('.') if f.startswith('unified_redaction_breaker_results_')]
    if not results_files:
        print("❌ No unified results files found")
        return

    # Sort by timestamp (newest first)
    results_files.sort(reverse=True)
    results_file = results_files[0]

    print(f"📁 Results File: {results_file}")

    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Basic stats (data is at root level, not under 'summary')
        files_analyzed = len(data.get('files_analyzed', []))
        breakthroughs = data.get('blackout_breakthroughs', [])
        image_results = data.get('image_analysis_results', [])

        print(f"📊 Files Analyzed: {files_analyzed}")
        print(f"🔓 Target Matches Found: {len(breakthroughs)}")
        print(f"🖼️ Images Analyzed: {len(image_results)}")
        print(f"⏰ Analysis Timestamp: {data.get('analysis_timestamp', 'Unknown')}")

        # Techniques used
        techniques = data.get('techniques_used', [])
        print(f"⚙️ Techniques Applied: {len(techniques)}")
        for technique in techniques:
            print(f"   • {technique}")

        if breakthroughs:
            print(f"\n🎯 TARGET DISCOVERIES:")
            print("-" * 50)

            # Group by target
            targets_found = {}
            for breakthrough in breakthroughs:
                target = breakthrough.get('target', 'unknown')
                targets_found[target] = targets_found.get(target, 0) + 1

            # Display target summary
            for target, count in sorted(targets_found.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {target}: {count} occurrences")

            print(f"\n📋 TOP FINDINGS (by target frequency):")
            top_targets = sorted(targets_found.items(), key=lambda x: x[1], reverse=True)[:10]

            for i, (target, count) in enumerate(top_targets, 1):
                # Find sample context for this target
                sample_context = ""
                for breakthrough in breakthroughs:
                    if breakthrough.get('target') == target:
                        sample_context = breakthrough.get('context', '')[:120]
                        break

                print(f"\n   {i}. {target.upper()} ({count} times)")
                print(f"      Sample: {sample_context}...")

            print(f"\n🔍 SAMPLE INDIVIDUAL FINDINGS:")
            for i, breakthrough in enumerate(breakthroughs[:8], 1):  # Show first 8
                print(f"\n   {i}. File: {breakthrough.get('file', 'Unknown')[:50]}...")
                print(f"      Target: {breakthrough.get('target', 'Unknown')}")
                print(f"      Method: {breakthrough.get('method', 'Unknown')}")
                print(f"      Page: {breakthrough.get('page', 'Unknown')}")
                context = breakthrough.get('context', '')[:80]
                print(f"      Context: {context}{'...' if len(breakthrough.get('context', '')) > 80 else ''}")

            if len(breakthroughs) > 8:
                print(f"\n   ... and {len(breakthroughs) - 8} more findings")

        if image_results:
            print(f"\n🖼️ IMAGE ANALYSIS RESULTS:")
            print("-" * 50)
            print(f"   Total images processed across all PDFs: {len(image_results)}")

            # Group by file
            images_by_file = {}
            for img_result in image_results:
                filename = img_result.get('filename', 'unknown')
                if filename not in images_by_file:
                    images_by_file[filename] = []
                images_by_file[filename].append(img_result)

            for filename, images in images_by_file.items():
                print(f"   • {filename}: {len(images)} images analyzed")

        else:
            print("\n🖼️ No images found in PDFs")

        print(f"\n✅ Analysis Complete - Full results saved to {results_file}")

    except json.JSONDecodeError as e:
        print(f"❌ Error reading results file: {e}")
        print("   The file may be corrupted or incomplete")

    except Exception as e:
        print(f"❌ Error processing results: {e}")

if __name__ == "__main__":
    display_unified_results()