"""
renderers/clouds/cloud_renderer.py
------------------------------------
Renderer Blender pour les nuages. Herite de BaseRenderer.

Seule responsabilite : build() — construire le mesh depuis le JSON.
Le reste (export GLB, preview PNG, parsing args) est gere par BaseRenderer.

NE PAS lancer avec `python` : necessite le contexte bpy de Blender.
Appele par run_pipeline.py :
    blender --background --python renderers/clouds/cloud_renderer.py -- \
        --json C:/tmp/clouds/cloud_01.json --out renderers/clouds/output
"""

import sys
from pathlib import Path

import bpy

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from shared.base_renderer import BaseRenderer
from shared.blender_utils import add_uv_sphere, join_objects, apply_remesh, apply_decimate
from shared.io_utils import log


# ---------------------------------------------------------------------------
# Parametres mesh  (tweak ici)
# ---------------------------------------------------------------------------

REMESH_VOXEL_SIZE = 0.25
DECIMATE_RATIO    = 0.25
SPHERE_SEGMENTS   = 8
SPHERE_RINGS      = 5


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

class CloudRenderer(BaseRenderer):

    camera_distance = 14.0
    camera_sensor   = 12.0

    def build(self, data: dict) -> bpy.types.Object:
        spheres_data = data["spheres"]
        cloud_id     = data["asset_id"]

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

        cloud_obj = join_objects(sphere_objects)
        apply_remesh(cloud_obj,   voxel_size=REMESH_VOXEL_SIZE)
        apply_decimate(cloud_obj, ratio=DECIMATE_RATIO)

        return cloud_obj


# ---------------------------------------------------------------------------
# Point d'entree Blender
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    CloudRenderer.main()