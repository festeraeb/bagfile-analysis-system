import sqlite3

def check_sample_data():
    """Check what data was actually inserted"""
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()

    # Get a few records with actual names
    cursor.execute("""
        SELECT id, name, date, latitude, longitude, feature_type, source, historical_place_names
        FROM features
        WHERE name IS NOT NULL AND name != ''
        ORDER BY id
        LIMIT 20
    """)

    records = cursor.fetchall()

    print("Sample records with names:")
    for record in records:
        print(f"ID: {record[0]}")
        print(f"Name: {record[1]}")
        print(f"Date: {record[2]}")
        print(f"Lat/Lon: {record[3]}, {record[4]}")
        print(f"Type: {record[5]}")
        print(f"Source: {record[6]}")
        print(f"Place: {record[7]}")
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    check_sample_data()