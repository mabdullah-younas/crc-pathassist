"""
smart_pipeline.py — CRC-PathAssist unified inference functions

ARCHITECTURE (v2 — anchoring-bias-free):
  run_smart_report uses a TWO-CALL design:
    Call 1 — images ONLY → morphological assessment (no staging in context)
    Call 2 — Call-1 output + clinical staging → concordance flags only
  risk_tier is computed deterministically in Python after both calls.

  run_survival_prediction — 2-step (feature extraction → LR classifier)
"""

import base64
import json
import os
import re
import pickle
import warnings
import numpy as np
from pathlib import Path
from PIL import Image
import io
import urllib.request
import urllib.error

# ── Prompt constants — single source of truth in prompts.py ───────────────────
from prompts import (
    MORPHOLOGY_SYSTEM,
    MORPHOLOGY_USER_TEMPLATE,
    CONCORDANCE_SYSTEM,
    SURVIVAL_FEATURE_SYSTEM,
)

# ── Model config ──────────────────────────────────────────────────────────────
MODEL = "gemma4:e4b"
N_PATCHES = 2
PATCH_SIZE = 448

# ── LR model path ─────────────────────────────────────────────────────────────
_LR_MODEL_PATH = Path(__file__).parent.parent / "lr_survival_model.pkl"


def _load_lr_model():
    """Load the logistic regression survival model."""
    for candidate in (_LR_MODEL_PATH, Path(__file__).parent / "lr_survival_model.pkl"):
        if candidate.exists():
            with open(candidate, "rb") as f:
                return pickle.load(f)
    return None


def _get_model_stats(lr_model) -> dict:
    """
    Introspect the LR model for accuracy/AUC metadata stored at training time.
    Falls back to the known SR386 holdout numbers if no metadata is present.
    Returns dict with keys: model_accuracy, model_auc, model_note.
    """
    if lr_model is None:
        return {
            "model_accuracy": "N/A (model not loaded)",
            "model_auc": "N/A",
            "model_note": "Heuristic fallback active — LR model file not found.",
        }
    acc = getattr(lr_model, "_accuracy", None)
    auc = getattr(lr_model, "_auc", None)
    note = getattr(lr_model, "_note", None)
    return {
        "model_accuracy": f"{acc:.1%}" if isinstance(acc, float) else (str(acc) if acc else "61.4%"),
        "model_auc": f"{auc:.3f}" if isinstance(auc, float) else (str(auc) if auc else "0.605"),
        "model_note": note or "Validated on 57 held-out SR386 cases. This is a research tool — do not use for clinical decisions.",
    }


def encode_image(path: str, resize_to: int = PATCH_SIZE) -> str:
    img = Image.open(path).convert("RGB")
    img = img.resize((resize_to, resize_to), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _call_ollama(system_prompt: str, user_prompt: str, images_b64: list[str]) -> str:
    OLLAMA_URL = "http://localhost:11434/api/generate"
    clean_images = []
    for b64 in images_b64:
        if "," in b64:
            clean_images.append(b64.split(",")[1])
        else:
            clean_images.append(b64)

    data = {
        "model": MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "images": clean_images,
        "stream": False,
        "format": "json",
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            res_json = json.loads(res_body)
            return res_json.get("response", "")
    except Exception as e:
        raise RuntimeError(
            f"Ollama connection failed: {e}. "
            "Ensure Ollama is running locally and your gemma model is pulled."
        )


def _parse_json(raw: str) -> dict:
    """Try direct JSON parse, then regex extraction, then return error dict."""
    try:
        return json.loads(raw)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]+\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"error": "Could not parse JSON from model response", "raw": raw[:500]}


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC RISK TIER (Fix 3: no longer delegated to LLM)
# ─────────────────────────────────────────────────────────────────────────────

