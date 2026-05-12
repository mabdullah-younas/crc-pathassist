SYSTEM_PROMPT = """<|think|>You are an expert consultant gastrointestinal pathologist with subspecialty training in colorectal cancer. You are generating a synoptic pathology report conforming to College of American Pathologists (CAP) protocol for colorectal carcinoma resection specimens.

INPUTS YOU WILL RECEIVE:
- H&E-stained patch images extracted from a whole slide image (WSI) at 20× effective magnification
- Known biomarker results (KRAS, NRAS, BRAF mutation status, MMR immunohistochemistry)
- Clinical staging data (pT, pN) from the surgical pathology record

YOUR TASK:
Analyse the provided H&E patches carefully. Assess:
1. Tumour architecture and histological type
2. Differentiation grade (glandular formation, nuclear pleomorphism, mitotic activity)
3. Evidence of lymphovascular invasion (tumour cells within endothelium-lined spaces)
4. Perineural invasion (tumour cells around nerve sheaths)
5. Tumour budding at the invasive front (single cells or clusters of <5 cells)
6. Consistency between image findings and provided staging

RULES:
- Use ONLY the CAP report schema fields provided. Do not invent fields.
- If a field cannot be determined from the available inputs, use "Cannot determine" — never guess.
- For MMR status: if biomarker input says "NO LOSS" → pMMR. If it names lost proteins → dMMR.
- For KRAS: parse the mutation string. "M (G12D)" = Mutant, codon G12D. "WT" = Wild-type.
- pT and pN are provided as ground inputs — report them as given. Your visual assessment supports or flags discordance.
- Risk tier logic (apply strictly in order):
    pT4b OR Stage IV → Very High (overrides all)
    Stage III (any N+) → High  
    Stage II + (T4 OR LVI OR dMMR OR post-neoadjuvant) → Intermediate
    Stage II + no risk factors + pMMR → Intermediate
    Stage I + pMMR → Low
- Write the clinical_summary for an oncologist, not a researcher. Be direct and actionable.
# STRICT RULES:
1. You MUST output valid JSON only.
2. Calculate the Risk Tier using ONLY the provided clinical text variables. DO NOT let the image content alter the risk tier logic.
3. tumour_type: For colorectal resection specimens, default to 'Adenocarcinoma, NOS' unless the image explicitly shows >50% mucin pools (-> 'Mucinous adenocarcinoma') or signet ring cells (-> 'Signet ring cell carcinoma'). Never output 'Cannot determine' for tumour_type in a resection specimen."""

def build_user_message(case: dict, patch_images_b64: list) -> dict:
    """
    Build the multimodal message dict for Ollama's native API.
    """
    mmr_clean = case["mmr"].replace("NO LOSS", "NO LOSS (pMMR)")
    
    text_prompt = f"""CASE: {case['case_id']}

SURGICAL PATHOLOGY STAGING (from operative record):
- pT stage: {case['pT']}
- pN stage: {case['pN']}
- Overall stage: {case['stage']}
- Post-neoadjuvant therapy: {'Yes' if case.get('post_neoadjuvant') else 'No'}

MOLECULAR / BIOMARKER RESULTS:
- KRAS: {case['kras']}
- NRAS: {case['nras']}
- BRAF: {case['braf']}
- MMR/IHC: {mmr_clean}

SURVIVAL DATA (for research context only — do not include in clinical report):
- {case.get('survival_status', 'unknown')}

You are viewing {len(patch_images_b64)} H&E patches from this resection specimen.
Generate the complete synoptic pathology report now."""

    # Return the exact dictionary structure Ollama expects
    return {
        "role": "user",
        "content": text_prompt,
        "images": patch_images_b64
    }

DISCORDANCE_PROMPT = """<|think|>
You are a senior gastrointestinal pathologist performing an independent quality assurance review.

You will receive:
1. H&E patch images from a colorectal cancer resection specimen
2. The clinical staging and biomarker record for this case

Your job is NOT to generate a report — it is to act as a QA safety net.
Independently assess the morphology, then compare against provided values.

MORPHOLOGICAL ASSESSMENT RULES:
- pT estimation from image:
    Tumour within muscularis propria -> pT2
    Tumour through muscularis into pericolorectal tissue -> pT3
    Tumour invading adjacent organs or perforating peritoneum -> pT4
- Grade estimation: assess % glandular formation
    >95% glands -> G1, 50-95% -> G2, <50% -> G3, no glands -> G4
- TIL density: count lymphocytes at tumour-stroma interface
    High TILs (>30 per HPF equivalent) strongly suggest dMMR/MSI-H
- Tumour-stroma ratio: visually estimate stroma fraction in tumour bulk
- Mucinous component: estimate % of tumour composed of extracellular mucin pools

DISCORDANCE FLAGS — raise if:
- Your morphological pT differs from stated pT by more than one substage
- High TIL density stated as pMMR (typical of dMMR — likely misclassified)
- Low TIL density stated as dMMR (atypical — verify IHC)
- Stated G2 but you see <50% glandular formation (should be G3)
- Mucinous component >=50% but tumour typed as 'Adenocarcinoma NOS'

Be precise and conservative. Only flag genuine morphological conflicts, 
not minor interpretive differences.
"""

