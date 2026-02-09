#!/usr/bin/env python3
import os
import sys

criteria = sys.argv[1]
existing_dir = sys.argv[2]
download_dir = sys.argv[3]

with open(criteria) as f:
    datasets = [l.strip() for l in f if l.strip()][1:]  # skip header

total_size = 0
for ds in datasets:
    parts = ds.split(".")[:10]
    for base in [existing_dir, download_dir]:
        path = os.path.join(base, *parts)
        if os.path.exists(path):
            for root, _, files in os.walk(path):
                for f in files:
                    if f.endswith(".nc"):
                        total_size += os.path.getsize(os.path.join(root, f))
            break

print(f"{total_size / (1024**3):.2f} GB")
