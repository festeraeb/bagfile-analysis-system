import sqlite3

conn = sqlite3.connect('wrecks.db')
cursor = conn.cursor()

cursor.execute('SELECT name, newspaper_clip FROM features WHERE newspaper_clip IS NOT NULL LIMIT 10')
results = cursor.fetchall()
print('Database records with PDF references:')
for name, pdf in results:
    print(f'  {name}: {pdf}')

cursor.execute('SELECT COUNT(*) FROM features WHERE newspaper_clip IS NOT NULL')
count = cursor.fetchone()[0]
print(f'\nTotal records with PDF references: {count}')

conn.close()