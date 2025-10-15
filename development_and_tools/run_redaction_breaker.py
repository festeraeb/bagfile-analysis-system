#!/usr/bin/env python3
"""
Run Redaction Breaker on Tools PDFs
Execute advanced redaction breaking on the PDFs in development_and_tools folder
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from advanced_redaction_breaker import AdvancedRedactionBreaker

def main():
    """Run redaction breaking on tools PDFs"""

    print("🔓 RUNNING REDACTION BREAKER ON TOOLS PDFs")
    print("=" * 60)
    print("📁 Target Directory: development_and_tools")
    print("🎯 Breaking redactions on SHPO Feature Reports")
    print()

    # Create breaker instance
    breaker = AdvancedRedactionBreaker()

    # Process PDFs in current directory (development_and_tools)
    try:
        results, findings = breaker.process_all_pdfs(pdf_directory=".")

        print(f"\n✅ REDACTION BREAKING COMPLETE!")
        print(f"📊 Results: {len(findings)} potential breakthroughs found")

        if findings:
            print("\n🎉 SUCCESS: Some redactions may have been broken!")
        else:
            print("\n🔒 No breakthroughs found - redactions appear effective")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()