import sqlite3

conn = sqlite3.connect('wrecks.db')
cursor = conn.cursor()

# Delete existing Swayze data
cursor.execute('DELETE FROM features WHERE source LIKE "%swayze%"')
deleted_count = cursor.rowcount
print(f'Deleted {deleted_count} existing Swayze records')

# Check remaining count
cursor.execute('SELECT COUNT(*) FROM features')
remaining_count = cursor.fetchone()[0]
print(f'Remaining records: {remaining_count}')

conn.commit()
conn.close()