# cmip6replication

Scripts for downloading CMIP6 datasets from ESGF.

## Usage

### Download datasets

```bash
python download_cmip6.py -c <criteria_file> -d <download_dir> -e <existing_dir>
```

- `-c` - Path or URL to criteria file containing dataset IDs
- `-d` - Directory for new downloads
- `-e` - Directory with existing data (to avoid re-downloading)

Example:
```bash
python download_cmip6.py -c criteria.txt -d /path/to/downloads -e /path/to/existing
```

### Check total size of datasets

```bash
python check_size.py <criteria_file> <existing_dir> <download_dir>
```

Example:
```bash
python check_size.py criteria.txt /path/to/existing /path/to/downloads
```

## Dependencies

- Python 3
- intake_esgf
