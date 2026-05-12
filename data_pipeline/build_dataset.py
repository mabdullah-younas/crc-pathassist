import pylibCZIrw.czi as pyczi
import numpy as np
from PIL import Image
from pathlib import Path
from tqdm import tqdm
import json, csv

PATCH_PX   = 512        # output patch size in pixels
TARGET_MPP = 0.5        # ~20x effective magnification
NATIVE_MPP = 0.1112     # SurGen scan resolution
ZOOM       = NATIVE_MPP / TARGET_MPP   # = 0.2224 (downsample factor)
N_PATCHES  = 8          # patches per slide
TISSUE_THR = 0.55       # min tissue fraction to accept a candidate

def tissue_score(patch_arr):
    """Fraction of valid tissue (excludes white glass AND black padding)."""
    # Convert to float to avoid overflow during mean if array is uint8
    gray = patch_arr.astype(float).mean(axis=2)
    
    # Tissue is darker than glass (< 220) but brighter than black padding (> 15)
    is_tissue = (gray < 220) & (gray > 15)
    
    return is_tissue.mean()

def extract(czi_path, out_dir, n=N_PATCHES):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with pyczi.open_czi(str(czi_path)) as czi:
        bb = czi.total_bounding_rectangle
        W, H = bb.w, bb.h

        # Low-res overview for tissue finding (~2% zoom)
        ov_zoom = 0.02
        overview = czi.read(roi=(bb.x, bb.y, W, H),
                            plane={"C": 0}, zoom=ov_zoom)
        ov = np.array(overview)[:, :, :3]
        ov_h, ov_w = ov.shape[:2]

        # Grid scan at overview resolution
        cell = 32  # grid cell size in overview pixels
        candidates = []
        for r in range(0, ov_h - cell, cell):
            for c in range(0, ov_w - cell, cell):
                score = tissue_score(ov[r:r+cell, c:c+cell])
                if score > TISSUE_THR:
                    # Map back to full-res coords
                    fx = bb.x + int(c / ov_zoom)
                    fy = bb.y + int(r / ov_zoom)
                    candidates.append((score, fx, fy))

        candidates.sort(reverse=True)

        # Space out selections (avoid redundant neighbours)
        min_dist = int(PATCH_PX / ZOOM) * 3
        selected, saved = [], []
        for score, fx, fy in candidates:
            if len(selected) >= n:
                break
            if all(abs(fx-sx) > min_dist or abs(fy-sy) > min_dist
                   for _, sx, sy in selected):
                selected.append((score, fx, fy))

        for i, (score, fx, fy) in enumerate(selected):
            native_size = int(PATCH_PX / ZOOM)
            region = czi.read(
                roi=(fx, fy, native_size, native_size),
                plane={"C": 0}, zoom=ZOOM
            )
            
            # Force conversion to standard 8-bit unsigned integer
            region_8bit = np.clip(region[:, :, :3], 0, 255).astype(np.uint8)
            
            img = Image.fromarray(region_8bit)
            # Ensure it is standard RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            img = img.resize((PATCH_PX, PATCH_PX), Image.LANCZOS)
            img.save(out_dir / f"p{i:02d}.png")
            saved.append(str(out_dir / f"p{i:02d}.png"))

    return saved

# ── Batch run ──────────────────────────────────────────────
CZI_DIR    = Path(r"G:\My Drive\Colorectal Cancer\Surgen\SR386\SR386_WSIs")
OUTPUT_DIR = Path("./patches")
LOG        = []

for czi_file in tqdm(sorted(CZI_DIR.glob("*.czi"))):
    case_id = czi_file.stem
    
    # Wrap the extraction in a try-except block
    try:
        patches = extract(czi_file, OUTPUT_DIR / case_id)
        LOG.append({"case_id": case_id, "patches": patches, "count": len(patches)})
    except Exception as e:
        # If a file crashes, log it and move to the next one!
        print(f"\n[ERROR] Skipping {case_id} due to error: {e}")
        continue

with open("patch_index.json", "w") as f:
    json.dump(LOG, f, indent=2)

print(f"Done. {len(LOG)} cases processed successfully.")