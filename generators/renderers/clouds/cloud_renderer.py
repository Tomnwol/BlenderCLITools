"""
renderers/clouds/cloud_renderer.py
------------------------------------
Script Blender (--background). Lit un JSON de nuage, construit le mesh,
exporte en GLB et génère une preview PNG isométrique 3/4.

Appelé par run_pipeline.py via subprocess :
    blender --background --python renderers/clouds/cloud_renderer.py -- \
        --json /tmp/clouds/cloud_01.json \
        --out  renderers/clouds/output

NE PAS lancer directement avec `python` : nécessite le contexte bpy de Blender.
"""

import sys
import argparse
from pathlib import Path

import bpy

# Résolution des shared helpers : on ajoute la racine du projet au path.
# run_pipeline.py lance Blender depuis la racine, donc parents[2] = racine.
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from shared.io_utils      import load_json, ensure_dir, log
from shared.blender_utils import (
    clear_scene, add_uv_sphere, join_objects,
    apply_remesh, apply_decimate, export_glb,
    apply_white_material,
)
from shared.preview_utils import (
    setup_iso_camera, setup_three_point_lighting, render_preview,
)


# ---------------------------------------------------------------------------
# Paramètres mesh  (tweak ici)
# ---------------------------------------------------------------------------

REMESH_VOXEL_SIZE = 0.25   # plus petit = plus de détails
DECIMATE_RATIO    = 0.25   # 0.25 = garde 25% des faces → low-poly marqué
SPHERE_SEGMENTS   = 8      # peu de segments = sphères anguleuses
SPHERE_RINGS      = 5


# ---------------------------------------------------------------------------
# Construction du nuage dans Blender
# ---------------------------------------------------------------------------

def build_cloud(cloud_data: dict) -> bpy.types.Object:
    """
    Instancie les sphères, les joint, applique remesh + decimate.
    Retourne l'objet final.
    """
    spheres_data = cloud_data["spheres"]
    cloud_id     = cloud_data["cloud_id"]

    log(f"Building '{cloud_id}' ({len(spheres_data)} spheres)...")

    sphere_objects = []
    for s in spheres_data:
        pos = (s["position"]["x"], s["position"]["y"], s["position"]["z"])
        sc  = (s["scale"]["x"],    s["scale"]["y"],    s["scale"]["z"])
        obj = add_uv_sphere(
            location=pos,
            scale=sc,
            segments=SPHERE_SEGMENTS,
            rings=SPHERE_RINGS,
        )
        sphere_objects.append(obj)

    cloud_obj      = join_objects(sphere_objects)
    cloud_obj.name = cloud_id

    apply_remesh(cloud_obj,   voxel_size=REMESH_VOXEL_SIZE)
    apply_decimate(cloud_obj, ratio=DECIMATE_RATIO)

    return cloud_obj


# ---------------------------------------------------------------------------
# Pipeline complète pour un fichier JSON
# ---------------------------------------------------------------------------

def process(json_path: str, out_dir: str):
    out        = Path(out_dir)
    ensure_dir(out)

    cloud_data = load_json(json_path)
    cloud_id   = cloud_data["cloud_id"]

    glb_path = str(out / f"{cloud_id}.glb")
    png_path = str(out / f"{cloud_id}")   # Blender ajoute .png automatiquement

    # Scène propre
    clear_scene()

    # Construction mesh
    cloud_obj = build_cloud(cloud_data)
    apply_white_material(cloud_obj)

    # Export GLB
    log(f"Exporting GLB → {glb_path}")
    export_glb(cloud_obj, glb_path)

    # Preview PNG
    log(f"Rendering preview → {png_path}.png")
    setup_three_point_lighting()
    setup_iso_camera(target=cloud_obj, distance=14.0, sensor_size=12.0)
    render_preview(
        output_path=png_path,
        resolution=(800, 600),
        engine="BLENDER_EEVEE_NEXT",
        samples=16,
    )

    log(f"Done: {cloud_id}", "OK")


# ---------------------------------------------------------------------------
# Parsing des args Blender (tout ce qui suit "--" dans la commande)
# ---------------------------------------------------------------------------

def _parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    p = argparse.ArgumentParser(description="Cloud Blender renderer")
    p.add_argument("--json", required=True, help="Chemin vers le JSON du nuage")
    p.add_argument("--out",  required=True, help="Dossier de sortie pour GLB et PNG")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    process(args.json, args.out)