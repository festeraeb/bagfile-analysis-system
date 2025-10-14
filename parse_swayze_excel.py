import pandas as pd
import sqlite3
import json

# Parse Swayze Excel file
excel_path = 'Swayze2019-1.xlsx'
xls = pd.ExcelFile(excel_path)
print("Sheet names:", xls.sheet_names)

df = pd.read_excel(excel_path, sheet_name=0, header=None)  # Read first sheet without headers

print("Raw data shape:", df.shape)
print("First 10 rows:")
print(df.head(10))

# Find where the actual data starts
for i in range(10):
    row = df.iloc[i]
    if 'Vessel Name' in str(row.values):
        print(f"Headers found at row {i}: {row.values}")
        headers = row.tolist()
        df_data = df.iloc[i+1:]
        df_data.columns = headers
        break
else:
    print("Could not find headers. Using default.")
    df_data = df

print("Data shape after processing:", df_data.shape)
print("First 5 data rows:")
print(df_data.head())

# Connect to SQLite database
conn = sqlite3.connect('wrecks.db')
cursor = conn.cursor()

# Insert Swayze data into database
for index, row in df_data.iterrows():
    # Combine location information
    loss_place = str(row.get('Loss Place', '')) if pd.notna(row.get('Loss Place')) else ''
    lake = str(row.get('Lake', '')) if pd.notna(row.get('Lake')) else ''
    location_info = f"{loss_place} ({lake})" if lake else loss_place

    cursor.execute("""
        INSERT INTO features (name, date, latitude, longitude, depth, feature_type, source, historical_place_names)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(row.get('Vessel Name', '')) if pd.notna(row.get('Vessel Name')) else None,
        str(row.get('Loss Date', '')) if pd.notna(row.get('Loss Date')) else None,
        None,  # latitude - will be estimated later
        None,  # longitude - will be estimated later
        None,  # depth - not in this dataset
        str(row.get('Type', '')) if pd.notna(row.get('Type')) else None,
        'Swayze2019-1.xlsx',
        location_info if location_info else None
    ))

conn.commit()
conn.close()

print("Swayze data inserted into database.")