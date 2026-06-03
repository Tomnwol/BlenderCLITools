"""
run_pipeline.py
---------------
Point d'entree unique. Orchestre :
    1. Generation des JSON  (via generator_script dans registry.py)
    2. Rendu Blender en parallele (via renderer_script dans registry.py)

Lancer depuis la RACINE du projet :

    python run_pipeline.py --type cloud --count 5
    python run_pipeline.py --type cloud --count 10 --seed 42
    python run_pipeline.py --type cloud --count 20 --workers 4
    python run_pipeline.py --types
    python run_pipeline.py --keep-tmp
    python run_pipeline.py --blender "C:/path/to/blender.exe"
"""

import argparse
import importlib.util
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import registry
from shared.io_utils import ensure_dir, log


# ---------------------------------------------------------------------------
# Chargement d'un module Python depuis un chemin fichier
# ---------------------------------------------------------------------------

def load_module(path: Path):
    """Charge un module Python depuis un chemin absolu."""
    spec   = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Rendu d'un seul asset (tourne dans un thread)
# ---------------------------------------------------------------------------

def render_one(json_path: Path, out_dir: Path, renderer_script: Path, blender_bin: str) -> tuple[str, bool, str]:
    asset_id     = json_path.stem
    renderer_abs = str(renderer_script.resolve())
    json_abs     = str(json_path.resolve())
    out_abs      = str(out_dir.resolve())

    if not renderer_script.exists():
        return asset_id, False, f"Renderer script not found: {renderer_abs}"

    cmd = [
        blender_bin,
        "--background",
        "--python", renderer_abs,
        "--",
        "--json", json_abs,
        "--out",  out_abs,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    output_summary = ""
    if stdout.strip():
        output_summary += "[stdout]\n" + "\n".join(f"    {l}" for l in stdout.splitlines()) + "\n"
    if stderr.strip():
        output_summary += "[stderr]\n" + "\n".join(f"    {l}" for l in stderr.splitlines()) + "\n"

    if result.returncode != 0:
        return asset_id, False, f"Blender exited code {result.returncode}\n{output_summary}"

    glb = out_dir / f"{asset_id}.glb"
    png = out_dir / f"{asset_id}.png"
    if not glb.exists() or not png.exists():
        return asset_id, False, f"Output files missing (glb={glb.exists()}, png={png.exists()})\n{output_summary}"

    return asset_id, True, output_summary


# ---------------------------------------------------------------------------
# Pipeline principale
# ---------------------------------------------------------------------------

def run_pipeline(
    asset_type: str,
    count: int,
    seed: int | None,
    blender_bin: str,
    keep_tmp: bool,
    workers: int,
):
    config          = registry.get(asset_type)
    generator_script = Path(config["generator_script"])
    renderer_script  = Path(config["renderer_script"])
    tmp_dir          = Path(config["tmp_dir"])
    out_dir          = Path(config["out_dir"])

    ensure_dir(out_dir)
    ensure_dir(tmp_dir)

    # Etape 1 : generation JSON
    log(f"Step 1/2 -- Generating {count} {asset_type}(s)  [seed={seed or 'random'}]")
    generator  = load_module(generator_script)
    json_files = generator.run(count=count, seed=seed, out_dir=str(tmp_dir))
    log(f"{len(json_files)} JSON(s) written to {tmp_dir}", "OK")

    # Etape 2 : rendu Blender en parallele
    effective_workers = min(workers, len(json_files))
    log(f"Step 2/2 -- Rendering with Blender  [workers={effective_workers}, bin='{blender_bin}']")

    success, failed = 0, 0
    futures = {}

    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        for json_path in json_files:
            future = executor.submit(render_one, json_path, out_dir, renderer_script, blender_bin)
            futures[future] = json_path.stem

        for future in as_completed(futures):
            asset_id, ok, msg = future.result()
            if ok:
                success += 1
                log(f"[{asset_id}] done", "OK")
            else:
                failed += 1
                log(f"[{asset_id}] FAILED", "ERROR")
            if msg.strip():
                print(msg)

    # Nettoyage tmp
    if not keep_tmp:
        for f in json_files:
            f.unlink(missing_ok=True)
        log(f"Cleaned up {tmp_dir}")

    print()
    log(f"Pipeline complete -- {success} rendered, {failed} failed",
        "OK" if failed == 0 else "WARN")
    log(f"Outputs -> {out_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="Asset pipeline")
    p.add_argument("--type",     type=str, default="cloud",
                   help=f"Type d'asset. Disponibles : {registry.list_types()}")
    p.add_argument("--types",    action="store_true")
    p.add_argument("--count",    type=int, default=3)
    p.add_argument("--seed",     type=int, default=None)
    p.add_argument("--workers",  type=int, default=2)
    p.add_argument("--blender",  type=str, default="blender")
    p.add_argument("--keep-tmp", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if args.types:
        print("Available asset types:")
        for t in registry.list_types():
            print(f"  - {t}")
    else:
        run_pipeline(
            asset_type  = args.type,
            count       = args.count,
            seed        = args.seed,
            blender_bin = args.blender,
            keep_tmp    = args.keep_tmp,
            workers     = args.workers,
        )