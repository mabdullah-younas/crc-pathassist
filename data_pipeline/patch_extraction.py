"""
patch_extractor_fixed.py — CRC-PathAssist anatomically-targeted patch extractor

STRATEGY (3-tier sampling):
  Tier 1 (50% of patches) — Invasive front: deepest tumour-stroma boundary
                            → pT staging, tumour budding, LVI, PNI
  Tier 2 (30% of patches) — Tumour-stroma interface: mid-invasion zone
                            → TIL density, stroma ratio, budding
  Tier 3 (20% of patches) — Tumour centre: high-cellularity core
                            → Grade, necrosis, mucinous component

KEY FIXES vs original:
  - TISSUE_THR lowered to 0.25 for Tier 1 (invasive front has fat/stroma mixed in)
  - Tumour boundary detected via gradient of tissue density map
  - Grid cell halved for finer spatial resolution
  - Patches saved with tier metadata in filename for debugging
"""

import pylibCZIrw.czi as pyczi
import numpy as np
from PIL import Image
from pathlib import Path
from tqdm import tqdm
from scipy.ndimage import gaussian_filter, sobel
import json

# ── Config ─────────────────────────────────────────────────────────────────────
PATCH_PX      = 512         # output patch size in pixels
TARGET_MPP    = 0.5         # ~20x effective magnification
NATIVE_MPP    = 0.1112      # SurGen CZI scan resolution (confirm this for your scanner)
ZOOM          = NATIVE_MPP / TARGET_MPP    # 0.2224 — downsample factor

N_PATCHES     = 6           # total patches per slide (safe for 6GB VRAM)
                             # Tier 1: 3 patches, Tier 2: 2 patches, Tier 3: 1 patch

OV_ZOOM       = 0.02        # overview zoom (~2%)
GRID_CELL     = 16          # overview pixels per grid cell (was 32 — finer now)

# Tissue fraction thresholds per tier
THR_CENTRE    = 0.60        # tumour centre: dense tissue
THR_INTERFACE = 0.35        # tumour-stroma interface: mixed
THR_FRONT     = 0.18        # invasive front: tumour + fat + stroma mixed

MIN_DIST_MULT = 2.5         # min_dist = patch_native_size * this (was 3 — slightly tighter)


def tissue_mask(patch_arr: np.ndarray) -> np.ndarray:
    """
    Returns boolean mask: True = tissue pixel.
    Excludes white glass (>220) and black padding/artifacts (<15).
    Works on RGB uint8 arrays.
    """
    gray = patch_arr.astype(np.float32).mean(axis=2)
    return (gray > 15) & (gray < 220)


def tissue_score(patch_arr: np.ndarray) -> float:
    """Fraction of tissue pixels in a patch."""
    return tissue_mask(patch_arr).mean()


def build_tissue_density_map(overview: np.ndarray, cell: int) -> np.ndarray:
    """
    Build a 2D array of tissue density values at grid-cell resolution.
    Shape: (n_rows, n_cols) with values in [0, 1].
    """
    ov_h, ov_w = overview.shape[:2]
    n_rows = (ov_h - cell) // cell
    n_cols = (ov_w - cell) // cell
    density = np.zeros((n_rows, n_cols), dtype=np.float32)
    for r in range(n_rows):
        for c in range(n_cols):
            cell_patch = overview[r*cell:(r+1)*cell, c*cell:(c+1)*cell]
            density[r, c] = tissue_score(cell_patch)
    return density


def find_invasive_front_candidates(
    density_map: np.ndarray,
    bb_x: int, bb_y: int,
    ov_zoom: float, cell: int,
    zoom: float, patch_px: int
) -> list[tuple[float, int, int]]:
    """
    Detect the invasive front via gradient of the tissue density map.
    High gradient = rapid transition from tumour (dense) to stroma/fat (sparse).
    This is morphologically where the invasive front lives.

    Returns: list of (gradient_magnitude, full_res_x, full_res_y)
    """
    # Smooth density map, then compute gradient magnitude
    smooth = gaussian_filter(density_map.astype(np.float64), sigma=1.5)
    grad_x = sobel(smooth, axis=1)
    grad_y = sobel(smooth, axis=0)
    grad_mag = np.hypot(grad_x, grad_y)

    # Only accept cells where density is in "transition zone" [0.15, 0.65]
    # Pure fat (very low density) or pure tumour centre (high density) = not front
    transition_mask = (density_map > 0.15) & (density_map < 0.65)
    grad_mag = grad_mag * transition_mask

    candidates = []
    n_rows, n_cols = density_map.shape
    for r in range(n_rows):
        for c in range(n_cols):
            if grad_mag[r, c] > 0.01:  # any meaningful gradient
                # Map grid cell back to full-res coordinates
                fx = bb_x + int((c * cell) / ov_zoom)
                fy = bb_y + int((r * cell) / ov_zoom)
                candidates.append((float(grad_mag[r, c]), fx, fy))

    candidates.sort(reverse=True)
    return candidates


