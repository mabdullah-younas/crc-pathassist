import pandas as pd
import json
import re

# 1. Load your actual CSV
meta = pd.read_csv(r"G:\My Drive\Colorectal Cancer\Surgen\SR386_labels.csv") 

# 2. Force the case_id column to be a string
meta["case_id"] = meta["case_id"].astype(str)

# 3. Load the patches
with open("patch_index.json", "r") as f:
    patch_index = json.load(f)

records = []

for entry in patch_index:
    raw_case_id = str(entry["case_id"])
    
    # 4. Extract the clean ID from the filename
    # This looks for the letter 'T' followed by digits (e.g., 'T001' -> '001')
    match = re.search(r'T(\d+)', raw_case_id)
    
    if match:
        # Convert "001" to int (becomes 1) to drop leading zeros, then back to string
        clean_id = str(int(match.group(1)))
    else:
        print(f"Warning: Could not parse a valid ID from filename {raw_case_id}")
        continue

    # Find the matching row in the CSV using the CLEAN ID
    row = meta[meta["case_id"] == clean_id]
    
    if row.empty:
        print(f"Warning: No metadata found in CSV for parsed ID {clean_id} (from {raw_case_id})")
        continue
        
    # Grab that specific row as a dictionary-like object
    row = row.iloc[0]
    
    # Map the data using the actual column names
    records.append({
        # We keep the raw_case_id here because this is what the patch folders are named!
        "case_id":   raw_case_id, 
        "patches":   entry["patches"],
        
        "kras":      str(row.get("kras_ex_2", "unknown")),
        "nras":      str(row.get("nras_ex_2", "unknown")),
        "braf":      str(row.get("braf_mutation", row.get("braf_mut", "unknown"))), 
        "mmr":       str(row.get("mmr_ihc", "unknown")),
        
        "stage":     str(row.get("stage", "")),
        "pT":        str(row.get("pT", "")),
        "pN":        str(row.get("pN", "")),
        
        "survival":  str(row.get("days_till_death", "")) 
    })

# Save the unified dataset
with open("dataset.json", "w") as f:
    json.dump(records, f, indent=2)

print(f"Success! {len(records)} unified records built.")