"""
run_pipeline.py
---------------
Point d'entree unique. Orchestre :
    1. Generation des JSON  (via generator_script dans registry.py)
    2. Rendu Blender en parallele (via renderer_script dans registry.py)
    3. Cache : skip les assets deja rendus avec le meme seed

Lancer depuis la RACINE du projet :

    python run_pipeline.py --type cloud --count 5
    python run_pipeline.py --type cloud --count 10 --seed 42
    python run_pipeline.py --type cloud --count 20 --workers 4
    python run_pipeline.py --types
    python run_pipeline.py --keep-tmp
    python run_pipeline.py --force          # ignore le cache, re-render tout
    python run_pipeline.py --cache-info     # affiche le contenu du cache
    python run_pipeline.py --blender "C:/path/to/blender.exe"
"""

# Disable __pycache__
import sys
sys.dont_write_bytecode = True

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import registry
import helpers
from shared.io_utils import ensure_dir, log
from shared import cache


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
    force: bool,
):
    config           = registry.get(asset_type)
    generator_script = Path(config["generator_script"])
    renderer_script  = Path(config["renderer_script"])
    tmp_dir          = Path(config["tmp_dir"])
    out_dir          = Path(config["out_dir"])

    ensure_dir(out_dir)
    ensure_dir(tmp_dir)

    # ── Step 1 : generation JSON ───────────────────────────────────────────
    log(f"Step 1/2 -- Generating {count} {asset_type}(s)  [seed={seed or 'random'}]")
    generator  = helpers.load_module(generator_script)
    json_files = generator.run(count=count, seed=seed, out_dir=str(tmp_dir))
    log(f"{len(json_files)} JSON(s) written to {tmp_dir}", "OK")

    # ── Step 2 : rendu Blender avec cache ─────────────────────────────────
    # Lire les seeds des JSON générés pour vérifier le cache
    from shared.io_utils import load_json

    to_render  = []
    skipped    = 0

    for json_path in json_files:
        data     = load_json(json_path)
        asset_id = data["asset_id"]
        jseed    = data["seed"]

        if not force and cache.is_cached(out_dir, asset_id, jseed):
            log(f"[{asset_id}] skipped (cached)", "INFO")
            skipped += 1
        else:
            to_render.append(json_path)

    effective_workers = min(workers, len(to_render)) if to_render else 1
    log(f"Step 2/2 -- Rendering {len(to_render)} asset(s)  "
        f"[skipped={skipped}, workers={effective_workers}]")

    success, failed = 0, 0

    if to_render:
        futures = {}
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            for json_path in to_render:
                future = executor.submit(render_one, json_path, out_dir, renderer_script, blender_bin)
                futures[future] = json_path

            for future in as_completed(futures):
                json_path        = futures[future]
                asset_id, ok, msg = future.result()

                if ok:
                    success += 1
                    log(f"[{asset_id}] done", "OK")
                    # Enregistrer dans le cache
                    data = load_json(json_path)
                    cache.register(out_dir, asset_id, data["seed"], asset_type)
                else:
                    failed += 1
                    log(f"[{asset_id}] FAILED", "ERROR")

                if msg.strip():
                    print(msg)

    # ── Nettoyage tmp ──────────────────────────────────────────────────────
    if not keep_tmp:
        for f in json_files:
            f.unlink(missing_ok=True)
        log(f"Cleaned up {tmp_dir}")

    # ── Résumé ─────────────────────────────────────────────────────────────
    print()
    log(f"Pipeline complete -- {success} rendered, {skipped} skipped, {failed} failed",
        "OK" if failed == 0 else "WARN")
    log(f"Outputs -> {out_dir}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = helpers._parse_args()

    if hasattr(args, "cache_info") and args.cache_info:
        config  = registry.get(args.type)
        out_dir = Path(config["out_dir"])
        print(cache.summary(out_dir))
    else:
        run_pipeline(
            asset_type  = args.type,
            count       = args.count,
            seed        = args.seed,
            blender_bin = args.blender,
            keep_tmp    = args.keep_tmp,
            workers     = args.workers,
            force       = args.force,
        )