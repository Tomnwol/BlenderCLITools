"""
generators/clouds/cloud_generator.py
-------------------------------------
Génère des nuages low-poly sous forme de fichiers JSON dans /tmp/clouds/.
Appelé par run_pipeline.py ou directement en CLI.

Usage direct:
    python generators/clouds/cloud_generator.py
    python generators/clouds/cloud_generator.py --count 10 --seed 42
    python generators/clouds/cloud_generator.py --count 5 --out /tmp/my_clouds
"""

import sys
import math
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.io_utils import save_json, ensure_dir, log


# ---------------------------------------------------------------------------
# Paramètres de génération  (tweak ici)
# ---------------------------------------------------------------------------

SPHERE_COUNT_MIN = 4
SPHERE_COUNT_MAX = 14

SCALE_X_RANGE = (0.5, 2.0)
SCALE_Y_RANGE = (0.4, 1.6)
SCALE_Z_RANGE = (0.3, 1.2)

POS_X_RANGE   = (-3.0,  3.0)
POS_Y_RANGE   = (-1.5,  1.5)
POS_Z_RANGE   = (-0.3,  0.8)  # nuage légèrement aplati sur Z

DEFAULT_TMP_DIR = "/tmp/clouds"


# ---------------------------------------------------------------------------
# Génération
# ---------------------------------------------------------------------------

def generate_cloud(cloud_id: str, seed: int) -> dict:
    """Génère un nuage reproductible à partir d'un seed."""
    rng = random.Random(seed)
    n   = rng.randint(SPHERE_COUNT_MIN, SPHERE_COUNT_MAX)

    spheres = [
        {
            "position": {
                "x": round(rng.uniform(*POS_X_RANGE), 4),
                "y": round(rng.uniform(*POS_Y_RANGE), 4),
                "z": round(rng.uniform(*POS_Z_RANGE), 4),
            },
            "scale": {
                "x": round(rng.uniform(*SCALE_X_RANGE), 4),
                "y": round(rng.uniform(*SCALE_Y_RANGE), 4),
                "z": round(rng.uniform(*SCALE_Z_RANGE), 4),
            },
        }
        for _ in range(n)
    ]

    return {
        "cloud_id":     cloud_id,
        "seed":         seed,
        "sphere_count": n,
        "spheres":      spheres,
    }


def generate_batch(count: int, global_seed: int | None = None, prefix: str = "cloud") -> list[dict]:
    """Génère `count` nuages avec des seeds dérivés d'un seed global."""
    master_seed = global_seed if global_seed is not None else random.randint(0, 2**31)
    master_rng  = random.Random(master_seed)
    pad = max(2, math.ceil(math.log10(count + 1)))

    clouds = []
    for i in range(count):
        cloud_id   = f"{prefix}_{str(i + 1).zfill(pad)}"
        cloud_seed = master_rng.randint(0, 2**31)
        clouds.append(generate_cloud(cloud_id, cloud_seed))

    return clouds


# ---------------------------------------------------------------------------
# Entrée principale (appelée par run_pipeline.py)
# ---------------------------------------------------------------------------

def run(count: int, seed: int | None, out_dir: str, prefix: str = "cloud") -> list[Path]:
    """
    Génère `count` nuages et sauvegarde les JSON dans out_dir.
    Retourne la liste des fichiers créés.
    """
    out = Path(out_dir)
    ensure_dir(out)

    clouds = generate_batch(count, seed, prefix)
    paths  = []

    for cloud in clouds:
        path = save_json(cloud, out / f"{cloud['cloud_id']}.json")
        log(f"Generated {cloud['cloud_id']} ({cloud['sphere_count']} spheres) → {path}", "OK")
        paths.append(path)

    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="Cloud JSON generator")
    p.add_argument("--count",  type=int, default=5)
    p.add_argument("--seed",   type=int, default=None)
    p.add_argument("--out",    type=str, default=DEFAULT_TMP_DIR)
    p.add_argument("--prefix", type=str, default="cloud")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    files = run(args.count, args.seed, args.out, args.prefix)
    log(f"{len(files)} cloud(s) saved to {args.out}", "INFO")