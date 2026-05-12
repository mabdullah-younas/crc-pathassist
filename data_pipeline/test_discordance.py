import json
from pipeline import run_discordance

# Load your demo cases
data = json.load(open("demo_cases.json"))
case = next(c for c in data if c["case_id"] == "SR386_40X_HE_T017_01" or "T017" in c["case_id"])

print(f"Testing Discordance QA on Case: {case['case_id']}")
print("Running inference... (Ensure Ollama is running)")

# Run the new discordance function
result = run_discordance(case, use_patches=2)

# Print the structured JSON output
print(json.dumps(result['qa_report'], indent=2))