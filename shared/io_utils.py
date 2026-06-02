"""
shared/io_utils.py
------------------
Utilitaires I/O communs à tous les générateurs et renderers.
Independant de Blender (pas d'import bpy).
"""

import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def load_json(path: str | Path) -> Any:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"[io_utils] JSON not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path, indent: int = 2) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def tmp_dir(subdir: str = "") -> Path:
    base = Path("/tmp")
    target = base / subdir if subdir else base
    return ensure_dir(target)


def list_json_files(directory: str | Path) -> list[Path]:
    return sorted(Path(directory).glob("*.json"))


# ---------------------------------------------------------------------------
# Logging  (pas d'emojis : crash encodage Windows cp1252)
# ---------------------------------------------------------------------------

def log(msg: str, level: str = "INFO"):
    tag = {"INFO": "[INFO]", "OK": "[ OK ]", "WARN": "[WARN]", "ERROR": "[ERR ]"}.get(level, "     ")
    print(f"{tag} {msg}", file=sys.stdout, flush=True)