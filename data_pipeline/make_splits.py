import json
import random

# Load the labelled cases we just generated
labelled = json.load(open("labelled_cases.json"))

# Shuffle with a fixed seed for reproducibility 
random.seed(42)
random.shuffle(labelled)

# Split: 300 dev, 50 val, 57 test
splits = {
    "dev":  labelled[:300],
    "val":  labelled[300:350],
    "test": labelled[350:]
}

for split, cases in splits.items():
    json.dump(cases, open(f"split_{split}.json", "w"), indent=2)

print(f"Splits created successfully!")
print(f"Dev: {len(splits['dev'])} cases")
print(f"Val: {len(splits['val'])} cases")
print(f"Test: {len(splits['test'])} cases")