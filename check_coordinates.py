import sqlite3

def check_coordinates_status():
    """Check how many features have vs. don't have coordinates"""
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()

    # Count total features
    cursor.execute("SELECT COUNT(*) FROM features")
    total = cursor.fetchone()[0]

    # Count with coordinates
    cursor.execute("SELECT COUNT(*) FROM features WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    with_coords = cursor.fetchone()[0]

    # Count without coordinates
    without_coords = total - with_coords

    print(f"Database Status:")
    print(f"Total features: {total}")
    print(f"With coordinates: {with_coords}")
    print(f"Without coordinates: {without_coords}")
    print(".1f")

    # Show sample of features without coordinates
    if without_coords > 0:
        cursor.execute("""
            SELECT name, date, historical_place_names, source
            FROM features
            WHERE latitude IS NULL OR longitude IS NULL
            LIMIT 10
        """)
        samples = cursor.fetchall()

        print("\nSample features without coordinates:")
        for sample in samples:
            print(f"- {sample[0]} ({sample[1] or 'no date'}) - {sample[2] or 'no location'} - Source: {sample[3]}")

    conn.close()

if __name__ == "__main__":
    check_coordinates_status()