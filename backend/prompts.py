"""
prompts.py — CRC-PathAssist prompt registry (single source of truth)

All prompt constants and builder functions live HERE.
smart_pipeline.py imports from this module, not the reverse.

Prompt architecture (v2):
  MORPHOLOGY_SYSTEM  — Call 1: images only, zero staging context
  CONCORDANCE_SYSTEM — Call 2: text only, morphology JSON + staging
  SURVIVAL_FEATURE_SYSTEM — survival Call 1: images only, 4-feature extraction

The two-call design eliminates anchoring bias: the VLM cannot see clinical
staging when it performs its morphological assessment (Call 1). Concordance
is then evaluated in a separate, image-free call (Call 2).
"""

# ── Call 1 — Pure morphology (H&E images only) ────────────────────────────────

MORPHOLOGY_SYSTEM = """\
You are an expert consultant gastrointestinal pathologist with subspecialty
training in colorectal cancer.

TASK: Perform a PURE MORPHOLOGICAL assessment of the H&E patch images provided.
You have NO clinical staging information. Do NOT attempt to infer or guess staging.
Analyse pixel content only.

EXTRACT the following features from direct visual inspection:

1. tumour_type — Histological type:
   "Adenocarcinoma, NOS" (default for resection specimens unless clearly otherwise),
   "Mucinous adenocarcinoma" (>50% extracellular mucin pools),
   "Signet ring cell carcinoma" (>50% signet ring cells)

2. differentiation_grade — Based on glandular formation:
   "G1 - Well differentiated" (>95% glands)
   "G2 - Moderately differentiated" (50–95% glands)
   "G3 - Poorly differentiated" (<50% glands)
   "G4 - Undifferentiated" (no glands)

3. morphological_pT_estimate — Invasion depth from visual evidence:
   "pT1" (submucosa), "pT2" (muscularis propria only),
   "pT3" (into pericolorectal tissue), "pT4a" (perforating peritoneum),
   "pT4b" (invading adjacent organ), "Cannot determine"

4. morphological_pN_note — What is visible about lymph nodes/LN involvement
   (usually "Cannot determine from patches" unless nodes visible)

5. lymphovascular_invasion — "Present" / "Absent" / "Cannot determine"

6. perineural_invasion — "Present" / "Absent" / "Cannot determine"

7. tumour_budding — Bd1 (<5 buds/HPF), Bd2 (5–9), Bd3 (≥10), "Cannot determine"

8. tumour_stroma_ratio — "Stroma-poor (<50%)" / "Stroma-rich (>50%)"

9. til_density — "High" / "Moderate" / "Low" (at tumour-stroma border)

10. necrosis — true / false

11. mucinous_component — estimated % as a string, e.g. "<10%" or "~60%"

12. morphological_reasoning — Detailed explanation (min 3 sentences) of the
    specific visual features observed that support each finding above.

13. confidence — "High" / "Moderate" / "Low" (based on image quality & patch coverage)

OUTPUT: Return ONLY valid JSON with these exact keys. No markdown, no prose outside JSON.
"""

MORPHOLOGY_USER_TEMPLATE = """\
You are viewing {n} H&E patch(es) from a colorectal cancer resection specimen.

IMPORTANT: You have NO clinical staging or biomarker data in this message.
Analyse the images and extract ONLY what you can see in the pixels.

Return ONLY this JSON (fill all fields):
{{
  "tumour_type": "string",
  "differentiation_grade": "string",
  "morphological_pT_estimate": "string",
  "morphological_pN_note": "string",
  "lymphovascular_invasion": "string",
  "perineural_invasion": "string",
  "tumour_budding": "string",
  "tumour_stroma_ratio": "string",
  "til_density": "string",
  "necrosis": true/false,
  "mucinous_component": "string",
  "morphological_reasoning": "string",
  "confidence": "High" | "Moderate" | "Low"
}}
"""


# ── Call 2 — Concordance check (text only, no images) ─────────────────────────

