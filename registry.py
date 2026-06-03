"""
registry.py
-----------
Registre central des types d'assets.

Pour ajouter un nouvel asset (ex: "rock") :
    1. Créer generators/rocks/rock_generator.py  (avec une classe RockGenerator)
    2. Créer renderers/rocks/rock_renderer.py    (avec une classe RockRenderer)
    3. Ajouter "rock" dans ASSETS ci-dessous — c'est tout.

Les chemins sont dérivés automatiquement depuis le nom du type :
    generator  ->  generators/<type>/<type>_generator.py
    renderer   ->  renderers/<type>/<type>_renderer.py
    tmp_dir    ->  tmp/<type>/
    out_dir    ->  renderers/<type>/output/
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Seul endroit à modifier pour ajouter un asset
# ---------------------------------------------------------------------------

ASSETS = [
    "cloud",
    "rock",
    # "tree",
]


# ---------------------------------------------------------------------------
# Resolution automatique des chemins
# ---------------------------------------------------------------------------

def get(asset_type: str) -> dict:
    """Retourne la config complète d'un asset. Lève ValueError si inconnu."""
    if asset_type not in ASSETS:
        raise ValueError(f"Unknown asset type '{asset_type}'. Known: {list_types()}")

    return {
        "generator_script": _ROOT / "generators" / asset_type / f"{asset_type}_generator.py",
        "renderer_script":  _ROOT / "renderers"  / asset_type / f"{asset_type}_renderer.py",
        "tmp_dir":          _ROOT / "tmp"         / asset_type,
        "out_dir":          _ROOT / "renderers"   / asset_type / "output",
    }


def list_types() -> list[str]:
    return list(ASSETS)