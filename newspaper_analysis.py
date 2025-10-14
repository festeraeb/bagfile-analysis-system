import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import quote_plus
import json

# Directory to save newspaper clips
CLIPS_DIR = 'newspaper_clips'
os.makedirs(CLIPS_DIR, exist_ok=True)

def search_newspaper_articles(wreck_name, wreck_date):
    """Search for newspaper articles about the wreck"""
    # Use Google News search (or other news API)
    query = f'"{wreck_name}" shipwreck {wreck_date}'
    url = f'https://www.google.com/search?q={quote_plus(query)}&tbm=nws'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find news results
        articles = []
        for result in soup.find_all('div', class_='Gx5Zad'):
            title_elem = result.find('h3')
            link_elem = result.find('a')
            source_elem = result.find('div', class_='BNeawe UPmit AP7Wnd')

            if title_elem and link_elem:
                articles.append({
                    'title': title_elem.get_text(),
                    'url': link_elem['href'],
                    'source': source_elem.get_text() if source_elem else 'Unknown'
                })

        return articles[:5]  # Return top 5 results

    except Exception as e:
        print(f"Error searching for {wreck_name}: {e}")
        return []

def save_article_clip(article, wreck_name, index):
    """Save a clip of the article (placeholder - would need screenshot tool)"""
    # For now, save article metadata as JSON
    clip_filename = f"{wreck_name.replace(' ', '_')}_{index}.json"
    clip_path = os.path.join(CLIPS_DIR, clip_filename)

    with open(clip_path, 'w') as f:
        json.dump(article, f, indent=2)

    return clip_path

def main():
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()

    # Get all wrecks with names and dates
    cursor.execute("SELECT id, name, date FROM features WHERE name IS NOT NULL AND name != '' LIMIT 100")  # Limit for testing
    wrecks = cursor.fetchall()

    print(f"Processing {len(wrecks)} wrecks for newspaper analysis...")

    for wreck_id, name, date in wrecks:
        print(f"Searching for articles about: {name} ({date})")

        # Search for articles
        articles = search_newspaper_articles(name, date or '')

        if articles:
            print(f"Found {len(articles)} articles")

            # Save clips and update database
            clip_paths = []
            for i, article in enumerate(articles):
                clip_path = save_article_clip(article, name, i)
                clip_paths.append(clip_path)

            # Update database with newspaper clip references
            cursor.execute("""
                UPDATE features
                SET newspaper_clip = ?
                WHERE id = ?
            """, (','.join(clip_paths), wreck_id))
        else:
            print("No articles found")

        # Rate limiting
        time.sleep(1)

    conn.commit()
    conn.close()
    print("Newspaper analysis complete!")

if __name__ == "__main__":
    main()