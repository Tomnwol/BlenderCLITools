"""
generators/rocks/rock_generator.py
----------------------------------
Generateur de rochers low-poly type Deep Rock Galactic.
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.base_generator import BaseGenerator
from shared.io_utils import log


# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------

WIDTH_RANGE = (0.5, 4.0)
DEPTH_RANGE = (0.5, 4.0)
HEIGHT_RANGE = (0.5, 3.0)

ROUGHNESS_RANGE = (0.2, 0.9)

SUBDIVISION_MIN = 0
SUBDIVISION_MAX = 1

DEFAULT_TMP_DIR = "tmp/rock"


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class RockGenerator(BaseGenerator):

    asset_type = "rock"

    def generate_one(self, asset_id: str, seed: int) -> dict:

        rng = random.Random(seed)

        return {
            **self._base_fields(asset_id, seed),

            "width": round(
                rng.uniform(*WIDTH_RANGE),
                4
            ),

            "depth": round(
                rng.uniform(*DEPTH_RANGE),
                4
            ),

            "height": round(
                rng.uniform(*HEIGHT_RANGE),
                4
            ),

            "roughness": round(
                rng.uniform(*ROUGHNESS_RANGE),
                4
            ),

            "subdivisions": rng.randint(
                SUBDIVISION_MIN,
                SUBDIVISION_MAX
            ),

            # garde une liste pour rester proche de ton archi
            "chunks": [
                {
                    "dummy": True
                }
            ]
        }

    def validate(self, data: dict) -> bool:

        required = {
            "asset_id",
            "asset_type",
            "seed",
            "width",
            "depth",
            "height",
            "roughness",
            "subdivisions",
            "chunks"
        }

        if not required.issubset(data.keys()):
            log(
                f"Missing keys: {required - data.keys()}",
                "WARN"
            )
            return False

        return True


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

_generator = RockGenerator()


def run(
    count: int,
    seed: int | None,
    out_dir: str,
    prefix: str | None = None
):
    return _generator.run(
        count=count,
        seed=seed,
        out_dir=out_dir,
        prefix=prefix
    )