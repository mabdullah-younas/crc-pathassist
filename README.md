# CRC-PathAssist

**Privacy-preserving AI pathology assistant for colorectal cancer** — powered by **Gemma 4 (gemma4:e4b)** running locally via **Ollama**. No cloud. No API keys. No PHI leaves the device.

Hackathon: [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) · Health & Sciences track · Ollama track

---

## What it does

CRC-PathAssist takes H&E histopathology patch images from a colorectal cancer resection specimen and generates a structured CAP-aligned pathology report — entirely on local hardware. This makes it deployable in low-resource hospitals, rural pathology units, and privacy-sensitive clinical environments where cloud AI is not an option.

| Capability | Detail |
|---|---|
| Morphological report | Tumour type, grade, pT estimate, budding, TIL density, stroma ratio, LVI, PNI |
| Concordance checking | Compares AI morphological staging against the clinician's surgical record |
| Risk stratification | Deterministic CAP/AJCC risk tier computed in Python (not delegated to LLM) |
| Survival risk score | Logistic regression classifier over 4 extracted morphological features |
| Local inference | gemma4:e4b via Ollama — runs on a 6 GB VRAM GPU (RTX 3060/4050) |
| Offline operation | Zero external API calls — no internet connection required during inference |

---

## Architecture

```
H&E patches
    │
    ▼
[Call 1 — Gemma 4 vision, images only]
  Morphological assessment (pT, grade, budding, TIL, stroma, LVI, PNI)
  No staging context → no anchoring bias
    │
    ▼
[Python pT consistency validator]
  Checks reasoning text for pericolorectal fat/stroma evidence
  Auto-corrects underestimated pT labels (e.g. pT2→pT3 when fat involvement
  is described in reasoning but label was misassigned)
    │
    ▼
[Call 2 — Gemma 4 text only, no images]
  Concordance check against clinical staging record
  Molecular/biomarker reformatting (KRAS, NRAS, BRAF, MMR)
  Clinical summary generation
    │
    ▼
[Python — compute_risk_tier()]
  Deterministic AJCC/CAP risk tier from staging + morphological features
  No LLM involvement in this step
    │
    ▼
Structured JSON report → React frontend → PDF export
```

### Why two calls + a Python validator?

