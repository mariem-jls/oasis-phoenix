import pandas as pd
import numpy as np
import sys

path = 'data/combined_clean.csv'
df = pd.read_csv(path)

print("=" * 80)
print("DIAGNOSTIC SCAN: OASIS PHOENIX DATA INTEGRITY")
print("=" * 80)

print("\n[1] DATASET STRUCTURE")
print(f"Shape: {df.shape} rows × {df.shape[1]} columns")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Total rows: {len(df)}")

print("\n[2] LAST 5 ROWS (SO₂, NDVI, Health Risk)")
print(df[['date', 'SO2_column_number_density', 'NDVI', 'health_risk_index']].tail())

print("\n[3] SO₂ STATISTICS")
print(df['SO2_column_number_density'].describe())
print(f"Min: {df['SO2_column_number_density'].min()}")
print(f"Max: {df['SO2_column_number_density'].max()}")
print(f"Rows with SO₂ = 0.0: {(df['SO2_column_number_density'] == 0.0).sum()}")
print(f"Rows with SO₂ < 0.0001: {(df['SO2_column_number_density'] < 0.0001).sum()}")

print("\n[4] NDVI STATISTICS")
print(df['NDVI'].describe())
print(f"Unique NDVI values: {df['NDVI'].nunique()}")

print("\n[5] MISSING SPATIAL COLUMNS")
has_zone = 'zone' in df.columns
has_lat = any('lat' in c.lower() for c in df.columns)
has_lon = any('lon' in c.lower() for c in df.columns)
print(f"Has 'zone' column: {has_zone}")
print(f"Has latitude column: {has_lat}")
print(f"Has longitude column: {has_lon}")

print("\n[6] DATA QUALITY CHECKS")
print(f"Nulls total: {df.isnull().sum().sum()}")
print(f"Inf values: {np.isinf(df.select_dtypes(include=[np.number_]).values).sum()}")

print("\n[7] ANOMALY LIST SAMPLE (Should be realistic)")
if 'is_anomaly' in df.columns:
    anomalies = df[df['is_anomaly'] == 1].nlargest(5, 'anomaly_score')
    print(anomalies[['date', 'SO2_column_number_density', 'anomaly_score']].to_string())
else:
    print("No 'is_anomaly' column found")

print("\n[8] HEALTH RISK INDEX DISTRIBUTION")
print(df['health_risk_index'].describe())
if 'risk_level' in df.columns:
    print(f"Risk levels: {df['risk_level'].value_counts().to_dict()}")

print("\n[9] ALL COLUMNS")
print(f"Columns ({len(df.columns)}): {df.columns.tolist()}")

print("\n[10] LAST ROW DETAILED")
last_row = df.iloc[-1]
print("Last row values (first 10 cols):")
for col in df.columns[:10]:
    print(f"  {col}: {last_row[col]}")
