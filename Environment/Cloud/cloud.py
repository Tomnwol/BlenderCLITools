"""
cloud_generator.py
------------------
Génère des nuages low-poly sous forme de fichiers JSON.
Chaque nuage = un ensemble de sphères avec position et scale par axe.

Usage:
    python cloud_generator.py                  # 5 nuages aléatoires
    python cloud_generator.py --count 10       # 10 nuages aléatoires
    python cloud_generator.py --seed 42        # seed fixe (reproductible)
    python cloud_generator.py --count 3 --seed 7 --out ./clouds
    python cloud_generator.py --single cloud_042.json  # fichiers séparés
"""

import json
import math
import random
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Paramètres de génération (tweak ici)
# ---------------------------------------------------------------------------

SPHERE_COUNT_MIN = 4
SPHERE_COUNT_MAX = 14

# Scale de chaque sphère par axe (unités Blender)
SCALE_X_RANGE = (0.5, 2.0)
SCALE_Y_RANGE = (0.4, 1.6)
SCALE_Z_RANGE = (0.3, 1.2)

# Spread de position autour du centre (0,0,0)
POS_X_RANGE   = (-3.0, 3.0)
POS_Y_RANGE   = (-1.5, 1.5)
POS_Z_RANGE   = (-0.5, 0.8)   # nuage légèrement plat sur Z


# ---------------------------------------------------------------------------
# Génération d'un nuage
# ---------------------------------------------------------------------------

def generate_cloud(cloud_id: str, rng: random.Random) -> dict:
    """Génère un nuage : liste de sphères avec position et scale."""
    n_spheres = rng.randint(SPHERE_COUNT_MIN, SPHERE_COUNT_MAX)

    spheres = []
    for _ in range(n_spheres):
        sphere = {
            "position": {
                "x": round(rng.uniform(*POS_X_RANGE), 4),
                "y": round(rng.uniform(*POS_Y_RANGE), 4),
                "z": round(rng.uniform(*POS_Z_RANGE), 4),
            },
            "scale": {
                "x": round(rng.uniform(*SCALE_X_RANGE), 4),
                "y": round(rng.uniform(*SCALE_Y_RANGE), 4),
                "z": round(rng.uniform(*SCALE_Z_RANGE), 4),
            }
        }
        spheres.append(sphere)

    return {
        "cloud_id": cloud_id,
        "seed": rng.getstate()[1][0],   # premier int de l'état = seed courant
        "sphere_count": n_spheres,
        "spheres": spheres,
    }


# ---------------------------------------------------------------------------
# Sauvegarde
# ---------------------------------------------------------------------------

def save_individual(clouds: list[dict], out_dir: Path):
    """Un fichier JSON par nuage."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for cloud in clouds:
        path = out_dir / f"{cloud['cloud_id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cloud, f, indent=2)
        print(f"  Saved: {path}")


def save_batch(clouds: list[dict], out_path: Path):
    """Tous les nuages dans un seul fichier JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    batch = {
        "cloud_count": len(clouds),
        "clouds": clouds,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2)
    print(f"  Saved batch: {out_path}  ({len(clouds)} clouds)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Low-poly cloud JSON generator")
    parser.add_argument("--count",  type=int,   default=5,            help="Nombre de nuages à générer")
    parser.add_argument("--seed",   type=int,   default=None,         help="Seed aléatoire (optionnel)")
    parser.add_argument("--out",    type=str,   default="./clouds",   help="Dossier de sortie")
    parser.add_argument("--batch",  action="store_true",              help="Un seul fichier JSON (batch) au lieu d'un par nuage")
    parser.add_argument("--prefix", type=str,   default="cloud",      help="Préfixe des IDs (ex: 'cloud' → cloud_001)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Seed
    seed = args.seed if args.seed is not None else random.randint(0, 2**31)
    rng = random.Random(seed)
    print(f"\n🌥  Generating {args.count} cloud(s) | seed={seed}\n")

    # Génération
    pad = math.ceil(math.log10(args.count + 1))
    clouds = []
    for i in range(args.count):
        cloud_id = f"{args.prefix}_{str(i + 1).zfill(pad)}"
        # Seed individuel : dérivé du seed global + index → reproductible
        cloud_seed = rng.randint(0, 2**31)
        cloud_rng  = random.Random(cloud_seed)
        cloud = generate_cloud(cloud_id, cloud_rng)
        cloud["seed"] = cloud_seed   # écrase avec le seed propre au nuage
        clouds.append(cloud)

    # Sauvegarde
    out = Path(args.out)
    if args.batch:
        save_batch(clouds, out / "clouds_batch.json")
    else:
        save_individual(clouds, out)

    print(f"\n✅  Done.")


if __name__ == "__main__":
    main()
