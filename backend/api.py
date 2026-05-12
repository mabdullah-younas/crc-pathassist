import os
import json
import asyncio
import base64
import io
from pathlib import Path
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool

# ── Backend detection ─────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.resolve()
TEMP_DIR = BACKEND_DIR / "temp_uploads"
TEMP_DIR.mkdir(exist_ok=True)

def str_to_bool(value: str) -> bool:
    """Accept True/False/true/false/1/0 from HTML form data."""
    return str(value).strip().lower() in ("true", "1", "yes")

# ── Import real pipeline (falls back to mock on import error) ─────────────────
try:
    from smart_pipeline import run_smart_report, run_survival_prediction
    _SMART_PIPELINE_AVAILABLE = True
except Exception as _e2:
    _SMART_PIPELINE_AVAILABLE = False
    print(f"[WARNING] Smart pipeline import failed: {_e2}")

# ── Mock fallbacks ─────────────────────────────────────────────────────────────
def _mock_smart_report(case: dict) -> dict:
    pT_user = case.get("pT", "").strip()
    pN_user = case.get("pN", "").strip()
    return {
        "tumour_type": "Adenocarcinoma (NOS)",
        "differentiation_grade": "Moderately differentiated (G2)",
        "morphological_pT_estimate": "pT3",
        "pT_comparison": "CONCORDANT" if pT_user == "pT3" else (f"DISCORDANT — model: pT3, record: {pT_user}" if pT_user else None),
        "morphological_pN_note": "No regional lymph node involvement visible in available patches",
        "pN_comparison": "CONCORDANT" if pN_user in ["N0", ""] else (f"DISCORDANT — model: N0, record: {pN_user}" if pN_user else None),
        "lymphovascular_invasion": "Not identified",
        "perineural_invasion": "Not identified",
        "tumour_budding": "Low (Bd1)",
        "tumour_stroma_ratio": "Stroma-poor (<50%)",
        "til_density": "Moderate",
        "necrosis": False,
        "mucinous_component": "<10% (Non-mucinous)",
        "mmr_status": "Proficient (pMMR)",
        "mmr_proteins_lost": [],
        "kras_status": "Wild-type",
        "kras_codon": "—",
        "nras_status": "Wild-type",
        "braf_status": "Not tested",
        "risk_tier": "Intermediate",
        "clinical_summary": (
            "This case demonstrates a moderately differentiated colorectal adenocarcinoma with pT3 invasion depth. "
            "No lymphovascular or perineural invasion is identified on the available patches. "
            "MMR proficiency is preserved and KRAS/NRAS wild-type status may confer eligibility for anti-EGFR therapy."
        ),
        "confidence": "Moderate",
        "flag_for_review": False,
        "morphological_reasoning": (
            "The tumour shows predominantly glandular architecture consistent with G2 differentiation. "
            "Invasion into pericolorectal fat is suggested by the morphological appearance, consistent with pT3. "
            "No lymphovascular spaces are identified. TIL density is moderate, consistent with pMMR status."
        ),
        "_mock": True,
    }

def _mock_survival() -> dict:
    return {
        "survival_prediction": "Good (>5 year survival likely)",
        "probability": 0.62,
        "features_extracted": {
            "til_density": "Moderate",
            "stromal_ratio": "Stroma-poor",
            "tumour_budding": "Bd1",
            "necrosis": False,
        },
        "raw_scores": {"til_score": 1, "stroma_score": 0, "budding_score": 1, "necrosis_score": 0},
        "model_accuracy": "61.4%",
        "model_auc": "0.605",
        "model_note": "Validated on 57 held-out SR386 cases. This is a research tool — do not use for clinical decisions.",
        "feature_reasoning": (
            "Moderate TIL density is observed at the tumour-stroma interface. "
            "Stroma-poor morphology (<50% stromal area) is associated with more favourable outcomes. "
            "Low tumour budding (Bd1) indicates a favourable budding profile."
        ),
        "_mock": True,
    }

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="CRC-PathAssist API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "CRC-PathAssist API v2",
        "smart_pipeline": _SMART_PIPELINE_AVAILABLE,
    }


async def _save_uploads(files: list[UploadFile]) -> list[str]:
    """Save uploaded files to temp dir and return absolute paths."""
    saved = []
    for f in files:
        dest = TEMP_DIR / f.filename
        content = await f.read()
        dest.write_bytes(content)
        saved.append(str(dest))
    return saved


