import bpy
import sys
import argparse

# -------------------------
# Récupération des args CLI
# -------------------------
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

parser = argparse.ArgumentParser()
parser.add_argument("--shape", type=str, default="cube")
parser.add_argument("--radius", type=float, default=1.0)
parser.add_argument("--output", type=str, default="output.blend")

args = parser.parse_args(argv)

# -------------------------
# Nettoyer la scène
# -------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# -------------------------
# Génération
# -------------------------
if args.shape == "cube":
    bpy.ops.mesh.primitive_cube_add(size=args.radius)

elif args.shape == "sphere":
    bpy.ops.mesh.primitive_uv_sphere_add(radius=args.radius)

elif args.shape == "cylinder":
    bpy.ops.mesh.primitive_cylinder_add(radius=args.radius, depth=args.radius * 2)

else:
    raise ValueError(f"Shape inconnue: {args.shape}")

# -------------------------
# Sauvegarde
# -------------------------

bpy.ops.export_scene.gltf(
    filepath=args.output,
    export_format='GLB'
)

print("Saved:", args.output)