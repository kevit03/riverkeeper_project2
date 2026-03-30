import sys, re
import pandas as pd
import numpy as np
from pathlib import Path

in_path = Path(sys.argv[1])

df = pd.read_csv(in_path, dtype=str, on_bad_lines="skip")

df.columns = (
    pd.Index(df.columns)
    .str.strip()
    .str.lower()
    .str.replace(r"\s+", "_", regex=True)
    .str.replace(r"[^0-9a-zA-Z_]", "", regex=True)
)

for c in df.columns:
    if df[c].dtype == object:
        s = df[c].astype(str).str.strip()
        s = s.str.replace(r"\s+", " ", regex=True)
        s = s.replace({"": np.nan, "nan": np.nan, "None": np.nan, "NaN": np.nan})
        df[c] = s

before = len(df)
df = df.drop_duplicates().dropna(how="all")
after = len(df)

obj_cols = df.select_dtypes(include="object").columns.tolist()

def try_to_date(s):
    dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
    rate = 1 - dt.isna().mean()
    return dt if rate >= 0.8 else None

def try_to_number(s):
    cleaned = s.str.replace(r"[,\$\%]", "", regex=True)
    num = pd.to_numeric(cleaned, errors="coerce")
    rate = 1 - num.isna().mean()
    return num if rate >= 0.8 else None

for c in obj_cols:
    cand = try_to_date(df[c])
    if cand is not None:
        df[c] = cand
        continue
    cand = try_to_number(df[c])
    if cand is not None:
        df[c] = cand

# df.to_csv(out_path, index=False)  # commented out, so no saving

missing_pct = (df.isna().mean() * 100).round(2).sort_values(ascending=False)

print("rows_before:", before)
print("rows_after:", after)
print("duplicates_removed:", before - after)
print("shape:", df.shape)
print("\nmissing_pct_by_column:")
print(missing_pct.to_string())
print("\npreview:")
print(df.head(10))
