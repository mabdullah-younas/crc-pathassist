import json

data = json.load(open("dataset.json"))

def survival_label(c):
    s = str(c.get("survival_status", ""))
    if "alive" in s.lower(): return "good"
    try:
        days = float(s.replace("days:",""))
        return "good" if days > 1825 else "poor"
    except:
        return None

good, poor, unknown = 0, 0, 0
labelled = []

for c in data:
    label = survival_label(c)
    if label == "good":   good += 1
    elif label == "poor": poor += 1
    else:                 unknown += 1
    
    if label:
        c["survival_label"] = label
        labelled.append(c)

print(f"Good prognosis: {good}")
print(f"Poor prognosis: {poor}")
print(f"Unknown/excluded: {unknown}")
print(f"Usable cases: {len(labelled)}")
print(f"Class balance: {good/(good+poor)*100:.1f}% good")

json.dump(labelled, open("labelled_cases.json","w"), indent=2)