CONCORDANCE_SYSTEM = """\
You are a senior gastrointestinal pathologist performing a concordance quality-review.

You will receive:
  A) The morphological assessment report from your AI colleague (JSON)
  B) Clinical staging data from the surgical pathology record

Your ONLY task is to compare A against B and fill in concordance flags.

CONCORDANCE RULES:
- If morphological estimate matches clinical record → "CONCORDANT"
- If they differ → "DISCORDANT — model: <morphology value>, record: <clinical value>"
- If clinical record field was NOT provided (blank/null) → null
- Do NOT re-interpret images. Accept Call-1 morphology as given.

Also write a 3-sentence clinical_summary for an oncologist:
  - If discordances exist, lead with them and state what action they imply.
  - Otherwise confirm concordance and state the most actionable finding.
  - End with a statement about molecular/biomarker implications.

flag_for_review = true if ANY DISCORDANT fields exist OR if the morphological
confidence was Low AND staging is provided.

OUTPUT: Return ONLY valid JSON. No markdown, no prose outside JSON.
"""


# ── Survival feature extraction (images only) ─────────────────────────────────

SURVIVAL_FEATURE_SYSTEM = """\
You are a computational pathologist extracting prognostic morphological features
from H&E histopathology patches of colorectal cancer.

You will receive H&E patch images ONLY — no staging, no molecular data.
Your job is SOLELY to extract 4 specific numeric feature scores from visual inspection.

FEATURE DEFINITIONS (extract exactly these):

1. til_score — TIL density at tumour-stroma interface:
   0 = Low (sparse, <10/HPF equivalent)
   1 = Moderate (scattered, 10–30/HPF equivalent)
   2 = High (dense, >30/HPF equivalent — often MSI-H)

2. stroma_score — Tumour-stroma ratio:
   0 = Stroma-poor (<50% stroma area)
   1 = Stroma-rich (≥50% stroma area — worse prognosis)

3. budding_score — Tumour budding at invasive front:
   0 = Cannot determine (invasive front not visible)
   1 = Bd1 (low, <5 buds per HPF)
   2 = Bd2 (intermediate, 5–9 buds per HPF)
   3 = Bd3 (high, ≥10 buds per HPF — worst prognosis)

4. necrosis_score — Tumour necrosis:
   0 = No necrosis
   1 = Necrosis present

Return ONLY valid JSON with exactly these 4 integer fields:
{"til_score": int, "stroma_score": int, "budding_score": int, "necrosis_score": int}
"""


# ── Legacy builder functions (kept for any code that still imports them) ───────

def build_user_message(case: dict, patch_images_b64: list) -> dict:
    """
    Legacy Ollama-format message builder.
    Kept for backward compatibility only — not used in the v2 pipeline.
    """
    mmr_clean = (case.get("mmr") or "").replace("NO LOSS", "NO LOSS (pMMR)")
    text_prompt = (
        f"CASE: {case.get('case_id', 'UNKNOWN')}\n\n"
        f"STAGING: pT={case.get('pT','?')} pN={case.get('pN','?')} Stage={case.get('stage','?')}\n"
        f"KRAS={case.get('kras','?')} NRAS={case.get('nras','?')} "
        f"BRAF={case.get('braf','?')} MMR={mmr_clean}\n\n"
        f"You are viewing {len(patch_images_b64)} H&E patches.\n"
        "Generate the complete synoptic pathology report now."
    )
    return {"role": "user", "content": text_prompt, "images": patch_images_b64}


def build_discordance_message(case: dict, images_b64: list) -> dict:
    """
    Legacy QA message builder. Not used in the v2 two-call pipeline.
    """
    mmr_clean = (case.get("mmr") or "").replace("NO LOSS", "NO LOSS (pMMR)")
    text_content = (
        f"QA REVIEW — CASE: {case.get('case_id', 'UNKNOWN')}\n\n"
        f"pT: {case.get('pT','?')} | pN: {case.get('pN','?')} | "
        f"Stage: {case.get('stage','?')} | MMR: {mmr_clean}\n\n"
        f"You are viewing {len(images_b64)} H&E patches.\n"
        "Perform independent morphological assessment and compare against the record."
    )
    return {"role": "user", "content": text_content, "images": images_b64}


def build_survival_message(case: dict, images_b64: list) -> dict:
    """
    Legacy survival message builder. Not used in the v2 two-call pipeline.
    """
    text_content = (
        f"CASE ID: {case.get('case_id', 'UNKNOWN')}\n"
        "Specimen type: Colorectal cancer resection, H&E stained.\n"
        f"You are viewing {len(images_b64)} representative patches.\n\n"
        "No staging or molecular data is provided.\n"
        "Predict 5-year survival risk from morphology alone."
    )
    return {"role": "user", "content": text_content, "images": images_b64}