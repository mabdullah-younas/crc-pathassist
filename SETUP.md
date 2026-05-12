# CRC-PathAssist — Complete Setup Guide

**Complete setup instructions for the CRC-PathAssist application.**

## Prerequisites

Before starting, ensure you have:

1. **Python 3.10+** — [Download](https://www.python.org/downloads/)
2. **Node.js 18+** — [Download](https://nodejs.org/)
3. **Ollama** — [Download](https://ollama.ai/)

### Install Gemma 4 Model

```bash
# Start Ollama service
ollama serve

# In another terminal, pull the Gemma 4 model
ollama pull gemma4:e4b
```

**Keep Ollama running** while using the application.

---

## Full Application Setup (5 minutes)

### Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Create Python virtual environment
python -m venv ../env

# Activate virtual environment
# On Windows:
../env/Scripts/activate
# On Linux/Mac:
source ../env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (optional configuration)
echo OLLAMA_BASE_URL=http://localhost:11434 > .env
echo OLLAMA_MODEL=gemma4:e4b >> .env

# Start API server
python -m uvicorn api:app --reload --port 8000
```

**API Server**: http://localhost:8000
**Health Check**: http://localhost:8000/api/health

### Step 2: Frontend Setup (in a new terminal)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend**: http://localhost:3000

### Step 3: Open Application

Visit **http://localhost:3000** in your browser and:

1. Upload an H&E histopathology patch (PNG/JPG)
2. *Optional*: Enter clinical staging (pT, pN, stage)
3. *Optional*: Enter molecular markers (KRAS, NRAS, BRAF, MMR)
4. Click **"Generate Comprehensive Report"**
5. Review results in the Synoptic Report, Survival, and Research tabs

---

## Directory Organization

```
crc-pathassist/
├── README.md                    ← Main documentation (you are here)
├── SETUP.md                     ← This file
├── .gitignore                   ← Git ignore patterns
├── lr_survival_model.pkl        ← Pre-trained survival model
│
├── backend/                     ← Python FastAPI backend ⭐ START HERE
│   ├── README.md               ← Backend documentation
│   ├── requirements.txt        ← Python dependencies
│   ├── api.py                  ← FastAPI endpoints
│   ├── smart_pipeline.py       ← Core AI pipeline
│   ├── schema.py               ← Data models
│   ├── prompts.py              ← AI system prompts
│   ├── .env                    ← Configuration (create this)
│   └── temp_uploads/           ← Auto-created upload directory
│
├── frontend/                    ← React + Vite frontend ⭐ START HERE
│   ├── README.md               ← Frontend documentation
│   ├── package.json            ← Node dependencies
│   ├── index.html
│   ├── src/
│   │   ├── App.tsx             ← Main React component
│   │   ├── main.tsx            ← Entry point
│   │   ├── index.css           ← Global styles
│   │   └── components/         ← UI components
│   └── vite.config.ts
│
├── data_pipeline/               ← Dataset tools (optional, development only)
│   ├── README.md               ← Data pipeline documentation
│   ├── build_dataset.py
│   ├── make_splits.py
│   ├── check_labels.py
│   └── ...
│
└── outputs/                     ← Generated reports (gitignored)
    ├── eval_results/
    ├── logs/
    └── reports/
```

---

## Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
../env/Scripts/activate  # Windows
pip install -r requirements.txt
```

### Ollama Connection Error

**Error**: `Ollama connection failed`

**Solution**:
```bash
# Ensure Ollama is running
ollama serve

# In another terminal, check the model is available
ollama list  # Should show gemma4:e4b

# Pull model if needed
ollama pull gemma4:e4b
```

### Frontend Can't Connect to Backend

**Error**: `Failed to fetch from http://localhost:8000`

**Solution**:
1. Ensure backend is running: `python -m uvicorn api:app --reload --port 8000`
2. Check backend is at http://localhost:8000/api/health
3. Verify CORS is enabled in `backend/api.py` (it is by default)

### Port Already in Use

**Error**: `Port 3000 already in use` (or 8000)

**Solution**:
```bash
# For backend (change 8000 to another port):
python -m uvicorn api:app --reload --port 8001

# For frontend (vite will usually find the next available port):
npm run dev
```

---

## Running Just the Backend (for Testing)

If you only want to test the API without the UI:

```bash
cd backend
../env/Scripts/activate
python -m uvicorn api:app --reload --port 8000
```

Then test with curl:
```bash
curl -X POST http://localhost:8000/api/generate \
  -F "files=@your_patch.png" \
  -F "case_id=TEST_001" \
  -F "pT=pT3" \
  -F "pN=N0" \
  -F "stage=2"
```

---

## Running Just the Frontend (with Mock Data)

The backend has built-in fallback mock data if Ollama is unavailable:

```bash
cd frontend
npm install
npm run dev
```

Then use the app — it will show mock pathology reports without needing Ollama running.

---

## Production Deployment

### Build Frontend for Production

```bash
cd frontend
npm run build

# This creates optimized files in dist/
# Deploy the dist/ folder to any static hosting service
```

### Run Backend in Production

```bash
cd backend
python -m uvicorn api:app --host 0.0.0.0 --port 8000

# Or use Gunicorn for multi-worker setup:
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app
```

---

## Additional Resources

- **FastAPI Docs**: http://localhost:8000/docs (when backend running)
- **Vite Guide**: https://vitejs.dev/
- **React Documentation**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/

---

## Support

For issues, check:
1. This SETUP.md file
2. Individual README files in `/backend` and `/frontend`
3. Ensure Ollama is running: `ollama serve`
4. Verify all dependencies installed: `pip list` and `npm list`

---

**Happy reporting! 🧬**
