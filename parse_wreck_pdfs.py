#!/usr/bin/env python3
"""
PDF Wreck Research Parser
Parses newspaper research PDFs and updates the wreck database with PDF references.
"""

import os
import fitz
import sqlite3
import re
import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFWreckParser:
    """Parser for wreck research PDFs"""

    def __init__(self, pdf_dir="newspaper_clips/pdfs", db_path="wrecks.db"):
        self.pdf_dir = Path(pdf_dir)
        self.db_path = db_path
        self.parsed_data = []

    def parse_single_pdf(self, pdf_path):
        """Parse a single PDF file and extract wreck information"""
        try:
            doc = fitz.open(str(pdf_path))
            text = ""

            # Extract text from all pages
            for page in doc:
                text += page.get_text()

            doc.close()

            # Parse the text using regex patterns
            wreck_info = {}

            # Extract wreck ID from filename
            filename = pdf_path.stem
            id_match = re.search(r'wreck_(\d+)_', filename)
            if id_match:
                wreck_info['wreck_id'] = int(id_match.group(1))

            # Extract information from text
            patterns = {
                'name': r'Wreck Research:\s*([^\n]+)',
                'wreck_id_text': r'Wreck ID:\s*(\d+)',
                'date': r'Date:\s*([^\n]+)',
                'location': r'Location:\s*([^\n]+)',
                'search_url': r'Search URL:\s*(https?://[^\s]+)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if key == 'wreck_id_text':
                        wreck_info['wreck_id'] = int(match.group(1))
                    elif key == 'date':
                        # Try to extract just the year
                        date_str = match.group(1).strip()
                        year_match = re.search(r'(\d{4})', date_str)
                        if year_match:
                            wreck_info[key] = year_match.group(1)
                        else:
                            wreck_info[key] = date_str
                    else:
                        wreck_info[key] = match.group(1).strip()

            # Set PDF path
            wreck_info['pdf_path'] = str(pdf_path)

            # Validate required fields
            if 'wreck_id' in wreck_info and 'name' in wreck_info:
                logger.info(f"Successfully parsed: {wreck_info['name']} (ID: {wreck_info['wreck_id']})")
                return wreck_info
            else:
                logger.warning(f"Missing required fields in {pdf_path}")
                return None

        except Exception as e:
            logger.error(f"Error parsing {pdf_path}: {e}")
            return None

    def parse_all_pdfs(self):
        """Parse all PDF files in the directory"""
        if not self.pdf_dir.exists():
            logger.error(f"PDF directory not found: {self.pdf_dir}")
            return

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to parse")

        for pdf_file in pdf_files:
            wreck_info = self.parse_single_pdf(pdf_file)
            if wreck_info:
                self.parsed_data.append(wreck_info)

        logger.info(f"Successfully parsed {len(self.parsed_data)} wreck PDFs")

    def update_database(self):
        """Update the SQLite database with PDF references"""
        if not self.parsed_data:
            logger.warning("No data to update")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if newspaper_clip column exists, add it if not
            cursor.execute("PRAGMA table_info(features)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'newspaper_clip' not in columns:
                logger.info("Adding newspaper_clip column to database")
                cursor.execute("ALTER TABLE features ADD COLUMN newspaper_clip TEXT")

            # Update records with PDF references
            updated_count = 0
            for wreck_info in self.parsed_data:
                wreck_id = wreck_info.get('wreck_id')
                pdf_path = wreck_info.get('pdf_path')

                if wreck_id and pdf_path:
                    # Update the record with the PDF path
                    cursor.execute("""
                        UPDATE features
                        SET newspaper_clip = ?
                        WHERE CAST(id AS INTEGER) = ?
                    """, (pdf_path, wreck_id))

                    if cursor.rowcount > 0:
                        updated_count += 1
                        logger.info(f"Updated wreck ID {wreck_id} with PDF: {pdf_path}")

            conn.commit()
            conn.close()

            logger.info(f"Database update complete. Updated {updated_count} records.")

        except Exception as e:
            logger.error(f"Database update failed: {e}")

    def generate_report(self):
        """Generate a summary report of the parsing results"""
        report = {
            'parsing_timestamp': datetime.now().isoformat(),
            'total_pdfs_found': len(list(self.pdf_dir.glob("*.pdf"))) if self.pdf_dir.exists() else 0,
            'successfully_parsed': len(self.parsed_data),
            'parsed_wrecks': self.parsed_data,
            'summary': {
                'with_dates': sum(1 for w in self.parsed_data if 'date' in w),
                'with_locations': sum(1 for w in self.parsed_data if 'location' in w),
                'with_search_urls': sum(1 for w in self.parsed_data if 'search_url' in w)
            }
        }

        # Save report
        report_path = Path("newspaper_clips/pdf_parsing_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Parsing report saved to: {report_path}")

        # Print summary
        print("\n" + "="*60)
        print("PDF PARSING SUMMARY")
        print("="*60)
        print(f"Total PDFs found: {report['total_pdfs_found']}")
        print(f"Successfully parsed: {report['successfully_parsed']}")
        print(f"With dates: {report['summary']['with_dates']}")
        print(f"With locations: {report['summary']['with_locations']}")
        print(f"With search URLs: {report['summary']['with_search_urls']}")
        print(f"Report saved to: {report_path}")
        print("="*60)

        return report

def main():
    """Main execution function"""
    parser = PDFWreckParser()

    print("Starting PDF wreck research parsing...")
    print(f"PDF directory: {parser.pdf_dir}")
    print(f"Database: {parser.db_path}")

    # Parse all PDFs
    parser.parse_all_pdfs()

    # Update database
    parser.update_database()

    # Generate report
    parser.generate_report()

    print("\nPDF parsing and database update complete!")

if __name__ == "__main__":
    main()