import pandas as pd

excel_path = 'Swayze2019-1.xlsx'
xls = pd.ExcelFile(excel_path)
df = pd.read_excel(excel_path, sheet_name=0, header=None)

print('Looking for headers...')
for i in range(15):
    row = df.iloc[i]
    if 'Vessel Name' in str(row.values):
        print(f'Headers found at row {i}:')
        headers = row.tolist()
        for j, header in enumerate(headers):
            if header and str(header).strip():
                print(f'  {j}: {header}')
        break

# Also show a sample of the data
print('\nSample data rows:')
for i in range(5, 10):
    row = df.iloc[i]
    print(f'Row {i}: {row.values}')