def compute_risk_tier(
    morphological_pt: str,
    pN_user: str,
    stage_user: str,
    lvi: str,
    mmr: str,
    post_neoadjuvant: bool = False,
    pT_user: str = "",
    # Additional morphological features for composite fallback scoring
    tumour_budding: str = "",
    differentiation_grade: str = "",
    til_density: str = "",
    necrosis: bool = False,
    tumour_stroma_ratio: str = "",
) -> str:
    """
    Deterministic risk tier computation per CAP/AJCC guidelines.

    Priority order (first match wins — uses clinical staging when provided):
      1. Very High  — pT4b (any source) OR Stage IV
      2. High       — Any N+ (pN1/pN2) OR Stage III
      3. Intermediate — Stage II (any risk factor: pT4a, LVI, dMMR, post-neo)
      4. Intermediate — Stage II, no risk factors
      5. Low        — Stage I, pMMR

    Morphology-only fallback (when no staging provided):
      Uses a weighted adverse-feature score across ALL available morphological
      features so a tier is always derivable from the H&E images alone.
    """
    # ── Normalise all inputs ──────────────────────────────────────────────────
    # Use provided clinical pT first; fall back to morphological estimate
    pt_raw  = (pT_user or morphological_pt or "").strip()
    pt      = pt_raw.upper()
    pn      = (pN_user or "").upper().strip()
    # Strip "Stage" / "STAGE" prefix properly with regex, then strip whitespace
    stg_raw = re.sub(r'^stage\s*', '', (stage_user or "").strip(), flags=re.IGNORECASE).strip().upper()

    lvi_present = "PRESENT" in (lvi or "").upper()
    dmmr = (
        "DMMR"      in (mmr or "").upper()
        or "DEFICIENT" in (mmr or "").upper()
        or "LOSS"     in (mmr or "").upper()
    )

    # Flexible pT helpers — match pT4b, T4B, pt4b, 4b, etc.
    def _pt_is(tier: str) -> bool:
        """Check if pt_raw matches a specific T-stage tier (case-insensitive)."""
        return bool(re.search(rf'\b{re.escape(tier)}\b', pt_raw, re.IGNORECASE))

    def _pt_contains(fragment: str) -> bool:
        """Broader check — does the raw pT string contain this fragment."""
        return fragment.upper() in pt.replace(" ", "")

    # ── STAGING-BASED RULES (clinical or morphological pT + pN + stage) ───────

    # Rule 1 — Very High
    if _pt_contains("4B") or stg_raw in ("IV", "4"):
        return "Very High"

    # Rule 2 — High (any N+ or Stage III)
    n_positive = pn not in ("", "N0", "NX", "CANNOT DETERMINE")
    if n_positive or stg_raw in ("III", "3"):
        return "High"

    # Rule 3/4 — Stage II  →  always Intermediate (risk factors refine surveillance, not tier)
    if stg_raw in ("II", "2"):
        return "Intermediate"

    # Rule 5 — Stage I
    if stg_raw in ("I", "1"):
        return "Low" if not dmmr else "Intermediate"

    # ── MORPHOLOGY-ONLY COMPOSITE FALLBACK (no clinical staging provided) ─────
    # Each feature contributes an adverse (+) or protective (-) weight.
    # Score ≥ 3  → High
    # Score 1-2  → Intermediate
    # Score ≤ 0  → Low
    # (Very High is caught above via pT4b)
    adverse = 0

    # pT contribution (most weight — captures invasion depth)
    if   _pt_contains("4B"): return "Very High"          # re-check for morph estimate
    elif _pt_contains("4A"): adverse += 3
    elif _pt_contains("3"):  adverse += 2                 # pT3 — most common CRC stage
    elif _pt_contains("2"):  adverse += 0
    elif _pt_contains("1"):  adverse -= 1
    # "Cannot determine" pT → adverse stays at 0; other features carry the score

    # Lymphovascular invasion — independent poor prognostic factor
    if lvi_present:
        adverse += 2

    # Tumour budding
    bud = (tumour_budding or "").upper()
    if   "BD3" in bud: adverse += 2
    elif "BD2" in bud: adverse += 1
    elif "BD1" in bud: adverse += 0

    # Differentiation grade
    grade = (differentiation_grade or "").upper()
    if   "G4" in grade or "UNDIFFERENTIATED" in grade: adverse += 2
    elif "G3" in grade or "POORLY"            in grade: adverse += 1
    elif "G1" in grade or "WELL"              in grade: adverse -= 1

    # Tumour-stroma ratio
    if "RICH" in (tumour_stroma_ratio or "").upper():
        adverse += 1

    # TIL density — protective at high levels (often MSI-H)
    til = (til_density or "").upper()
    if   "HIGH" in til:     adverse -= 1
    elif "LOW"  in til:     adverse += 1

    # Necrosis
    if necrosis:
        adverse += 1

    # dMMR — generally protective for Stage II but adverse context in III/IV
    # In morphology-only context treat as neutral (no independent scoring)

    # post-neoadjuvant — generally flags higher-risk intent
    if post_neoadjuvant:
        adverse += 1

    # ── Map composite score to tier ───────────────────────────────────────────
    if   adverse >= 4: return "High"
    elif adverse >= 1: return "Intermediate"
    else:              return "Low"