The standard single-call approach has an anchoring bias problem: if the model sees the clinical staging in the same prompt as the images, it tends to fit its morphological description to match the provided stage. The two-call design eliminates this — Call 1 is morphology-only with zero staging context. The Python validator then catches the most common model error (pT label inconsistent with the model's own written reasoning) before concordance is computed.

---

## Project structure

```
├── backend/
│   ├── api.py                 # FastAPI routes
│   ├── smart_pipeline.py      # Core inference (two-call + Python validator)
│   ├── prompts.py             # All system prompts (single source of truth)
│   ├── schema.py              # Pydantic data models
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template (copy to .env)
│   └── temp_uploads/          # Auto-created upload directory
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── components/
│   │       ├── InputSection.tsx
│   │       ├── OutputSection.tsx
│   │       ├── SynopticReportTab.tsx
│   │       ├── SurvivalTab.tsx
│   │       └── ResearchTab.tsx
│   └── package.json
│
├── data_pipeline/
│   ├── patch_extraction.py    # 3-tier anatomical WSI patch sampler (CZI)
│   ├── build_dataset.py
│   ├── make_splits.py
│   └── check_labels.py
│
├── lr_survival_model.pkl      # Pre-trained logistic regression (research only)
├── survival_morphology.ipynb  # Model training notebook
└── README.md
```

---

## Quick start

> **Full setup guide**: see [SETUP.md](SETUP.md)

### Option A — One-click (recommended for judges)

```bat
run.bat
```

Double-click `run.bat` from the project root. It will:
1. Check Python, Node.js, and Ollama are installed
2. Create the Python virtual environment (if not present)
3. Install all Python and Node dependencies automatically
4. Start the backend (port 8000) and frontend (port 3000) in separate windows
5. Open `http://localhost:3000` in your browser

> **Pre-requisite**: Pull the Gemma 4 model once before running (one-time ~5 GB download):
> ```bash
> ollama pull gemma4:e4b
> ollama serve
> ```

### Option B — Manual setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama with gemma4:e4b pulled

```bash
# 1. Install Ollama from https://ollama.ai/
# 2. Pull the model (one-time, ~5 GB download)
ollama pull gemma4:e4b
# 3. Start Ollama (keep this running)
ollama serve
```

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv ../env
../env/Scripts/activate        # Windows
# source ../env/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment config (no API keys needed)
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/Mac

# Start API server
python -m uvicorn api:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:3000` · API: `http://localhost:8000` · API docs: `http://localhost:8000/docs`

### Using the app

1. Upload 1–2 H&E patch images (PNG/JPG)
2. Optionally enter clinical staging (pT, pN, overall stage)
3. Optionally enter molecular results (KRAS, NRAS, BRAF, MMR)
4. Click **Generate Report**
5. View synoptic report, concordance flags, survival risk score

---

## VRAM requirements

| GPU VRAM | Configuration | Notes |
|---|---|---|
| 6 GB (RTX 3060 / 4050) | N_PATCHES=2, PATCH_SIZE=256 | Default — safe headroom |
| 8 GB (RTX 3070 / 4060) | N_PATCHES=3, PATCH_SIZE=336 | Increase in smart_pipeline.py |
| 12+ GB | N_PATCHES=4, PATCH_SIZE=448 | Maximum detail |

gemma4:e4b (Q4_K_M) occupies ~5.0 GB of VRAM for weights. Each 256px patch adds ~250–350 MB for the vision projection and KV cache. The 6 GB default is calibrated so two patches fit comfortably within the remaining headroom.

To adjust for your hardware, edit two lines in `backend/smart_pipeline.py`:
```python
N_PATCHES  = 2    # increase if you have more VRAM
PATCH_SIZE = 256  # increase if you have more VRAM
```

---

## Patch extraction (WSI pipeline)

`data_pipeline/patch_extraction.py` implements a **3-tier anatomical sampler** for Zeiss CZI whole-slide images:

| Tier | Fraction | Target region | Clinical purpose |
|---|---|---|---|
| Tier 1 (_front) | 50% | Invasive front | pT staging, tumour budding, LVI, PNI |
| Tier 2 (_interface) | 30% | Tumour-stroma interface | TIL density, stroma ratio |
| Tier 3 (_centre) | 20% | Tumour centre | Grade, necrosis, mucinous component |

The invasive front is detected via Sobel gradient on a tissue density map computed from an overview image — high-gradient cells in the density map (0.15–0.65 range) correspond to the tissue transition zone where the tumour meets pericolorectal stroma or fat.

Target resolution: 0.5 MPP (~20× effective magnification).

---

## API reference

### POST `/api/generate`
Runs smart report and survival prediction concurrently.

```bash
curl -X POST http://localhost:8000/api/generate \
  -F "files=@patch_front.png" \
  -F "files=@patch_interface.png" \
  -F "case_id=CASE_001" \
  -F "pT=pT3" \
  -F "pN=N0" \
  -F "stage=2" \
  -F "kras=WT" \
  -F "nras=WT" \
  -F "braf=NOT_TESTED" \
  -F "mmr=NO_LOSS"
```

### POST `/api/smart-report`
Smart report only (morphology + concordance).

### POST `/api/survival-prediction`
Survival risk score only.

### GET `/api/health`
Returns `{"status": "ok", "smart_pipeline": true/false}`.

---

## The pT consistency problem (and how we fixed it)

Small vision-language models frequently produce **label–reasoning inconsistency**: the model writes in its reasoning that it sees "tumour invading into soft tissue" or "pericolorectal fat involvement" but then labels the case pT2. This is the most common error in automated CRC staging.

CRC-PathAssist addresses this at three levels:

**1. Prompt-level — decision tree anchors.** The morphology prompt provides an explicit pT decision tree: "if you see pericolorectal fat or loose connective tissue outside the MP containing tumour → it is pT3 or pT4." It also requires the model to write a specific sentence in its reasoning that either confirms or excludes pericolorectal fat involvement, making the inconsistency visible.

**2. Prompt-level — forced reasoning structure.** The `morphological_reasoning` field requires five structured sentences. Sentence 2 must explicitly state whether fat/stroma beyond the MP outer border was present or absent. This forces the model to confront the key diagnostic criterion.

**3. Python validator.** After Call 1, `smart_pipeline.py` scans the reasoning text for pericolorectal fat/tissue evidence phrases. If such evidence is found but the pT label is pT1 or pT2, the label is automatically upgraded to pT3 and a note is appended to the reasoning field for auditability.

---

## Survival risk model

The survival score uses a logistic regression classifier over four morphological features extracted by Gemma 4 from the H&E patches: TIL density score (0–2), stroma score (0–1), tumour budding score (0–3), and necrosis score (0–1).

**Important caveat:** The LR model was trained and validated on the SR386 dataset (57 held-out cases). This is a small validation cohort. The model should be treated as a morphological risk score — a structured summary of adverse and protective features — rather than a clinical survival predictor. It is not validated for clinical use.

We report the model's internal validation numbers honestly in the UI rather than omitting them, because transparency about model limitations is part of responsible AI in healthcare.

---

## Public datasets for testing

If you do not have CZI slides, you can test the pipeline using publicly available CRC patch datasets:

| Dataset         | Size                         | MPP       | Access |
|-----------------|------------------------------|-----------|--------|
| CRC-VAL-HE-7K   | 7,180 patches, 224×224px     | 0.5 MPP   | [zenodo.org/records/1214456](https://zenodo.org/records/1214456)
| NCT-CRC-HE-100K | 100,000 patches, 224×224px   | 0.5 MPP   | [zenodo.org/records/1214456](https://zenodo.org/records/1214456)
| TCGA-COAD (WSI) | Full slides with pT/pN labels| variable  | [cancerimagingarchive.net](https://www.cancerimagingarchive.net/collection/tcga-coad/)

CRC-VAL-HE-7K is the best starting point — ~200 MB download, 50 patients, same 0.5 MPP as this pipeline's target resolution.

---

## Why Gemma 4 and why local?

- **Privacy:** H&E slides contain identifiable patient tissue. Running inference locally ensures no PHI leaves the hospital network.
- **Offline deployment:** Many district hospitals and pathology units in low-resource settings have no reliable internet. A locally running model works in these environments.
- **Ollama integration:** gemma4:e4b is the right size — capable enough for multimodal pathology reasoning, small enough to run on a workstation GPU without cloud infrastructure.
- **No API keys:** Judges and evaluators can run the app with zero account setup — just Ollama and the model weight download.
- **Apache 2.0 license:** Gemma 4 can be freely used, modified, and deployed in research and commercial settings.

---

## Limitations and ethical notes

- **Research use only.** This tool is not validated for clinical diagnosis and must not be used as a substitute for qualified pathologist review.
- **Patch-based limitations.** pN staging requires lymph node tissue, which is rarely captured in random patches. The model correctly reports this as indeterminate.
- **Small VRAM constraint.** The 6 GB configuration uses 2 patches at 256px. More patches and higher resolution improve accuracy. Upgrade the hardware configuration when possible.
- **Survival model.** The LR classifier has AUC 0.605 on 57 held-out cases — close to chance. It is a structured feature summary, not a validated prognostic tool.

---

## License

Apache 2.0 (matching Gemma 4 license). See LICENSE.

## Contact

CRC-PathAssist Team — Gemma 4 Good Hackathon submission, May 2026