# CRC-PathAssist Data Pipeline

Dataset preparation and preprocessing scripts for training and evaluation.

## Overview

This directory contains tools for:
- Extracting H&E patches from CZI (Carl Zeiss Image) microscopy files
- Creating train/validation/test splits
- Verifying label consistency
- Computing dataset statistics

**Note**: These scripts are used for dataset development, not required for running the application.

## Files

- **build_dataset.py** — Extract patches from CZI files
  - Input: CZI files from SurGen dataset
  - Output: PNG patches at specified magnification
  - Filters patches by tissue content

- **make_splits.py** — Create train/val/test splits
  - Stratified splitting by case
  - Generates metadata JSON for tracking

- **check_labels.py** — Verify label consistency
  - Check for duplicate cases
  - Validate morphological feature annotations

- **test_discordance.py** — Test staging discordance detection
  - Compare model estimates vs. reference labels
  - Generate discordance statistics

- **dataprep_merger.py** — Merge datasets
  - Combine multiple dataset sources

- **finalize_dataset.py** — Final dataset validation
  - Create final splits with metadata

## Usage

These scripts are designed for development only and require additional dependencies:

```bash
# Optional: Install data processing dependencies
pip install pillow numpy tqdm pylibCZIrw pandas scikit-learn
```

**Note**: The main application does NOT require these scripts. They are provided for reference and dataset reproducibility.

## Data Sources

- **SurGen Dataset**: Colorectal cancer H&E patches
  - Resolution: 0.1112 MPP (High magnification)
  - Format: CZI (Zeiss) or PNG patches

- **SR386**: Internal colorectal cancer dataset (57 cases)
  - Used for survival model validation

## Typical Workflow (Development Only)

```bash
# 1. Extract patches from raw CZI files
python build_dataset.py --input data/raw/czi_files --output data/patches

# 2. Create splits
python make_splits.py --input data/patches --output data/splits

# 3. Verify labels
python check_labels.py --input data/splits

# 4. Finalize dataset
python finalize_dataset.py --input data/splits --output data/final
```

## Important Notes

- These scripts require **large storage** for image patches (~500GB+)
- CZI file reading requires `pylibCZIrw` (optional dependency)
- Intended for **development/research** only
- Not part of the production application deployment

## For Hackathon Submission

Include this directory for **reproducibility and transparency**:
- Shows how datasets were prepared
- Demonstrates data handling and validation
- Helps judges understand the data pipeline

**However**, these scripts are NOT required to run the application.