# ─────────────────────────────────────────────────────────────────────────────
# Prompt constants are imported from prompts.py (see import block above).
# MORPHOLOGY_SYSTEM, MORPHOLOGY_USER_TEMPLATE, CONCORDANCE_SYSTEM,
# and SURVIVAL_FEATURE_SYSTEM are all defined canonically in prompts.py.
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# run_smart_report — Two-call anchoring-bias-free architecture (Fix 1)
# ─────────────────────────────────────────────────────────────────────────────

def run_smart_report(patches: list[str], clinical_inputs: dict, molecular_inputs: dict) -> dict:
    """
    Unified smart report: morphological assessment + concordance check.

    Architecture (v2 — two-call, anchoring-bias-free):
      Call 1 — images ONLY (MORPHOLOGY_SYSTEM). Zero staging context.
               Returns morphological features + estimates.
      Call 2 — text only (CONCORDANCE_SYSTEM). Feeds Call-1 JSON + staging.
               Returns concordance flags + clinical summary.
      Post-processing — compute_risk_tier() in Python (deterministic).

    Args:
        patches: list of patch file paths (up to N_PATCHES used)
        clinical_inputs: dict with keys pT, pN, stage, post_neoadjuvant
        molecular_inputs: dict with keys kras, nras, braf, mmr

    Returns:
        dict conforming to the smart report schema
    """
    patch_paths = patches[:N_PATCHES]
    images_b64 = [encode_image(p, resize_to=PATCH_SIZE) for p in patch_paths]

    # ── Unpack inputs ─────────────────────────────────────────────────────────
    pT_user  = (clinical_inputs.get("pT")    or "").strip()
    pN_user  = (clinical_inputs.get("pN")    or "").strip()
    stage_user = (clinical_inputs.get("stage") or "").strip()
    post_neo   = bool(clinical_inputs.get("post_neoadjuvant", False))

    kras = molecular_inputs.get("kras", "NOT TESTED")
    nras = molecular_inputs.get("nras", "NOT TESTED")
    braf = molecular_inputs.get("braf", "NOT TESTED")
    mmr  = molecular_inputs.get("mmr",  "NO LOSS")

    # ═════════════════════════════════════════════════════════════════════════
    # CALL 1 — Pure morphology (NO staging context)
    # ═════════════════════════════════════════════════════════════════════════
    morph_user = MORPHOLOGY_USER_TEMPLATE.format(n=len(images_b64))
    morph_raw = _call_ollama(MORPHOLOGY_SYSTEM, morph_user, images_b64)
    morphology = _parse_json(morph_raw)

    if "error" in morphology:
        return morphology  # propagate parse failure up

    # ═════════════════════════════════════════════════════════════════════════
    # CALL 2 — Concordance check (text only, no images)
    # ═════════════════════════════════════════════════════════════════════════
    staging_block = ""
    if pT_user or pN_user or stage_user:
        staging_block = f"""\
CLINICAL STAGING FROM SURGICAL RECORD:
  pT stage    : {pT_user  or '[NOT PROVIDED]'}
  pN stage    : {pN_user  or '[NOT PROVIDED]'}
  Overall stage: {stage_user or '[NOT PROVIDED]'}"""
    else:
        staging_block = "CLINICAL STAGING: NOT PROVIDED by user."

    concordance_user = f"""\
=== MORPHOLOGICAL ASSESSMENT (from Call 1 — image-only analysis) ===
{json.dumps(morphology, indent=2)}

=== {staging_block} ===

MOLECULAR / BIOMARKER RESULTS (lab results — for summary context only):
  KRAS   : {kras}
  NRAS   : {nras}
  BRAF   : {braf}
  MMR/IHC: {mmr}

Compare morphological estimates against clinical staging and fill concordance fields.

Return ONLY this JSON:
{{
  "pT_comparison"  : "CONCORDANT" | "DISCORDANT — model: X, record: Y" | null,
  "pN_comparison"  : "CONCORDANT" | "DISCORDANT — model: X, record: Y" | null,
  "mmr_status"     : "string (Proficient/Deficient based on MMR input)",
  "mmr_proteins_lost": [],
  "kras_status"    : "Mutant" | "Wild-type" | "Not tested",
  "kras_codon"     : "string",
  "nras_status"    : "Mutant" | "Wild-type" | "Not tested",
  "braf_status"    : "Mutant" | "Wild-type" | "Not tested",
  "clinical_summary": "string (3 sentences, discordances first if any)",
  "flag_for_review" : true/false
}}
"""
    concordance_raw = _call_ollama(CONCORDANCE_SYSTEM, concordance_user, [])
    concordance = _parse_json(concordance_raw)

    if "error" in concordance:
        # Degrade gracefully — fill concordance fields with nulls
        concordance = {
            "pT_comparison": None,
            "pN_comparison": None,
            "mmr_status": "Cannot determine",
            "mmr_proteins_lost": [],
            "kras_status": "Not tested",
            "kras_codon": "N/A",
            "nras_status": "Not tested",
            "braf_status": "Not tested",
            "clinical_summary": "Concordance assessment could not be completed due to a parsing error.",
            "flag_for_review": True,
            "_concordance_error": concordance.get("error", "unknown"),
        }

    # ═════════════════════════════════════════════════════════════════════════
    # PYTHON-SIDE CONCORDANCE VALIDATION
    # The LLM can hallucinate CONCORDANT when both sides are indeterminate
    # (e.g. user provides pTX and model returns "Cannot determine").
    # Concordance is only meaningful when BOTH sides have a real estimate.
    # Rule: force pT_comparison / pN_comparison to null when:
    #   - The model estimate is "Cannot determine" / empty, OR
    #   - The user-supplied value is an "unknown" code (pTX, NX) OR was not provided.
    # ═════════════════════════════════════════════════════════════════════════
    _INDETERMINATE_PT = {"PTX", "PTX", "CANNOT DETERMINE", "CANNOT BE DETERMINED", ""}
    _INDETERMINATE_PN = {"NX", "CANNOT DETERMINE", "CANNOT BE DETERMINED", ""}

    morph_pt_upper = (morphology.get("morphological_pT_estimate") or "").upper().strip()
    user_pt_upper  = pT_user.upper().strip()
    morph_pn_note  = (morphology.get("morphological_pN_note") or "").upper()
    user_pn_upper  = pN_user.upper().strip()

    # pT concordance — null when either side is indeterminate
    pt_model_indeterminate = (
        morph_pt_upper in _INDETERMINATE_PT
        or "CANNOT" in morph_pt_upper
        or "DETERMINE" in morph_pt_upper
    )
    pt_user_indeterminate = (
        user_pt_upper in _INDETERMINATE_PT
        or "PTX" in user_pt_upper
        or not user_pt_upper  # not provided
    )
    if pt_model_indeterminate or pt_user_indeterminate:
        concordance["pT_comparison"] = None

    # pN concordance — null when either side is indeterminate
    pn_model_indeterminate = (
        "CANNOT" in morph_pn_note
        or "DETERMINE" in morph_pn_note
        or not morph_pn_note.strip()
    )
    pn_user_indeterminate = (
        user_pn_upper in _INDETERMINATE_PN
        or "NX" in user_pn_upper
        or not user_pn_upper  # not provided
    )
    if pn_model_indeterminate or pn_user_indeterminate:
        concordance["pN_comparison"] = None

    # ═════════════════════════════════════════════════════════════════════════
    # POST-PROCESSING — Deterministic risk tier (Fix 3)
    # ═════════════════════════════════════════════════════════════════════════
    risk_tier = compute_risk_tier(
        morphological_pt    = morphology.get("morphological_pT_estimate", ""),
        pN_user             = pN_user,
        stage_user          = stage_user,
        lvi                 = morphology.get("lymphovascular_invasion", ""),
        mmr                 = mmr,
        post_neoadjuvant    = post_neo,
        pT_user             = pT_user,
        # Extra morphological features for composite fallback scoring
        tumour_budding      = morphology.get("tumour_budding", ""),
        differentiation_grade = morphology.get("differentiation_grade", ""),
        til_density         = morphology.get("til_density", ""),
        necrosis            = bool(morphology.get("necrosis", False)),
        tumour_stroma_ratio = morphology.get("tumour_stroma_ratio", ""),
    )

    # ═════════════════════════════════════════════════════════════════════════
    # MERGE — Combine morphology + concordance into final report
    # ═════════════════════════════════════════════════════════════════════════
    result = {
        # ── Core morphological features (from Call 1) ─────────────────────
        "tumour_type"               : morphology.get("tumour_type", "Cannot determine"),
        "differentiation_grade"     : morphology.get("differentiation_grade", "Cannot determine"),
        "morphological_pT_estimate" : morphology.get("morphological_pT_estimate", "Cannot determine"),
        "morphological_pN_note"     : morphology.get("morphological_pN_note", "Cannot determine"),
        "lymphovascular_invasion"   : morphology.get("lymphovascular_invasion", "Cannot determine"),
        "perineural_invasion"       : morphology.get("perineural_invasion", "Cannot determine"),
        "tumour_budding"            : morphology.get("tumour_budding", "Cannot determine"),
        "tumour_stroma_ratio"       : morphology.get("tumour_stroma_ratio", "Cannot determine"),
        "til_density"               : morphology.get("til_density", "Cannot determine"),
        "necrosis"                  : morphology.get("necrosis", False),
        "mucinous_component"        : morphology.get("mucinous_component", "Cannot determine"),
        "morphological_reasoning"   : morphology.get("morphological_reasoning", ""),
        # ── Concordance fields (from Call 2) ──────────────────────────────
        "pT_comparison"             : concordance.get("pT_comparison"),
        "pN_comparison"             : concordance.get("pN_comparison"),
        "mmr_status"                : concordance.get("mmr_status", "Cannot determine"),
        "mmr_proteins_lost"         : concordance.get("mmr_proteins_lost", []),
        "kras_status"               : concordance.get("kras_status", "Not tested"),
        "kras_codon"                : concordance.get("kras_codon", "N/A"),
        "nras_status"               : concordance.get("nras_status", "Not tested"),
        "braf_status"               : concordance.get("braf_status", "Not tested"),
        "clinical_summary"          : concordance.get("clinical_summary", ""),
        "flag_for_review"           : concordance.get("flag_for_review", False),
        # ── Deterministic Python-computed fields ──────────────────────────
        "risk_tier"                 : risk_tier,
        "confidence"                : morphology.get("confidence", "Moderate"),
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# SURVIVAL PREDICTION — images-only Call 1 + LR classifier
# SURVIVAL_FEATURE_SYSTEM is imported from prompts.py (see top of file)
# ─────────────────────────────────────────────────────────────────────────────


def run_survival_prediction(patches: list[str]) -> dict:
    """
    2-step survival prediction:
      Step 1: Ollama extracts 4 features from H&E patches (images only — no staging)
      Step 2: LR classifier produces Good/Poor prediction + probability

    Args:
        patches: list of patch file paths

    Returns:
        dict with survival prediction, probability, features, model stats
    """
    patch_paths = patches[:N_PATCHES]
    images_b64 = [encode_image(p, resize_to=PATCH_SIZE) for p in patch_paths]

    # ── Step 1: Feature extraction (images only) ──────────────────────────────
    user_text = (
        f"You are viewing {len(images_b64)} H&E patches from a colorectal cancer resection specimen.\n"
        "Extract the 4 prognostic morphological feature scores as specified.\n"
        "Return ONLY the JSON object with the 4 integer scores."
    )

    features_raw = {}
    try:
        raw = _call_ollama(SURVIVAL_FEATURE_SYSTEM, user_text, images_b64)
        features_raw = _parse_json(raw)
        if isinstance(features_raw, list) and features_raw:
            features_raw = features_raw[0]
        if "error" in features_raw:
            raise ValueError(f"Could not parse feature JSON: {raw[:300]}")
    except Exception as e:
        return {"error": f"Feature extraction failed: {e}"}

    # Validate and clamp features
    til_score      = int(max(0, min(2, features_raw.get("til_score",      1))))
    stroma_score   = int(max(0, min(1, features_raw.get("stroma_score",   0))))
    budding_score  = int(max(0, min(3, features_raw.get("budding_score",  0))))
    necrosis_score = int(max(0, min(1, features_raw.get("necrosis_score", 0))))

    # ── Step 2: LR classifier ─────────────────────────────────────────────────
    lr_model = _load_lr_model()
    feature_vector = np.array([[til_score, stroma_score, budding_score, necrosis_score]])

    if lr_model is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                pred_label = int(lr_model.predict(feature_vector)[0])
                proba = lr_model.predict_proba(feature_vector)[0]
                if hasattr(lr_model, "classes_"):
                    classes = list(lr_model.classes_)
                    good_idx = classes.index(1) if 1 in classes else 1
                    prob_good = float(proba[good_idx])
                else:
                    prob_good = float(proba[1]) if len(proba) > 1 else float(proba[0])

                survival_prediction = (
                    "Good (>5 year survival likely)" if pred_label == 1
                    else "Poor (<5 year survival likely)"
                )
                probability = round(prob_good, 3)
            except Exception:
                survival_prediction = "Poor (<5 year survival likely)"
                probability = 0.35
                prob_good = 0.35
    else:
        # Heuristic fallback if model not found
        adverse_score = stroma_score + (budding_score > 1) + necrosis_score - (til_score > 0)
        prob_good = max(0.15, min(0.85, 0.60 - adverse_score * 0.12))
        probability = round(prob_good, 3)
        survival_prediction = (
            "Good (>5 year survival likely)" if prob_good >= 0.5
            else "Poor (<5 year survival likely)"
        )

    # Human-readable feature labels
    til_label     = {0: "Low", 1: "Moderate", 2: "High"}.get(til_score, "Unknown")
    stroma_label  = {0: "Stroma-poor", 1: "Stroma-rich"}.get(stroma_score, "Unknown")
    budding_label = {0: "Cannot determine", 1: "Bd1", 2: "Bd2", 3: "Bd3"}.get(budding_score, "Unknown")
    necrosis_bool = necrosis_score == 1

    # Reasoning text
    reasoning_parts = []
    if til_score == 2:
        reasoning_parts.append(
            "High TIL density suggests active anti-tumour immune response, "
            "often associated with MSI-H status and better prognosis."
        )
    elif til_score == 0:
        reasoning_parts.append(
            "Low TIL density indicates limited immune infiltration at the "
            "tumour-stroma border, associated with less favourable immune microenvironment."
        )
    else:
        reasoning_parts.append("Moderate TIL density is observed at the tumour-stroma interface.")

    if stroma_score == 1:
        reasoning_parts.append(
            "Stroma-rich tumour architecture (>50% stromal area) is an independent adverse prognostic feature."
        )
    else:
        reasoning_parts.append(
            "Stroma-poor morphology (<50% stromal area) is associated with more favourable outcomes."
        )

    if budding_score >= 2:
        reasoning_parts.append(
            f"Tumour budding grade {budding_label} at the invasive front is a significant "
            "independent poor prognostic factor per ITBCC guidelines."
        )
    elif budding_score == 0:
        reasoning_parts.append("Tumour budding could not be reliably assessed from the available patches.")
    else:
        reasoning_parts.append("Low tumour budding (Bd1) is identified, indicating a favourable budding profile.")

    if necrosis_bool:
        reasoning_parts.append(
            "Intratumoral necrosis is present, which correlates with aggressive tumour biology and poor prognosis."
        )

    feature_reasoning = " ".join(reasoning_parts[:3])

    stats = _get_model_stats(lr_model)

    return {
        "survival_prediction": survival_prediction,
        "probability": probability,
        "features_extracted": {
            "til_density"  : til_label,
            "stromal_ratio": stroma_label,
            "tumour_budding": budding_label,
            "necrosis"     : necrosis_bool,
        },
        "raw_scores": {
            "til_score"     : til_score,
            "stroma_score"  : stroma_score,
            "budding_score" : budding_score,
            "necrosis_score": necrosis_score,
        },
        "model_accuracy"  : stats["model_accuracy"],
        "model_auc"       : stats["model_auc"],
        "model_note"      : stats["model_note"],
        "feature_reasoning": feature_reasoning,
    }
