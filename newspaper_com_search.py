import sqlite3
import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from urllib.parse import quote_plus, urlencode
import pdfkit
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io

# Directory to save newspaper clips
CLIPS_DIR = 'newspaper_clips'
PDF_DIR = os.path.join(CLIPS_DIR, 'pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters"""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    return filename.strip('_')

def create_wreck_pdf(wreck_id, wreck_name, wreck_date, wreck_location, search_url):
    """Create a PDF for a wreck with search information and instructions"""
    # Sanitize wreck name for filename
    safe_name = sanitize_filename(wreck_name)
    filename = f"wreck_{wreck_id}_{safe_name}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    try:
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph(f"Wreck Research: {wreck_name}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Wreck information
        info_text = f"""
        <b>Wreck ID:</b> {wreck_id}<br/>
        <b>Name:</b> {wreck_name}<br/>
        <b>Date:</b> {wreck_date or 'Unknown'}<br/>
        <b>Location:</b> {wreck_location or 'Unknown'}<br/>
        """

        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Search instructions
        instructions = """
        <b>Newspaper Research Instructions:</b><br/>
        1. Visit the search URL below<br/>
        2. Log in to newspaper.com with your subscription<br/>
        3. Review the search results for relevant articles<br/>
        4. Save any relevant newspaper articles as images or text<br/>
        5. Note the publication date and newspaper name<br/>
        """

        story.append(Paragraph(instructions, styles['Normal']))
        story.append(Spacer(1, 12))

        # Search URL (break into multiple lines if too long)
        url_text = f"<b>Search URL:</b><br/><font size='8'>{search_url}</font>"
        story.append(Paragraph(url_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Additional search terms
        search_terms = f"""
        <b>Suggested additional search terms:</b><br/>
        • "{wreck_name}" shipwreck<br/>
        • "{wreck_name}" sinking<br/>
        • "{wreck_name}" foundered<br/>
        • "{wreck_name}" lost<br/>
        """

        if wreck_location:
            search_terms += f"• {wreck_location} shipwreck<br/>"

        story.append(Paragraph(search_terms, styles['Normal']))
        story.append(Spacer(1, 12))

        # Footer with generation info
        footer = f"<font size='8'>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')} - Wreck Research Database</font>"
        story.append(Paragraph(footer, styles['Normal']))

        # Build PDF
        doc.build(story)

        return filepath

    except Exception as e:
        print(f"Error creating PDF for {wreck_name}: {e}")
        return None

    # Build PDF
    doc.build(story)

    return filepath

def attempt_article_fetch(search_url, wreck_name):
    """Attempt to fetch basic article information (limited due to authentication)"""
    try:
        # This is a placeholder - newspaper.com requires authentication
        # In a real implementation, you would need proper API access or authentication
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # For now, just return placeholder information
        return {
            'status': 'requires_authentication',
            'message': 'Newspaper.com requires login to access articles',
            'search_url': search_url
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'search_url': search_url
        }

def generate_newspaper_com_search_url(wreck_name, wreck_date=None, location=None):
    """Generate newspaper.com search URL"""
    base_url = "https://www.newspapers.com/search/"

    # Clean up wreck name for search
    clean_name = wreck_name.replace('"', '').replace("'", "").strip()

    # Build search parameters
    params = {
        'query': f'"{clean_name}" shipwreck OR sinking OR wreck',
        'sort': 'date_asc'
    }

    # Add date range if available
    if wreck_date:
        try:
            # Try to parse date and create range
            # For shipwrecks, search 10 years before and after the loss date
            year = int(re.search(r'\b(18|19|20)\d{2}\b', wreck_date).group())
            params['dateStart'] = f"{year-10}-01-01"
            params['dateEnd'] = f"{year+10}-12-31"
        except:
            pass

    # Add location if available
    if location:
        params['query'] += f' {location}'

    search_url = f"{base_url}?{urlencode(params)}"
    return search_url

def create_pdf_batch(batch_size=500):
    """Create PDFs for wrecks with newspaper search information"""
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()

    # Get wrecks that don't have PDFs yet
    cursor.execute("""
        SELECT id, name, date, historical_place_names
        FROM features
        WHERE name IS NOT NULL AND name != ''
        AND (newspaper_clip IS NULL OR newspaper_clip = '')
        ORDER BY name
        LIMIT ?
    """, (batch_size,))

    wrecks = cursor.fetchall()

    if not wrecks:
        print("No wrecks found that need PDFs!")
        conn.close()
        return []

    print(f"Creating PDFs for {len(wrecks)} wrecks...")

    pdf_files = []
    pdf_data = []

    for i, (wreck_id, name, date, place) in enumerate(wrecks):
        try:
            # Generate search URL
            search_url = generate_newspaper_com_search_url(name, date, place)

            # Create PDF
            pdf_path = create_wreck_pdf(wreck_id, name, date, place, search_url)

            if pdf_path:
                # Attempt to fetch article info (placeholder)
                article_info = attempt_article_fetch(search_url, name)

                pdf_files.append(pdf_path)
                pdf_data.append({
                    'wreck_id': wreck_id,
                    'name': name,
                    'date': date,
                    'location': place,
                    'search_url': search_url,
                    'pdf_path': pdf_path,
                    'article_info': article_info
                })

                if (i + 1) % 50 == 0:
                    print(f"Created {i + 1} PDFs...")

            # Small delay to avoid overwhelming
            time.sleep(0.05)

        except Exception as e:
            print(f"Error processing {name}: {e}")
            continue

    # Save PDF data to JSON
    json_file = os.path.join(CLIPS_DIR, f'wreck_pdfs_batch_{int(time.time())}.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(pdf_data, f, indent=2, ensure_ascii=False)

    # Update database with PDF references
    updated_count = 0
    for pdf_info in pdf_data:
        try:
            cursor.execute("""
                UPDATE features
                SET newspaper_clip = ?
                WHERE id = ?
            """, (os.path.basename(pdf_info['pdf_path']), pdf_info['wreck_id']))
            updated_count += 1
        except Exception as e:
            print(f"Error updating database for {pdf_info['name']}: {e}")

    conn.commit()
    conn.close()

    print(f"\nPDF Creation Complete!")
    print(f"Created {len(pdf_files)} PDFs in {PDF_DIR}")
    print(f"Updated {updated_count} database records")
    print(f"JSON data saved to: {json_file}")

    return pdf_files

def main():
    import sys

    # Allow batch size as command line argument
    batch_size = 500
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except ValueError:
            print("Invalid batch size, using default of 500")

    print(f"Starting PDF creation with batch size: {batch_size}")
    pdf_files = create_pdf_batch(batch_size)

    print("\nNext steps:")
    print("1. PDFs created in newspaper_clips/pdfs/")
    print("2. Open each PDF to see search instructions")
    print("3. Log in to newspaper.com and follow the links")
    print("4. Save relevant articles and update database manually")
    print("5. PDFs are now attached to each wreck record")
    print(f"6. Run again with larger batch size if needed: python newspaper_com_search.py 1000")

if __name__ == "__main__":
    main()