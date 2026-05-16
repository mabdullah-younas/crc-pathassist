# CRC-PathAssist Backend

The main application backend powered by FastAPI.

## Quick Start

```bash
# Create virtual environment
python -m venv ../env
../env/Scripts/activate  # Windows
# or: source ../env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn api:app --reload --port 8000
```

## Files

- **api.py**: FastAPI application with 3 endpoints
  - `POST /api/generate` — Run smart report + survival concurrently
  - `POST /api/smart-report` — Smart report only
  - `POST /api/survival-prediction` — Survival prediction only

- **smart_pipeline.py**: Core inference functions
  - `run_smart_report()` — Morphological analysis + concordance checking
  - `run_survival_prediction()` — Feature extraction + LR classification

- **schema.py**: Pydantic models for API requests/responses

- **prompts.py**: System prompts for Ollama (gemma4:e4b) — all inference is local

- **.env**: Configuration file (create this, copy from .env.example if provided)

- **temp_uploads/**: Temporary storage for uploaded patch images (auto-created)

## Environment Variables

Create a `.env` file in this directory:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
```

## Dependencies

See `requirements.txt` for the complete list. Key packages:
- **fastapi** — Web framework
- **uvicorn** — ASGI server
- **pillow** — Image processing
- **pydantic** — Data validation
- **numpy** — Numerical computations

## API Examples

### Generate Full Report

```bash
curl -X POST http://localhost:8000/api/generate \
  -F "files=@histology_patch.png" \
  -F "case_id=CASE_001" \
  -F "pT=pT3" \
  -F "pN=N0" \
  -F "stage=2" \
  -F "kras=WT" \
  -F "nras=WT" \
  -F "braf=NOT_TESTED" \
  -F "mmr=NO_LOSS" \
  -F "post_neo=False"
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "ok",
  "service": "CRC-PathAssist API v2",
  "smart_pipeline": true
}
```

## Notes

- Ollama must be running locally: `ollama serve`
- Model must be pulled: `ollama pull gemma4:e4b`
- If Ollama unavailable, API returns mock data for testing
- All processing is local — no cloud API calls
