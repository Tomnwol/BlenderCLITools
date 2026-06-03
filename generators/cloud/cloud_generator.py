"""
generators/clouds/cloud_generator.py
-------------------------------------
Generateur de nuages low-poly. Herite de BaseGenerator.

Usage direct:
    python generators/clouds/cloud_generator.py --count 5 --seed 42
    python generators/clouds/cloud_generator.py --count 5 --out C:/tmp/clouds
"""

import sys
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.base_generator import BaseGenerator
from shared.io_utils import log


# ---------------------------------------------------------------------------
# Parametres de generation  (tweak ici)
# ---------------------------------------------------------------------------

SPHERE_COUNT_MIN = 4
SPHERE_COUNT_MAX = 14

SCALE_X_RANGE = (0.5, 2.0)
SCALE_Y_RANGE = (0.4, 1.6)
SCALE_Z_RANGE = (0.3, 1.2)

POS_X_RANGE   = (-3.0,  3.0)
POS_Y_RANGE   = (-1.5,  1.5)
POS_Z_RANGE   = (-0.3,  0.8)

DEFAULT_TMP_DIR = "tmp/clouds"


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

class CloudGenerator(BaseGenerator):

    asset_type = "cloud"

    def generate_one(self, asset_id: str, seed: int) -> dict:
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
            **self._base_fields(asset_id, seed),
            "sphere_count": n,
            "spheres":      spheres,
            "material": {
                "name":       f"{asset_id}_mat",
                "base_color": [0.2, 0.93, 0.2],   # blanc bleuté
                "roughness":  round(rng.uniform(0.7, 1.0), 3),
                "metallic":   0.0,
                "specular":   0.03,
                "alpha":      1.0,
            },
        }

    def validate(self, data: dict) -> bool:
        required = {"asset_id", "asset_type", "seed", "sphere_count", "spheres", "material"}
        if not required.issubset(data.keys()):
            log(f"Missing keys: {required - data.keys()}", "WARN")
            return False
        if not isinstance(data["spheres"], list) or len(data["spheres"]) == 0:
            log("'spheres' must be a non-empty list", "WARN")
            return False
        mat = data["material"]
        if not isinstance(mat.get("base_color"), list) or len(mat["base_color"]) != 3:
            log("material.base_color must be a list of 3 floats", "WARN")
            return False
        return True


# ---------------------------------------------------------------------------
# Fonction run() — interface attendue par run_pipeline.py
# ---------------------------------------------------------------------------

_generator = CloudGenerator()

def run(count: int, seed: int | None, out_dir: str, prefix: str | None = None) -> list[Path]:
    return _generator.run(count=count, seed=seed, out_dir=out_dir, prefix=prefix)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Cloud JSON generator")
    p.add_argument("--count",  type=int, default=5)
    p.add_argument("--seed",   type=int, default=None)
    p.add_argument("--out",    type=str, default=DEFAULT_TMP_DIR)
    p.add_argument("--prefix", type=str, default=None)
    args = p.parse_args()

    files = run(args.count, args.seed, args.out, args.prefix)
    log(f"{len(files)} cloud(s) saved to {args.out}", "OK")