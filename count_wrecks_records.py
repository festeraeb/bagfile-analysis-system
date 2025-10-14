import sqlite3

def main():
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM features')
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Total records in features table: {count}")

if __name__ == "__main__":
    main()
