"""
shared/base_renderer.py
------------------------
Classe de base abstraite pour tous les renderers Blender.

Chaque renderer (cloud_renderer.py, rock_renderer.py, ...) herite de cette
classe et n'a qu'une seule methode a implementer : build(data) qui construit
le mesh dans Blender et retourne l'objet bpy final.

Le reste (clear scene, material, GLB export, preview PNG) est gere ici
une seule fois pour tous les renderers.

CE FICHIER est importe UNIQUEMENT depuis un contexte Blender (--background).
"""

import argparse
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import bpy

from shared.io_utils      import load_json, ensure_dir, log
from shared.blender_utils import clear_scene, apply_white_material, export_glb
from shared.preview_utils import setup_iso_camera, setup_three_point_lighting, render_preview


class BaseRenderer(ABC):

    # Parametres de preview (surchargeable par sous-classe)
    camera_distance: float = 14.0
    camera_sensor:   float = 12.0
    preview_res:     tuple = (800, 600)
    render_engine:   str   = "BLENDER_EEVEE"
    render_samples:  int   = 16

    # -----------------------------------------------------------------------
    # Interface a implementer
    # -----------------------------------------------------------------------

    @abstractmethod
    def build(self, data: dict) -> bpy.types.Object:
        """
        Construit le mesh Blender a partir du dict JSON.
        Doit retourner l'objet bpy final (apres join/remesh/decimate etc.)
        L'objet sera nomme, texture, exporte et rendu automatiquement.
        """
        ...

    # -----------------------------------------------------------------------
    # Pipeline complete (ne pas surcharger sauf besoin specifique)
    # -----------------------------------------------------------------------

    def process(self, json_path: str, out_dir: str):
        """
        Pipeline complete pour un fichier JSON :
            1. Charge le JSON
            2. Clear la scene
            3. Appelle build() -> objet Blender
            4. Applique le materiau
            5. Exporte en GLB
            6. Rend la preview PNG
        """
        out        = Path(out_dir)
        ensure_dir(out)

        data     = load_json(json_path)
        asset_id = data["asset_id"]

        glb_path = str(out / f"{asset_id}.glb")
        png_path = str(out / f"{asset_id}")   # Blender ajoute .png

        clear_scene()

        obj = self.build(data)
        obj.name = asset_id
        apply_white_material(obj)

        log(f"Exporting GLB -> {glb_path}")
        export_glb(obj, glb_path)

        #blend_path = str(out / f"{asset_id}.blend")
        #log(f"Saving BLEND -> {blend_path}")
        #bpy.ops.wm.save_as_mainfile(filepath=blend_path)

        log(f"Rendering preview -> {png_path}.png")
        setup_three_point_lighting()
        setup_iso_camera(target=obj, distance=self.camera_distance, sensor_size=self.camera_sensor)
        render_preview(
            output_path=png_path,
            resolution=self.preview_res,
            engine=self.render_engine,
            samples=self.render_samples,
        )

        log(f"Done: {asset_id}", "OK")

    # -----------------------------------------------------------------------
    # Parsing args Blender (tout ce qui suit "--" dans la commande)
    # -----------------------------------------------------------------------

    @classmethod
    def parse_args(cls) -> argparse.Namespace:
        argv = sys.argv
        if "--" in argv:
            argv = argv[argv.index("--") + 1:]
        else:
            argv = []
        p = argparse.ArgumentParser()
        p.add_argument("--json", required=True)
        p.add_argument("--out",  required=True)
        return p.parse_args(argv)

    @classmethod
    def main(cls):
        """Point d'entree : instancie le renderer et lance process()."""
        renderer = cls()
        args     = cls.parse_args()
        renderer.process(args.json, args.out)