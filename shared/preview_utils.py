"""
shared/preview_utils.py
-----------------------
Setup caméra isométrique 3/4, éclairage three-point, rendu PNG.
Importé uniquement depuis un contexte Blender (--background).
"""

import bpy
import math
from mathutils import Vector


# ---------------------------------------------------------------------------
# Caméra isométrique 3/4
# ---------------------------------------------------------------------------

def setup_iso_camera(
    target: bpy.types.Object = None,
    distance: float = 12.0,
    sensor_size: float = 10.0,
) -> bpy.types.Object:
    """
    Crée une caméra orthographique en vue 3/4 isométrique.
    Pointe vers le centre de la bounding box de `target` si fourni.

    Angles isométriques classiques :
        Azimut    : 45°
        Élévation : 35.264° (arctan(1/√2))
    """
    if target is not None:
        bbox_world = [target.matrix_world @ Vector(c) for c in target.bound_box]
        center = sum(bbox_world, Vector()) / 8
    else:
        center = Vector((0, 0, 0))

    azimuth_rad   = math.radians(45)
    elevation_rad = math.radians(35.264)

    x = center.x + distance * math.cos(elevation_rad) * math.cos(azimuth_rad)
    y = center.y + distance * math.cos(elevation_rad) * math.sin(azimuth_rad)
    z = center.z + distance * math.sin(elevation_rad)

    cam_data = bpy.data.cameras.new("IsoCamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = sensor_size

    cam_obj = bpy.data.objects.new("IsoCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = (x, y, z)

    # Orienter vers le centre via une contrainte Track To
    constraint = cam_obj.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis    = "UP_Y"

    # Empty cible au centre
    empty = bpy.data.objects.new("CamTarget", None)
    empty.location = center
    bpy.context.scene.collection.objects.link(empty)
    constraint.target = empty

    # Forcer le recalcul de la contrainte
    bpy.context.view_layer.update()

    bpy.context.scene.camera = cam_obj
    return cam_obj


# ---------------------------------------------------------------------------
# Éclairage three-point
# ---------------------------------------------------------------------------

def setup_three_point_lighting():
    """
    Éclairage three-point classique :
        Key light  : forte, devant-droite-haut
        Fill light : douce, devant-gauche
        Rim light  : derrière, contour
    """
    lights = [
        {
            "name": "KeyLight",
            "type": "SUN",
            "energy": 3.0,
            "location": (5, -5, 8),
            "rotation_euler": (math.radians(45), 0, math.radians(45)),
        },
        {
            "name": "FillLight",
            "type": "SUN",
            "energy": 1.2,
            "location": (-5, -3, 4),
            "rotation_euler": (math.radians(60), 0, math.radians(-45)),
        },
        {
            "name": "RimLight",
            "type": "SUN",
            "energy": 0.8,
            "location": (0, 8, 3),
            "rotation_euler": (math.radians(120), 0, math.radians(180)),
        },
    ]

    for l in lights:
        light_data = bpy.data.lights.new(name=l["name"], type=l["type"])
        light_data.energy = l["energy"]
        light_obj = bpy.data.objects.new(l["name"], light_data)
        light_obj.location = l["location"]
        light_obj.rotation_euler = l["rotation_euler"]
        bpy.context.scene.collection.objects.link(light_obj)


# ---------------------------------------------------------------------------
# Rendu PNG
# ---------------------------------------------------------------------------

def render_preview(
    output_path: str,
    resolution: tuple[int, int] = (800, 600),
    engine: str = "BLENDER_EEVEE",
    samples: int = 16,
):
    """
    Rend la scène courante et sauvegarde en PNG transparent.

    Args:
        output_path : chemin absolu du .png de sortie (sans extension, Blender l'ajoute)
        resolution  : (width, height) en pixels
        engine      : 'BLENDER_EEVEE_NEXT' (rapide) ou 'CYCLES' (qualité)
        samples     : samples Cycles uniquement
    """
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = output_path
    scene.render.film_transparent = True

    if engine == "CYCLES":
        scene.cycles.samples = samples
        try:
            bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
            scene.cycles.device = "GPU"
        except Exception:
            scene.cycles.device = "CPU"

    bpy.ops.render.render(write_still=True)