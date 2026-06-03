"""
registry.py
-----------
Registre central de tous les types d'assets de la pipeline.

Pour ajouter un nouvel asset (ex: "rock") :
    1. Créer generators/rocks/rock_generator.py  (avec une fonction run())
    2. Créer renderers/rocks/rock_renderer.py    (script Blender)
    3. Ajouter une entrée dans ASSETS ci-dessous — c'est tout.

run_pipeline.py n'a jamais besoin d'être modifié.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Format d'une entrée :
#
#   "type_name": {
#       "generator_module" : import path Python du générateur
#                            (doit exposer une fonction run(count, seed, out_dir))
#       "renderer_script"  : chemin absolu vers le script Blender
#       "tmp_dir"          : dossier temporaire pour les JSON
#       "out_dir"          : dossier de sortie GLB + PNG
#   }
# ---------------------------------------------------------------------------

ASSETS: dict[str, dict] = {
    "cloud": {
        "generator_module": "generators.clouds.cloud_generator",
        "renderer_script":  _ROOT / "renderers" / "clouds" / "cloud_renderer.py",
        "tmp_dir":          _ROOT / "tmp" / "clouds",
        "out_dir":          _ROOT / "renderers" / "clouds" / "output",
    },
    # Exemple pour un futur asset :
    # "rock": {
    #     "generator_module": "generators.rocks.rock_generator",
    #     "renderer_script":  _ROOT / "renderers" / "rocks" / "rock_renderer.py",
    #     "tmp_dir":          _ROOT / "tmp" / "rocks",
    #     "out_dir":          _ROOT / "renderers" / "rocks" / "output",
    # },
}


def get(asset_type: str) -> dict:
    """Retourne la config d'un asset. Lève ValueError si inconnu."""
    if asset_type not in ASSETS:
        known = ", ".join(ASSETS.keys())
        raise ValueError(f"Unknown asset type '{asset_type}'. Known types: {known}")
    return ASSETS[asset_type]


def list_types() -> list[str]:
    return list(ASSETS.keys())