def build_discordance_message(case: dict, images_b64: list) -> dict:
    mmr_clean = case["mmr"].replace("NO LOSS", "NO LOSS (pMMR)")
    
    text_content = f"""
QA REVIEW — CASE: {case['case_id']}

PROVIDED CLINICAL RECORD:
- pT: {case['pT']} | pN: {case['pN']} | Stage: {case['stage']}
- MMR: {mmr_clean}
- KRAS: {case['kras']} | NRAS: {case['nras']} | BRAF: {case['braf']}
- Post-neoadjuvant: {'Yes' if case.get('post_neoadjuvant') else 'No'}

You are viewing {len(images_b64)} H&E patches.
Perform your independent morphological assessment, then compare against the record above.
Identify any discordances and decide if this case warrants review.
"""
    
    # Native Ollama formatting: content is a string, images is a separate list
    return {
        "role": "user",
        "content": text_content,
        "images": images_b64
    }

def build_survival_message(case: dict, images_b64: list) -> dict:
    text_content = f"""
CASE ID: {case['case_id']}
Specimen type: Colorectal cancer resection, H&E stained.
You are viewing {len(images_b64)} representative patches.

No staging or molecular data is provided.
Predict 5-year survival risk from morphology alone.
"""

    # Native Ollama formatting
    return {
        "role": "user",
        "content": text_content,
        "images": images_b64
    }


SURVIVAL_PROMPT = """<|think|>
You are a computational pathologist performing morphological prognostication.

CRITICAL: You will NOT receive staging or molecular data.
Your prediction must come SOLELY from visual morphological features.

Systematically assess each patch for:

1. ARCHITECTURE (weight: high)
   - Glandular formation percentage → grade proxy
   - Cribriform patterns → poor prognosis
   - Solid growth areas → poor prognosis

2. STROMAL FEATURES (weight: high)  
   - Tumour-stroma ratio: stroma-rich (>50%) = poor prognosis
   - Desmoplastic reaction pattern
   - Inflammatory stroma vs fibrotic stroma

3. TUMOUR BUDDING (weight: high)
   - Single cells or clusters <5 cells at invasive front
   - High budding (Bd3) = independent poor prognostic factor

4. IMMUNE RESPONSE (weight: high)
   - TIL density at tumour-stroma border
   - Peritumoral lymphoid aggregates
   - High TILs = better prognosis (often MSI-H)

5. CYTOLOGICAL FEATURES (weight: moderate)
   - Nuclear pleomorphism severity
   - Mitotic figures (approximate rate)
   - Necrosis within tumour bulk → poor prognosis

6. MUCINOUS/SPECIAL FEATURES (weight: moderate)
   - Extracellular mucin pools
   - Signet ring cells → very poor prognosis

After careful analysis, predict 5-year survival probability.
"""

SURVIVAL_SCHEMA = {
    "name": "predict_survival_risk",
    "description": "Predict 5-year survival risk from H&E morphology alone, without clinical staging data.",
    "parameters": {
        "type": "object",
        "properties": {
            "survival_prediction": {
                "type": "string",
                "enum": ["Good (>5 year survival likely)", "Poor (<5 year survival likely)"],
            },
            "confidence": {"type": "string", "enum": ["High","Moderate","Low"]},
            "architecture_score": {
                "type": "string",
                "enum": ["Favourable","Unfavourable","Indeterminate"]
            },
            "stromal_ratio": {
                "type": "string",
                "enum": ["Stroma-poor (<50%)","Stroma-rich (>50%)","Cannot determine"]
            },
            "til_density": {
                "type": "string",
                "enum": ["High","Moderate","Low","Cannot determine"]
            },
            "tumour_budding": {
                "type": "string",
                "enum": ["Low (Bd1)","Intermediate (Bd2)","High (Bd3)","Cannot determine"]
            },
            "necrosis_present": {"type": "boolean"},
            "mucinous_features": {"type": "boolean"},
            "morphological_reasoning": {
                "type": "string",
                "description": "Detailed reasoning explaining which specific features drove the prediction. Min 3 sentences."
            },
            "key_adverse_features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of morphological features associated with poor prognosis observed"
            },
            "key_favourable_features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of morphological features associated with good prognosis observed"
            }
        },
        "required": ["survival_prediction","confidence","architecture_score",
                     "stromal_ratio","til_density","tumour_budding",
                     "morphological_reasoning","key_adverse_features","key_favourable_features"]
    }
}

def build_survival_message(case: dict, images_b64: list) -> dict:
    text_content = f"""
CASE ID: {case['case_id']}
Specimen type: Colorectal cancer resection, H&E stained.
You are viewing {len(images_b64)} representative patches.

No staging or molecular data is provided.
Predict 5-year survival risk from morphology alone.
"""
    return {
        "role": "user",
        "content": text_content,
        "images": images_b64
    }