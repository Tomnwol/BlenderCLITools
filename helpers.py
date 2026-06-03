import sys
sys.dont_write_bytecode = True

import importlib.util
import argparse
from pathlib import Path

import registry


def load_module(path: Path):
    """Charge un module Python depuis un chemin absolu."""
    spec   = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_args():
    p = argparse.ArgumentParser(description="Asset pipeline")
    p.add_argument("--type",       type=str, default=None,
                   help=f"Type d'asset. Disponibles : {registry.list_types()}")
    p.add_argument("--types",      action="store_true",
                   help="Liste les types disponibles et quitte")
    p.add_argument("--count",      type=int, default=3)
    p.add_argument("--seed",       type=int, default=None)
    p.add_argument("--workers",    type=int, default=2)
    p.add_argument("--blender",    type=str, default="blender")
    p.add_argument("--keep-tmp",   action="store_true",
                   help="Ne pas supprimer les JSON tmp apres rendu")
    p.add_argument("--force",      action="store_true",
                   help="Ignore le cache et re-render tous les assets")
    p.add_argument("--cache-info", action="store_true",
                   help="Affiche le contenu du cache pour --type donne et quitte")

    args = p.parse_args()

    if args.types:
        print("Available asset types:")
        for t in registry.list_types():
            print(f"  - {t}")
        sys.exit(0)

    if not args.type or args.type not in registry.list_types():
        print("requires --type <TYPE>. To see all types available, use --types")
        sys.exit(1)

    return args