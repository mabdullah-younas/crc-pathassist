import json
from collections import Counter

# 1. Load the merged dataset
with open("dataset.json", "r") as f:
    data = json.load(f)

# Setup counters for the audit
stage_dist = Counter()
nx_cases = []
yp_cases = []

# 2. Normalize and Audit
for c in data:
    # --- AUDIT ---
    # Track stages
    stage_dist[str(c.get("stage", "unknown"))] += 1
    
    # Track missing lymph node data
    if str(c.get("pN")) == "NX":
        nx_cases.append(c["case_id"])
    
    # Track post-neoadjuvant cases (yp prefix)
    pT_val = str(c.get("pT", ""))
    c["post_neoadjuvant"] = pT_val.startswith("yp")
    if c["post_neoadjuvant"]:
        yp_cases.append(c["case_id"])

    # --- NORMALIZE ---
    # Clean up survival status
    s = str(c.get("survival", "nan"))
    if s.lower() == "alive":
        c["survival_status"] = "alive"
    elif s.lower() == "nan" or s == "":
        c["survival_status"] = "unknown"
    else:
        c["survival_status"] = f"days:{s}"

    # Prevent BRAF hallucination
    if c.get("braf") == "unknown":
        c["braf"] = "not_tested"

# Save the cleaned dataset back to the main file
with open("dataset.json", "w") as f:
    json.dump(data, f, indent=2)

print("--- Data Audit Results ---")
print("Stage distribution:", dict(stage_dist))
print("NX (no lymph node data):", len(nx_cases))
print("Post-neoadjuvant (yp prefix):", len(yp_cases))

# 3. Create the Curated Demo Set
demo_ids = [
    "SR386_40X_HE_T017_01", "SR386_40X_HE_T022_01",  # MSI-H (Gold for demo)
    "SR386_40X_HE_T001_01", "SR386_40X_HE_T003_01",  # KRAS mut stage 1
    "SR386_40X_HE_T010_01", "SR386_40X_HE_T019_01",  # KRAS G12C (Targetable)
    "SR386_40X_HE_T007_01", "SR386_40X_HE_T027_01",  # pT4 (Aggressive invasion)
    "SR386_40X_HE_T020_01",                          # stage 3 N1
    "SR386_40X_HE_T006_01",                          # WT baseline (Clean comparison)
]

demo_cases = [c for c in data if c["case_id"] in demo_ids]

# Save the demo cases to a separate file
with open("demo_cases.json", "w") as f:
    json.dump(demo_cases, f, indent=2)

print(f"\nDemo set: {len(demo_cases)} cases saved to demo_cases.json")
print("Phase 2 Complete! ✅")