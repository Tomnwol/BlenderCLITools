"""
shared/cache.py
---------------
Cache des assets rendus. Un fichier .cache.json par dossier output.

Fonctions principales :
    load(out_dir)                        -> dict
    is_cached(out_dir, asset_id, seed)   -> bool
    register(out_dir, asset_id, seed, asset_type, glb_path, png_path)
    invalidate(out_dir, asset_id)

Format du .cache.json :
    {
      "cloud_01": {
        "asset_type": "cloud",
        "seed":       478163327,
        "glb":        "renderers/cloud/output/cloud_01.glb",
        "png":        "renderers/cloud/output/cloud_01.png"
      },
      ...
    }
"""

from pathlib import Path
from shared.io_utils import load_json, save_json, log

CACHE_FILENAME = ".cache.json"


# ---------------------------------------------------------------------------
# Lecture / écriture
# ---------------------------------------------------------------------------

def _cache_path(out_dir: Path) -> Path:
    return out_dir / CACHE_FILENAME


def load(out_dir: Path) -> dict:
    """Charge le cache. Retourne un dict vide si inexistant."""
    path = _cache_path(out_dir)
    try:
        return load_json(path)
    except FileNotFoundError:
        return {}


def _save(out_dir: Path, cache: dict):
    save_json(cache, _cache_path(out_dir))


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def is_cached(out_dir: Path, asset_id: str, seed: int) -> bool:
    """
    Retourne True si l'asset est dans le cache ET que :
      - le seed correspond (même paramètres de génération)
      - le GLB et le PNG existent encore sur le disque
    """
    cache = load(out_dir)
    entry = cache.get(asset_id)

    if entry is None:
        return False

    if entry.get("seed") != seed:
        log(f"Cache miss [{asset_id}] : seed changed ({entry.get('seed')} -> {seed})", "INFO")
        return False

    glb_exists = Path(entry["glb"]).exists()
    png_exists = Path(entry["png"]).exists()

    if not glb_exists or not png_exists:
        log(f"Cache miss [{asset_id}] : files missing on disk (glb={glb_exists}, png={png_exists})", "INFO")
        return False

    return True


def get_entry(out_dir: Path, asset_id: str) -> dict | None:
    """Retourne l'entrée complète d'un asset, ou None."""
    return load(out_dir).get(asset_id)


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------

def register(out_dir: Path, asset_id: str, seed: int, asset_type: str):
    """
    Enregistre un asset rendu dans le cache.
    Appelé par run_pipeline.py après un render réussi.
    """
    cache = load(out_dir)
    cache[asset_id] = {
        "asset_type": asset_type,
        "seed":       seed,
        "glb":        str((out_dir / f"{asset_id}.glb").resolve()),
        "png":        str((out_dir / f"{asset_id}.png").resolve()),
    }
    _save(out_dir, cache)
    log(f"Cached [{asset_id}]", "OK")


def invalidate(out_dir: Path, asset_id: str):
    """Supprime un asset du cache (sans supprimer les fichiers)."""
    cache = load(out_dir)
    if asset_id in cache:
        del cache[asset_id]
        _save(out_dir, cache)
        log(f"Invalidated [{asset_id}]", "INFO")


def invalidate_all(out_dir: Path):
    """Vide entièrement le cache d'un dossier output."""
    _save(out_dir, {})
    log(f"Cache cleared for {out_dir}", "INFO")


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------

def list_cached(out_dir: Path) -> list[str]:
    """Retourne la liste des asset_id en cache."""
    return list(load(out_dir).keys())


def summary(out_dir: Path) -> str:
    """Résumé lisible du cache."""
    cache = load(out_dir)
    if not cache:
        return "Cache empty."
    lines = [f"  {aid} | type={e['asset_type']} | seed={e['seed']}" for aid, e in cache.items()]
    return f"Cache ({len(cache)} entries):\n" + "\n".join(lines)