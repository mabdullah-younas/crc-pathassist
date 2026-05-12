# CRC-PathAssist

**AI-assisted colorectal cancer (CRC) pathology reporting** powered by **Gemma 4** (via Ollama).

Hackathon: [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)

## Overview

CRC-PathAssist is a full-stack application that:
- Analyzes H&E histopathology patches using a local Gemma 4 vision model (via Ollama)
- Generates CAP-aligned synoptic colorectal cancer pathology reports
- Performs concordance checking between AI-generated morphological staging and clinician inputs
- Predicts 5-year survival outcomes using extracted morphological features
- Provides risk stratification and flags cases for senior pathologist review

## Features

- **Smart Synoptic Reports**: Morphological analysis → staging estimation → concordance checking
- **Survival Prediction**: Feature extraction → logistic regression classification
- **Discordance Detection**: Flags cases where AI estimates differ from clinical records
- **Local Processing**: All inference runs locally (no cloud dependencies)
- **Modern UI**: React + Vite frontend with real-time report generation

## Project Structure

```
├── backend/                    # Python FastAPI backend
│   ├── api.py                 # FastAPI routes + endpoints
│   ├── smart_pipeline.py      # Core ML pipeline (smart report + survival)
│   ├── schema.py              # Pydantic data models
│   ├── prompts.py             # Gemini/Ollama system prompts
│   ├── temp_uploads/          # Temporary storage for uploaded patches
│   └── .env                   # Backend configuration (secrets/API keys)
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.tsx            # Main app component
│   │   ├── components/        # UI components
│   │   │   ├── InputSection.tsx
│   │   │   ├── OutputSection.tsx
│   │   │   ├── SynopticReportTab.tsx
│   │   │   ├── SurvivalTab.tsx
│   │   │   └── ResearchTab.tsx
│   │   └── main.tsx           # Entry point
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── data_pipeline/              # Dataset preparation (training/dev only)
│   ├── build_dataset.py       # Extract patches from CZI files
│   ├── make_splits.py         # Create train/val/test splits
│   ├── check_labels.py        # Verify label consistency
│   └── ...
│
├── outputs/                    # Generated reports, eval results (gitignored)
│   ├── eval_results/
│   ├── reports/
│   ├── logs/
│   └── thumbnails/
│
├── env/                        # Python virtual environment (gitignored)
├── .gitignore
├── lr_survival_model.pkl       # Pre-trained logistic regression model
└── README.md
```

## Quick Start

### Prerequisites
- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Ollama** running locally with `gemma4:e4b` model pulled
  ```bash
  ollama pull gemma4:e4b
  ollama serve  # Run in background
  ```

### 1. Backend Setup
```bash
cd backend

# Create virtual environment (if not done)
python -m venv ../env
../env/Scripts/activate  # Windows
# or: source ../env/bin/activate  # Linux/Mac

# Install dependencies
pip install fastapi uvicorn pillow pydantic

# Start FastAPI server
python -m uvicorn api:app --reload --port 8000
```

Server runs at: `http://localhost:8000`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

App runs at: `http://localhost:5173` (default Vite port)

### 3. Using the App
1. Open the app in browser
2. Upload H&E patch image(s)
3. Enter clinical staging (pT, pN, stage) — *optional*
4. Enter molecular biomarkers (KRAS, NRAS, BRAF, MMR) — *optional*
5. Click **"Generate Comprehensive Report"**
6. View synoptic report, survival prediction, and flags

## Key Files

| File | Purpose |
|------|---------|
| `backend/api.py` | FastAPI endpoints: `/api/generate`, `/api/smart-report`, `/api/survival-prediction` |
| `backend/smart_pipeline.py` | Core inference: `run_smart_report()`, `run_survival_prediction()` |
| `backend/schema.py` | Pydantic models for reports, survival data, concordance |
| `frontend/src/components/SynopticReportTab.tsx` | Report display + PDF export |
| `lr_survival_model.pkl` | Serialized scikit-learn logistic regression model |

## API Endpoints

### POST `/api/generate`
Runs both smart report + survival prediction concurrently.
```bash
curl -X POST http://localhost:8000/api/generate \
  -F "files=@patch.png" \
  -F "case_id=CASE_001" \
  -F "pT=pT3" \
  -F "pN=N0" \
  -F "stage=2" \
  -F "kras=WT" \
  -F "nras=WT" \
  -F "braf=NOT_TESTED" \
  -F "mmr=NO_LOSS"
```

## Environment Variables

### Backend (`.env`)
```env
# Optional: Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
```

## Notes

- **Offline inference**: All processing runs locally via Ollama — no cloud calls
- **Mock fallback**: If Ollama is unavailable, API returns mock data for testing
- **Report flags**: Cases flagged for review when discordances are detected or unusual features present
- **Confidence levels**: Model-assigned High/Moderate/Low based on feature clarity
- **Research tool**: Survival predictions validated on 57 SR386 test cases (61.4% accuracy)

## License

TBD — Hackathon submission

## Contact

CRC-PathAssist Team
