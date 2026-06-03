"""
renderers/rocks/rock_renderer.py
--------------------------------
Renderer de rochers low-poly type Deep Rock Galactic.
"""

import mathutils
import sys
import random
from pathlib import Path

import bpy
import bmesh

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from shared.base_renderer import BaseRenderer
from shared.io_utils import log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_rock(
    width: float,
    depth: float,
    height: float,
    roughness: float,
    subdivisions: int,
    seed: int
):

    rng = random.Random(seed)

    bpy.ops.mesh.primitive_cube_add(size=2)

    obj = bpy.context.active_object
    mesh = obj.data

    bm = bmesh.new()
    bm.from_mesh(mesh)

    if subdivisions > 0:
        bmesh.ops.subdivide_edges(
            bm,
            edges=bm.edges[:],
            cuts=subdivisions,
            use_grid_fill=True
        )


    center = mathutils.Vector((0,0,0))

    for v in bm.verts:
        center += v.co

    center /= len(bm.verts)

    for vert in bm.verts:

        direction = (vert.co - center).normalized()

        offset = rng.uniform(
            -roughness,
            roughness
        )

        vert.co += direction * offset

        vert.co.z *= rng.uniform(
            0.9,
            1.3
        )
    bm.to_mesh(mesh)
    bm.free()

    obj.scale = (
        width,
        depth,
        height
    )

    return obj


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class RockRenderer(BaseRenderer):

    def build(self, data: dict) -> bpy.types.Object:

        asset_id = data["asset_id"]

        log(
            f"Building rock '{asset_id}'..."
        )

        rock_obj = create_rock(
            width=data["width"],
            depth=data["depth"],
            height=data["height"],
            roughness=data["roughness"],
            subdivisions=data["subdivisions"],
            seed=data["seed"]
        )

        bpy.context.view_layer.objects.active = rock_obj

        bpy.ops.object.shade_flat()

        return rock_obj


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    RockRenderer.main()