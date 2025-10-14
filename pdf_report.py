import sqlite3
import os
import json

def generate_pdf_report():
    """Generate a comprehensive report of PDF creation status"""

    # Database statistics
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()

    # Total wrecks
    cursor.execute('SELECT COUNT(*) FROM features')
    total_wrecks = cursor.fetchone()[0]

    # Wrecks with PDFs
    cursor.execute('SELECT COUNT(*) FROM features WHERE newspaper_clip IS NOT NULL AND newspaper_clip != ""')
    pdf_wrecks = cursor.fetchone()[0]

    # Wrecks with coordinates
    cursor.execute('SELECT COUNT(*) FROM features WHERE latitude IS NOT NULL')
    coord_wrecks = cursor.fetchone()[0]

    # Wrecks with both PDFs and coordinates
    cursor.execute('''
        SELECT COUNT(*) FROM features
        WHERE newspaper_clip IS NOT NULL AND newspaper_clip != ""
        AND latitude IS NOT NULL
    ''')
    complete_wrecks = cursor.fetchone()[0]

    conn.close()

    # PDF file statistics
    pdf_dir = 'newspaper_clips/pdfs'
    if os.path.exists(pdf_dir):
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        total_pdf_files = len(pdf_files)
    else:
        total_pdf_files = 0

    # Generate report
    report = f"""
WRECK DATABASE PDF CREATION REPORT
{'='*50}

DATABASE STATISTICS:
• Total wreck records: {total_wrecks:,}
• Records with coordinates: {coord_wrecks:,} ({coord_wrecks/total_wrecks*100:.1f}%)
• Records with PDF references: {pdf_wrecks:,} ({pdf_wrecks/total_wrecks*100:.1f}%)
• Records with both coordinates & PDFs: {complete_wrecks:,} ({complete_wrecks/total_wrecks*100:.1f}%)

PDF FILE STATISTICS:
• PDF files created: {total_pdf_files:,}
• PDF directory: {pdf_dir}

PROGRESS SUMMARY:
• Research PDFs created for newspaper validation
• Each PDF contains search URLs and instructions
• Database linked to PDF files for easy access
• Ready for manual newspaper.com research

NEXT STEPS:
1. Open PDFs from newspaper_clips/pdfs/
2. Follow search URLs to newspaper.com
3. Save relevant articles found during research
4. Update database with article references

USAGE:
• Run: python newspaper_com_search.py [batch_size]
• Default batch size: 500
• Processes wrecks without PDFs first
"""

    print(report)

    # Save report to file
    with open('newspaper_clips/pdf_creation_report.txt', 'w') as f:
        f.write(report)

    print("Report saved to: newspaper_clips/pdf_creation_report.txt")

if __name__ == "__main__":
    generate_pdf_report()