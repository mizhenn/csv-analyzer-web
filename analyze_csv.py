#!/usr/bin/env python3
"""
CLI utility to analyze a CSV from disk and print stats to stdout.
"""

import argparse
import csv
import io
from pathlib import Path

import pandas as pd
import numpy as np


def sniff_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=[",", ";", "\t", "|", ":"])
        return dialect.delimiter
    except Exception:
        return ","


def read_csv_with_fallback(path: Path):
    data_bytes = path.read_bytes()
    encoding_used = "utf-8"
    try:
        text = data_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = data_bytes.decode("latin-1")
        encoding_used = "latin-1"
    detected_delimiter = sniff_delimiter(text[:10000])
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python", low_memory=False)
    return df, encoding_used, detected_delimiter


def human_bytes(num: int) -> str:
    symbols = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    f = float(num)
    while f >= 1024 and i < len(symbols) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.2f} {symbols[i]}"


def main():
    parser = argparse.ArgumentParser(description="Analyze a CSV file and print stats.")
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    args = parser.parse_args()

    df, encoding_used, detected_delimiter = read_csv_with_fallback(args.csv_path)

    rows = len(df)
    cols = df.shape[1]
    dtypes_df = pd.DataFrame({"Column": df.columns, "Dtype": [str(dt) for dt in df.dtypes]})
    missing_per_col = df.isna().sum().reset_index()
    missing_per_col.columns = ["Column", "Missing"]
    total_cells = rows * cols
    overall_missing = int(missing_per_col["Missing"].sum())
    overall_missing_pct = (overall_missing / total_cells * 100.0) if total_cells > 0 else 0.0
    duplicates_count = int(df.duplicated().sum())
    dup_preview_df = df[df.duplicated()].head(10)
    numeric_df = df.select_dtypes(include=[np.number])
    has_numeric = not numeric_df.empty
    numeric_summary_df = df.describe(include=[np.number]).round(3) if has_numeric else pd.DataFrame()
    preview_df = df.head(10)
    mem_usage_bytes = int(df.memory_usage(deep=True).sum())

    print("# CSV Analysis")
    print(f"- File: {args.csv_path}")
    print(f"- Encoding: {encoding_used}")
    print(f"- Detected delimiter: {detected_delimiter}")
    print()
    print("## Dimensions")
    print(f"- Rows: {rows}")
    print(f"- Columns: {cols}")
    print()
    print("## Dtypes")
    print(dtypes_df.to_string(index=False))
    print()
    print("## Missing per column")
    print(missing_per_col.to_string(index=False))
    print()
    print(f"Overall missing: {overall_missing} values ({overall_missing_pct:.3f}%)")
    print()
    print("## Duplicates")
    print(f"- Count: {duplicates_count}")
    if duplicates_count > 0:
        print("Preview (up to 10 rows):")
        print(dup_preview_df.to_string(index=False))
        print()
    print("## Numeric summary")
    if has_numeric:
        print(numeric_summary_df.to_string())
    else:
        print("No numeric columns.")
    print()
    print("## Preview (first 10 rows)")
    print(preview_df.to_string(index=False))
    print()
    print("## Memory usage")
    print(f"- {mem_usage_bytes} bytes ({human_bytes(mem_usage_bytes)})")


if __name__ == "__main__":
    main()
