#!/usr/bin/env python3
"""Download CMIP6 datasets based on a criteria file."""

import os
import sys
import argparse
import urllib.request
import intake_esgf


def load_criteria_file(source):
    if source.startswith("http://") or source.startswith("https://"):
        print(f"Downloading criteria from: {source}")
        try:
            with urllib.request.urlopen(source) as response:
                content = response.read().decode("utf-8")
            lines = content.strip().split("\n")
        except Exception as e:
            print(f"ERROR: Failed to download: {e}")
            return None
    else:
        if not os.path.exists(source):
            source = os.path.join(os.getcwd(), source)
        if not os.path.exists(source):
            print(f"ERROR: File not found: {source}")
            return None
        print(f"Loading criteria from: {source}")
        with open(source) as f:
            lines = [line.strip() for line in f.readlines()]

    datasets = []
    for i, line in enumerate(lines):
        if i == 0 and "project" in line.lower() and "activity" in line.lower():
            continue
        if line.strip():
            datasets.append(line.strip())

    print(f"Found {len(datasets)} datasets")
    return datasets


def get_dataset_path(dataset_id, base_dir):
    parts = dataset_id.split(".")
    if len(parts) < 10:
        return None
    return os.path.join(base_dir, *parts[:10])


def check_existing_datasets(datasets, existing_dir, download_dir):
    in_existing = []
    in_download = []
    need_download = []

    for ds in datasets:
        path_existing = get_dataset_path(ds, existing_dir)
        path_download = get_dataset_path(ds, download_dir)

        if path_existing and os.path.exists(path_existing):
            in_existing.append(ds)
        elif path_download and os.path.exists(path_download):
            in_download.append(ds)
        else:
            need_download.append(ds)

    return in_existing, in_download, need_download


def build_search_params(datasets):
    need_set = set()
    params = {
        "project": set(),
        "activity_id": set(),
        "institution_id": set(),
        "source_id": set(),
        "experiment_id": set(),
        "variant_label": set(),
        "table_id": set(),
        "variable_id": set(),
        "grid_label": set(),
    }

    fields = list(params.keys())

    for ds in datasets:
        parts = ds.split(".")
        if len(parts) < 9:
            continue
        key = ".".join(parts[:9])
        need_set.add(key)
        for i, field in enumerate(fields):
            params[field].add(parts[i])

    params = {k: list(v) for k, v in params.items()}
    return params, need_set


def main():
    parser = argparse.ArgumentParser(description="Download CMIP6 datasets")
    parser.add_argument("--criteria", "-c", required=True, help="Criteria file path or URL")
    parser.add_argument("--download-dir", "-d", required=True, help="Download directory")
    parser.add_argument("--existing-dir", "-e", required=True, help="Existing data directory")
    args = parser.parse_args()

    datasets = load_criteria_file(args.criteria)
    if not datasets:
        sys.exit(1)

    in_existing, in_download, need_download = check_existing_datasets(
        datasets, args.existing_dir, args.download_dir
    )

    print(f"Total: {len(datasets)}, Existing: {len(in_existing)}, Downloaded: {len(in_download)}, Need: {len(need_download)}")

    if not need_download:
        print("All datasets already present")
        sys.exit(0)

    for ds in need_download[:10]:
        print(ds)
    if len(need_download) > 10:
        print(f"and {len(need_download) - 10} more")

    intake_esgf.conf.set(
        local_cache=args.download_dir,
        esg_dataroot=args.existing_dir,
        indices={"esgf.ceda.ac.uk": True},
        break_on_error=False,
    )

    print("Searching ESGF")
    params, need_set = build_search_params(need_download)

    cat = intake_esgf.catalog.ESGFCatalog()
    subset = cat.search(**params)
    print(f"Search returned {len(subset.df)} results")

    df = subset.df.copy()
    df["key"] = (
        df["project"] + "." + df["activity_drs"] + "." + df["institution_id"] + "." +
        df["source_id"] + "." + df["experiment_id"] + "." + df["member_id"] + "." +
        df["table_id"] + "." + df["variable_id"] + "." + df["grid_label"]
    )

    mask = df["key"].isin(need_set)
    not_found = need_set - set(df.loc[mask, "key"])

    print(f"Matched: {mask.sum()}, Not on ESGF: {len(not_found)}")

    if not_found:
        print("Not available on ESGF:")
        for nf in sorted(not_found):
            print(nf)

    if mask.sum() > 0:
        print(f"Downloading {mask.sum()} datasets")
        subset.df = df[mask].drop(columns=["key"])
        dsdict = subset.to_dataset_dict(add_measures=False)
        print(f"Loaded {len(dsdict)} datasets")

    total_files = 0
    total_size = 0
    if os.path.exists(args.download_dir):
        for root, _, files in os.walk(args.download_dir):
            for f in files:
                if f.endswith(".nc"):
                    total_files += 1
                    total_size += os.path.getsize(os.path.join(root, f))

    print(f"Downloaded: {total_files} files, {total_size / (1024**3):.2f} GB")


if __name__ == "__main__":
    main()
