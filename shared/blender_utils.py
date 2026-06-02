"""
shared/blender_utils.py
-----------------------
Wrappers bpy réutilisables pour tous les renderers.
CE FICHIER est importé UNIQUEMENT depuis un contexte Blender (--background).
"""

import bpy
import math


# ---------------------------------------------------------------------------
# Scène
# ---------------------------------------------------------------------------

def clear_scene():
    """Supprime tous les objets de la scène et purge les données orphelines."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)


def deselect_all():
    bpy.ops.object.select_all(action="DESELECT")


def set_active(obj):
    deselect_all()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def add_uv_sphere(location=(0, 0, 0), scale=(1, 1, 1), segments=8, rings=6) -> bpy.types.Object:
    """
    Ajoute une UV Sphere basse résolution (segments/rings bas = low-poly).
    Retourne l'objet créé.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
    )
    obj = bpy.context.active_object
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return obj


# ---------------------------------------------------------------------------
# Opérations mesh
# ---------------------------------------------------------------------------

def join_objects(objects: list) -> bpy.types.Object:
    """Joint une liste d'objets en un seul. Retourne l'objet résultant."""
    deselect_all()
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def apply_remesh(obj, voxel_size: float = 0.3):
    """Applique un Voxel Remesh : fusionne les volumes qui se chevauchent."""
    set_active(obj)
    mod = obj.modifiers.new(name="Remesh", type="REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel_size
    bpy.ops.object.modifier_apply(modifier=mod.name)


def apply_decimate(obj, ratio: float = 0.3):
    """Applique un Decimate pour réduire le nombre de polygones."""
    set_active(obj)
    mod = obj.modifiers.new(name="Decimate", type="DECIMATE")
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_glb(obj, filepath: str):
    """Exporte l'objet sélectionné en GLB."""
    set_active(obj)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )


# ---------------------------------------------------------------------------
# Matériau
# ---------------------------------------------------------------------------

def apply_white_material(obj, name: str = "CloudMat"):
    """Applique un matériau blanc mat (utile pour la preview PNG)."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
        bsdf.inputs["Specular IOR Level"].default_value = 0.05
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)