def find_centre_candidates(
    density_map: np.ndarray,
    bb_x: int, bb_y: int,
    ov_zoom: float, cell: int,
    thr: float
) -> list[tuple[float, int, int]]:
    """
    High-density cells = tumour centre. Used for Tier 2 and Tier 3 sampling.
    Returns: list of (density_score, full_res_x, full_res_y)
    """
    candidates = []
    n_rows, n_cols = density_map.shape
    for r in range(n_rows):
        for c in range(n_cols):
            if density_map[r, c] > thr:
                fx = bb_x + int((c * cell) / ov_zoom)
                fy = bb_y + int((r * cell) / ov_zoom)
                candidates.append((float(density_map[r, c]), fx, fy))
    candidates.sort(reverse=True)
    return candidates


def select_spaced(
    candidates: list[tuple[float, int, int]],
    n: int,
    min_dist: int,
    already_selected: list[tuple[float, int, int]] | None = None
) -> list[tuple[float, int, int]]:
    """
    Pick up to n candidates that are spatially spread out.
    already_selected: existing picks to also avoid overlapping.
    """
    selected = list(already_selected or [])
    new_picks = []
    for score, fx, fy in candidates:
        if len(new_picks) >= n:
            break
        if all(abs(fx - sx) > min_dist or abs(fy - sy) > min_dist
               for _, sx, sy in selected):
            selected.append((score, fx, fy))
            new_picks.append((score, fx, fy))
    return new_picks


def read_patch(czi, fx: int, fy: int, native_size: int, zoom: float, patch_px: int) -> Image.Image | None:
    """
    Read a single patch from the CZI file, convert to 8-bit RGB PIL Image.
    Returns None if the patch is unreadable or mostly black/white.
    """
    try:
        region = czi.read(
            roi=(fx, fy, native_size, native_size),
            plane={"C": 0},
            zoom=zoom
        )
        arr = np.clip(region[:, :, :3], 0, 255).astype(np.uint8)
        # Sanity check — reject if actual tissue content is too low
        if tissue_score(arr) < 0.10:
            return None
        img = Image.fromarray(arr)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = img.resize((patch_px, patch_px), Image.LANCZOS)
        return img
    except Exception:
        return None


