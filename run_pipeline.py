"""
run_pipeline.py
---------------
Point d'entrée unique. Orchestre :
    1. Génération des JSON  (generators/clouds/cloud_generator.py)
    2. Rendu Blender pour chaque JSON  (renderers/clouds/cloud_renderer.py)

Lancer depuis la RACINE du projet :

    python run_pipeline.py                           # 3 nuages, seed aléatoire
    python run_pipeline.py --count 10 --seed 42     # 10 nuages reproductibles
    python run_pipeline.py --keep-tmp               # garde les JSON dans /tmp
    python run_pipeline.py --blender /opt/blender/blender  # chemin custom
"""

import argparse
import subprocess
from pathlib import Path

from shared.io_utils import ensure_dir, log
from generators.clouds.cloud_generator import run as generate_clouds

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PROJECT_ROOT    = Path(__file__).resolve().parent
RENDERER_SCRIPT = PROJECT_ROOT / "renderers" / "clouds" / "cloud_renderer.py"
OUTPUT_DIR      = PROJECT_ROOT / "renderers" / "clouds" / "output"
TMP_DIR         = str(PROJECT_ROOT / "tmp" / "clouds")


# ---------------------------------------------------------------------------
# Lancement Blender pour un JSON
# ---------------------------------------------------------------------------

def render_cloud(json_path: Path, out_dir: Path, blender_bin: str = "blender") -> bool:
    renderer_abs = str(RENDERER_SCRIPT.resolve())
    json_abs     = str(json_path.resolve())
    out_abs      = str(out_dir.resolve())

    if not RENDERER_SCRIPT.exists():
        log(f"Renderer script not found: {renderer_abs}", "ERROR")
        return False

    cmd = [
        blender_bin,
        "--background",
        "--python", renderer_abs,
        "--",
        "--json", json_abs,
        "--out",  out_abs,
    ]

    log(f"Rendering {json_path.stem} ...")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # encoding UTF-8 + ignore les caractères non décodables (emojis, etc.)
        encoding="utf-8",
        errors="replace",
    )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if stdout.strip():
        print("  [blender stdout]")
        for line in stdout.splitlines():
            print(f"    {line}")

    if stderr.strip():
        print("  [blender stderr]")
        for line in stderr.splitlines()[-40:]:
            print(f"    {line}")

    if result.returncode != 0:
        log(f"Blender exited with code {result.returncode} on {json_path.stem}", "ERROR")
        return False

    glb = out_dir / f"{json_path.stem}.glb"
    png = out_dir / f"{json_path.stem}.png"
    if not glb.exists() or not png.exists():
        log(f"Output files missing for {json_path.stem} (glb={glb.exists()}, png={png.exists()})", "ERROR")
        return False

    return True


# ---------------------------------------------------------------------------
# Pipeline principale
# ---------------------------------------------------------------------------

def run_pipeline(count: int, seed: int | None, out_dir: Path, blender_bin: str, keep_tmp: bool):
    ensure_dir(out_dir)

    log(f"Step 1/2 -- Generating {count} cloud(s)  [seed={seed or 'random'}]")
    json_files = generate_clouds(count=count, seed=seed, out_dir=TMP_DIR)
    log(f"{len(json_files)} JSON(s) written to {TMP_DIR}", "OK")

    log(f"Step 2/2 -- Rendering with Blender  [bin='{blender_bin}']")
    success, failed = 0, 0

    for json_path in json_files:
        ok = render_cloud(json_path, out_dir, blender_bin)
        if ok:
            success += 1
        else:
            failed += 1

    if not keep_tmp:
        for f in json_files:
            f.unlink(missing_ok=True)
        log(f"Cleaned up {TMP_DIR}")

    print()
    log(f"Pipeline complete -- {success} rendered, {failed} failed",
        "OK" if failed == 0 else "WARN")
    log(f"Outputs -> {out_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="Low-poly cloud pipeline")
    p.add_argument("--count",    type=int, default=3)
    p.add_argument("--seed",     type=int, default=None)
    p.add_argument("--out",      type=str, default=str(OUTPUT_DIR))
    p.add_argument("--blender",  type=str, default="blender")
    p.add_argument("--keep-tmp", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline(
        count       = args.count,
        seed        = args.seed,
        out_dir     = Path(args.out),
        blender_bin = args.blender,
        keep_tmp    = args.keep_tmp,
    )