# ─────────────────────────────────────────────────────────────────────────────
# NEW: /api/generate — runs smart report + survival in parallel
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/generate")
async def api_generate(
    files: list[UploadFile] = File(default=[]),
    case_id: str = Form("DEMO_001"),
    pT: str = Form(""),
    pN: str = Form(""),
    stage: str = Form(""),
    kras: str = Form("NOT TESTED"),
    nras: str = Form("NOT TESTED"),
    braf: str = Form("NOT TESTED"),
    mmr: str = Form("NO LOSS"),
    post_neo: str = Form("False")
):
    """
    Runs smart report + survival prediction concurrently.
    Returns both results in one response.
    """
    try:
        saved_paths = await _save_uploads(files)

        clinical_inputs = {"pT": pT, "pN": pN, "stage": stage, "post_neoadjuvant": str_to_bool(post_neo)}
        molecular_inputs = {"kras": kras, "nras": nras, "braf": braf, "mmr": mmr}

        if _SMART_PIPELINE_AVAILABLE and saved_paths:
            # Run both in parallel via thread pool (blocking calls)
            report_task = run_in_threadpool(
                run_smart_report, saved_paths, clinical_inputs, molecular_inputs
            )
            survival_task = run_in_threadpool(
                run_survival_prediction, saved_paths
            )
            report_result, survival_result = await asyncio.gather(
                report_task, survival_task
            )
        else:
            # Fallback mocks
            case = {"pT": pT, "pN": pN, "stage": stage}
            report_result = _mock_smart_report(case)
            survival_result = _mock_survival()

        if "error" in report_result:
            raise HTTPException(status_code=500, detail=f"Smart report error: {report_result['error']}")
        if "error" in survival_result:
            raise HTTPException(status_code=500, detail=f"Survival prediction error: {survival_result['error']}")

        return {
            "case_id": case_id,
            "report": report_result,
            "survival": survival_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# NEW: /api/smart-report — standalone
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/smart-report")
async def api_smart_report(
    files: list[UploadFile] = File(default=[]),
    case_id: str = Form("DEMO_001"),
    pT: str = Form(""),
    pN: str = Form(""),
    stage: str = Form(""),
    kras: str = Form("NOT TESTED"),
    nras: str = Form("NOT TESTED"),
    braf: str = Form("NOT TESTED"),
    mmr: str = Form("NO LOSS"),
    post_neo: str = Form("False")
):
    try:
        saved_paths = await _save_uploads(files)
        clinical_inputs = {"pT": pT, "pN": pN, "stage": stage}
        molecular_inputs = {"kras": kras, "nras": nras, "braf": braf, "mmr": mmr}

        if _SMART_PIPELINE_AVAILABLE and saved_paths:
            result = await run_in_threadpool(
                run_smart_report, saved_paths, clinical_inputs, molecular_inputs
            )
        else:
            result = _mock_smart_report({"pT": pT, "pN": pN})

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# NEW: /api/survival-prediction — standalone
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/survival-prediction")
async def api_survival_prediction(
    files: list[UploadFile] = File(default=[]),
    case_id: str = Form("DEMO_001")
):
    try:
        saved_paths = await _save_uploads(files)

        if _SMART_PIPELINE_AVAILABLE and saved_paths:
            result = await run_in_threadpool(run_survival_prediction, saved_paths)
        else:
            result = _mock_survival()

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY endpoints kept for backward compatibility
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/report")
async def api_report(
    files: list[UploadFile] = File(default=[]),
    case_id: str = Form("DEMO_001"),
    pT: str = Form("pT3"),
    pN: str = Form("N0"),
    stage: str = Form("2"),
    kras: str = Form("WT"),
    nras: str = Form("WT"),
    braf: str = Form("not_tested"),
    mmr: str = Form("NO LOSS"),
    post_neo: str = Form("False"),
):
    try:
        saved_paths = await _save_uploads(files)
        case = {
            "case_id": case_id,
            "patches": saved_paths,
            "pT": pT, "pN": pN, "stage": stage,
            "kras": kras, "nras": nras, "braf": braf, "mmr": mmr,
            "post_neoadjuvant": str_to_bool(post_neo),
            "survival_status": "unknown",
        }
        if _PIPELINE_AVAILABLE and saved_paths:
            result = await run_in_threadpool(run_inference, case, 2)
            report = result.get("report", {})
        else:
            report = _mock_smart_report(case)
        if "error" in report:
            raise HTTPException(status_code=500, detail=str(report))
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/qa")
async def api_qa(
    files: list[UploadFile] = File(default=[]),
    case_id: str = Form("DEMO_001"),
    pT: str = Form("pT3"),
    pN: str = Form("N0"),
    stage: str = Form("2"),
    kras: str = Form("WT"),
    nras: str = Form("WT"),
    braf: str = Form("not_tested"),
    mmr: str = Form("NO LOSS"),
    post_neo: str = Form("False"),
):
    try:
        saved_paths = await _save_uploads(files)
        case = {
            "case_id": case_id,
            "patches": saved_paths,
            "pT": pT, "pN": pN, "stage": stage,
            "kras": kras, "nras": nras, "braf": braf, "mmr": mmr,
            "post_neoadjuvant": str_to_bool(post_neo),
        }
        if _PIPELINE_AVAILABLE and saved_paths:
            result = await run_in_threadpool(run_discordance, case, 2)
            qa = result.get("qa_report", {})
        else:
            qa = {
                "morphological_pt_estimate": pT,
                "provided_pt": pT,
                "pt_concordant": True,
                "differentiation_estimate": "Moderately differentiated (G2)",
                "tumour_stroma_ratio": "Low stroma (<50%)",
                "til_density": "Moderate",
                "til_mmr_concordant": True,
                "budding_estimate": "Low (Bd1)",
                "mucinous_component": "<10% — Non-mucinous",
                "overall_discordance": False,
                "discordance_details": [],
                "flag_for_review": False,
                "confidence": "High",
                "qa_summary": "Morphological features are concordant with provided staging.",
            }
        if "error" in qa:
            raise HTTPException(status_code=500, detail=str(qa))
        return qa
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pdf/{case_id}")
async def download_pdf(case_id: str):
    pdf_path = BACKEND_DIR / f"report_{case_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"No PDF found for case {case_id}")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"report_{case_id}.pdf",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)