def extract(czi_path: str | Path, out_dir: str | Path, n: int = N_PATCHES) -> list[str]:
    """
    Extract n patches from a CZI WSI using 3-tier anatomical sampling.

    Tier 1 (invasive front)  — 50% of n
    Tier 2 (tumour-stroma)   — 30% of n
    Tier 3 (tumour centre)   — 20% of n

    Returns list of saved patch file paths.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Tier allocation
    n_front     = max(1, round(n * 0.50))   # e.g. 3 for n=6
    n_interface = max(1, round(n * 0.30))   # e.g. 2 for n=6
    n_centre    = max(1, n - n_front - n_interface)  # e.g. 1 for n=6

    native_size = int(PATCH_PX / ZOOM)
    min_dist    = int(native_size * MIN_DIST_MULT)

    saved = []

    with pyczi.open_czi(str(czi_path)) as czi:
        bb = czi.total_bounding_rectangle
        W, H = bb.w, bb.h

        # ── Overview image ────────────────────────────────────────────────────
        overview_raw = czi.read(
            roi=(bb.x, bb.y, W, H),
            plane={"C": 0},
            zoom=OV_ZOOM
        )
        ov = np.clip(overview_raw[:, :, :3], 0, 255).astype(np.uint8)

        # ── Build density map ─────────────────────────────────────────────────
        density_map = build_tissue_density_map(ov, GRID_CELL)

        # ── Tier 1 — Invasive front ───────────────────────────────────────────
        front_candidates = find_invasive_front_candidates(
            density_map, bb.x, bb.y, OV_ZOOM, GRID_CELL, ZOOM, PATCH_PX
        )
        all_selected = []
        tier1_picks = select_spaced(front_candidates, n_front, min_dist, all_selected)
        all_selected.extend(tier1_picks)

        patch_idx = 0
        for i, (score, fx, fy) in enumerate(tier1_picks):
            img = read_patch(czi, fx, fy, native_size, ZOOM, PATCH_PX)
            if img is not None:
                fname = out_dir / f"p{patch_idx:02d}_front.png"
                img.save(fname)
                saved.append(str(fname))
                patch_idx += 1

        # ── Tier 2 — Tumour-stroma interface ──────────────────────────────────
        interface_candidates = find_centre_candidates(
            density_map, bb.x, bb.y, OV_ZOOM, GRID_CELL, thr=THR_INTERFACE
        )
        # Filter to mid-range density (0.35–0.65) only — avoid pure centre
        interface_candidates = [
            (s, fx, fy) for (s, fx, fy) in interface_candidates
            if s < 0.65
        ]
        tier2_picks = select_spaced(interface_candidates, n_interface, min_dist, all_selected)
        all_selected.extend(tier2_picks)

        for i, (score, fx, fy) in enumerate(tier2_picks):
            img = read_patch(czi, fx, fy, native_size, ZOOM, PATCH_PX)
            if img is not None:
                fname = out_dir / f"p{patch_idx:02d}_interface.png"
                img.save(fname)
                saved.append(str(fname))
                patch_idx += 1

        # ── Tier 3 — Tumour centre ────────────────────────────────────────────
        centre_candidates = find_centre_candidates(
            density_map, bb.x, bb.y, OV_ZOOM, GRID_CELL, thr=THR_CENTRE
        )
        tier3_picks = select_spaced(centre_candidates, n_centre, min_dist, all_selected)
        all_selected.extend(tier3_picks)

        for i, (score, fx, fy) in enumerate(tier3_picks):
            img = read_patch(czi, fx, fy, native_size, ZOOM, PATCH_PX)
            if img is not None:
                fname = out_dir / f"p{patch_idx:02d}_centre.png"
                img.save(fname)
                saved.append(str(fname))
                patch_idx += 1

        # ── Fallback: fill remaining slots with any tissue ────────────────────
        if len(saved) < n:
            fallback_candidates = find_centre_candidates(
                density_map, bb.x, bb.y, OV_ZOOM, GRID_CELL, thr=0.20
            )
            fallback_picks = select_spaced(
                fallback_candidates, n - len(saved), min_dist, all_selected
            )
            for score, fx, fy in fallback_picks:
                img = read_patch(czi, fx, fy, native_size, ZOOM, PATCH_PX)
                if img is not None:
                    fname = out_dir / f"p{patch_idx:02d}_fallback.png"
                    img.save(fname)
                    saved.append(str(fname))
                    patch_idx += 1

    return saved


# ── Batch run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    CZI_DIR    = Path(r"G:\My Drive\Colorectal Cancer\Surgen\SR386\SR386_WSIs")
    OUTPUT_DIR = Path("./paatchees")
    LOG        = []

    czi_files = list(sorted(CZI_DIR.glob("*.czi")))
    czi_files = czi_files[:10]  # process only the first 10 files
    for czi_file in tqdm(czi_files):
        case_id = czi_file.stem
        try:
            patches = extract(czi_file, OUTPUT_DIR / case_id, n=N_PATCHES)
            LOG.append({
                "case_id": case_id,
                "patches": patches,
                "count": len(patches),
                "tiers": {
                    "front":     [p for p in patches if "front"     in p],
                    "interface": [p for p in patches if "interface" in p],
                    "centre":    [p for p in patches if "centre"    in p],
                    "fallback":  [p for p in patches if "fallback"  in p],
                }
            })
        except Exception as e:
            print(f"\n[ERROR] Skipping {case_id}: {e}")
            continue

    with open("patch_index.json", "w") as f:
        json.dump(LOG, f, indent=2)

    print(f"Done. {len(LOG)} cases processed.")