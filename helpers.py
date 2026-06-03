import importlib.util
import argparse
import registry
from pathlib import Path

# Load Python module from a file path
def load_module(path: Path):
    spec   = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# args
def _parse_args():
    p = argparse.ArgumentParser(description="Asset pipeline")
    p.add_argument("--type",     type=str, default=None,
                   help=f"Type d'asset. Disponibles : {registry.list_types()}")
    p.add_argument("--types",    action="store_true")
    p.add_argument("--count",    type=int, default=3)
    p.add_argument("--seed",     type=int, default=None)
    p.add_argument("--workers",  type=int, default=2)
    p.add_argument("--blender",  type=str, default="blender")
    p.add_argument("--keep-tmp", action="store_true")

    args = p.parse_args()
    if args.types:
        print("Available asset types:")
        for t in registry.list_types():
            print(f"  - {t}")
        sys.exit()

    elif not (args.type and args.type in registry.list_types()):
        print("requires --type <TYPE>. To see all the types available, add --types")
        sys.exit()
    return args
