# CRC-PathAssist Frontend

React + Vite frontend for the CRC-PathAssist pathology reporting application.

## Tech Stack

- **Framework**: React 19
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS 4
- **Icons**: Lucide React
- **Animations**: Motion
- **Language**: TypeScript

## Quick Start

### Prerequisites
- **Node.js 18+** with npm

### Installation & Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will run at: `http://localhost:3000` (or as specified in package.json)

### Production Build

```bash
# Build for production
npm run build

# Preview production build locally
npm run preview

# Clean build artifacts
npm clean
```

## Project Structure

```
src/
├── App.tsx                    # Main app component
├── main.tsx                   # Entry point
├── index.css                  # Global styles
└── components/
    ├── InputSection.tsx       # Case data & image upload
    ├── OutputSection.tsx      # Tab switcher (Report/Survival/Research)
    ├── SynopticReportTab.tsx  # Pathology report display + PDF export
    ├── SurvivalTab.tsx        # Survival prediction results
    └── ResearchTab.tsx        # Research findings tab
```

## Key Features

### InputSection
- Upload H&E patch images
- Enter clinical staging (pT, pN, stage)
- Enter molecular biomarkers (KRAS, NRAS, BRAF, MMR)
- Trigger report generation

### SynopticReportTab
- Display CAP-aligned pathology report
- Show risk tier (Low/Intermediate/High/Very High)
- Display confidence level (Low/Moderate/High)
- Highlight discordances between AI and clinical staging
- **Flag for review** warning (when discordances detected)
- PDF export functionality

### SurvivalTab
- Display 5-year survival prediction (Good/Poor)
- Show prediction probability
- Display extracted morphological features (TIL, stroma, budding, necrosis)
- Include model accuracy metrics

## API Integration

Frontend communicates with FastAPI backend at `http://localhost:8000`

Endpoints used:
- `POST /api/generate` — Generate full report + survival
- `GET /api/health` — Health check

## Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Create optimized production build |
| `npm run preview` | Preview production build locally |
| `npm clean` | Remove dist folder |
| `npm run lint` | Type-check with TypeScript |

## Configuration

Ensure the backend API is running on `http://localhost:8000` before starting the frontend.

If backend is on a different URL, update API calls in component files.

## Styling

Uses **Tailwind CSS 4** for all styling. Custom classes and animations are defined in:
- Component files (inline className attributes)
- index.css (global styles)

Key design patterns:
- Motion animations for smooth transitions
- Color-coded risk tiers (green/amber/orange/red)
- Responsive grid layouts
- Card-based UI components

## Notes

- All report data comes from backend `/api/generate` endpoint
- PDF generation happens client-side using HTML + window.print()
- Frontend is fully responsive (mobile, tablet, desktop)
