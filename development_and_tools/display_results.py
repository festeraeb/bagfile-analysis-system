#!/usr/bin/env python3
"""
Display Redaction Breaker Results
Parse and display the findings from the redaction breaking analysis
"""

import json
import os
from datetime import datetime

def display_results():
    """Display the redaction breaker results"""

    print("🔓 REDACTION BREAKER RESULTS SUMMARY")
    print("=" * 60)

    # Find the most recent results file
    results_files = [f for f in os.listdir('.') if f.startswith('redaction_breaker_results_') and f.endswith('.json')]
    if not results_files:
        print("❌ No results files found")
        return

    # Sort by timestamp (newest first)
    results_files.sort(reverse=True)
    results_file = results_files[0]

    print(f"📁 Results File: {results_file}")

    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        summary = data.get('summary', {})

        # Basic stats
        files_analyzed = len(summary.get('files_analyzed', []))
        breakthroughs = summary.get('blackout_breakthroughs', [])

        print(f"📊 Files Analyzed: {files_analyzed}")
        print(f"🎯 Target Matches Found: {len(breakthroughs)}")
        print(f"⏰ Analysis Timestamp: {summary.get('analysis_timestamp', 'Unknown')}")

        if breakthroughs:
            print(f"\n🎉 SUCCESSFUL BREAKTHROUGHS:")
            print("-" * 40)

            # Group by target
            targets_found = {}
            for breakthrough in breakthroughs:
                target = breakthrough.get('target', 'unknown')
                targets_found[target] = targets_found.get(target, 0) + 1

            # Display target summary
            print("📈 TARGETS DISCOVERED:")
            for target, count in sorted(targets_found.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {target}: {count} occurrences")

            print(f"\n📋 SAMPLE FINDINGS (first 5):")
            for i, breakthrough in enumerate(breakthroughs[:5], 1):
                print(f"\n   {i}. File: {breakthrough.get('file', 'Unknown')}")
                print(f"      Target: {breakthrough.get('target', 'Unknown')}")
                print(f"      Method: {breakthrough.get('method', 'Unknown')}")
                print(f"      Page: {breakthrough.get('page', 'Unknown')}")
                context = breakthrough.get('context', '')[:150]
                print(f"      Context: {context}{'...' if len(breakthrough.get('context', '')) > 150 else ''}")

            if len(breakthroughs) > 5:
                print(f"\n   ... and {len(breakthroughs) - 5} more findings")

        else:
            print("\n🔒 No breakthroughs found")
            print("   Redactions appear to be effective against these techniques")

        print(f"\n✅ Analysis Complete - Results saved to {results_file}")

    except json.JSONDecodeError as e:
        print(f"❌ Error reading results file: {e}")
        print("   The file may be corrupted or incomplete due to serialization issues")

    except Exception as e:
        print(f"❌ Error processing results: {e}")

if __name__ == "__main__":
    display_results()