import sqlite3

conn = sqlite3.connect('wrecks.db')
cursor = conn.cursor()

# Check Swayze data
cursor.execute('SELECT name, historical_place_names, feature_type, source FROM features WHERE source LIKE "%swayze%" LIMIT 5')
swayze_data = cursor.fetchall()
print("Swayze data samples:")
for row in swayze_data:
    print(row)

# Check total counts
cursor.execute('SELECT COUNT(*) FROM features WHERE source LIKE "%swayze%"')
swayze_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM features WHERE latitude IS NOT NULL')
coord_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM features')
total_count = cursor.fetchone()[0]

print(f"\nTotal records: {total_count}")
print(f"Swayze records: {swayze_count}")
print(f"Records with coordinates: {coord_count}")

conn.close()</content>
<parameter name="filePath">c:\Temp\bagfilework\check_swayze_data.py