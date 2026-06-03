"""
shared/base_generator.py
------------------------
Classe de base abstraite pour tous les generateurs d'assets.

Contrat impose a chaque generateur :
    - generate_one(asset_id, seed) -> dict   : genere un asset, retourne un dict valide
    - validate(data)               -> bool   : valide la structure d'un dict
    - run(count, seed, out_dir)    -> list   : genere N assets, sauvegarde les JSON

Squelette JSON garanti par tous les generateurs :
    {
        "asset_id" : str,   # identifiant unique (ex: "cloud_01")
        "asset_type": str,  # type declare dans registry (ex: "cloud")
        "seed"     : int,   # seed ayant produit cet asset
        <champs specifiques au type>
    }
"""

import math
import random
from abc import ABC, abstractmethod
from pathlib import Path

from shared.io_utils import save_json, ensure_dir, log


class BaseGenerator(ABC):

    # Chaque sous-classe declare son type (doit correspondre a registry.py)
    asset_type: str = ""

    # -----------------------------------------------------------------------
    # Interface a implementer
    # -----------------------------------------------------------------------

    @abstractmethod
    def generate_one(self, asset_id: str, seed: int) -> dict:
        """
        Genere un asset et retourne un dict.
        Le dict DOIT contenir les cles : asset_id, asset_type, seed.
        Les cles supplementaires sont libres.
        """
        ...

    @abstractmethod
    def validate(self, data: dict) -> bool:
        """
        Valide la structure d'un dict d'asset.
        Retourne True si valide, False sinon.
        Appele automatiquement par run() avant chaque sauvegarde.
        """
        ...

    # -----------------------------------------------------------------------
    # Helpers partages
    # -----------------------------------------------------------------------

    def _base_fields(self, asset_id: str, seed: int) -> dict:
        """Retourne les champs communs a injecter dans chaque asset."""
        return {
            "asset_id":   asset_id,
            "asset_type": self.asset_type,
            "seed":       seed,
        }

    def _make_ids(self, count: int, prefix: str | None = None) -> list[str]:
        """Genere une liste d'IDs zero-paddes : cloud_01, cloud_02, ..."""
        pfx = prefix or self.asset_type
        pad = max(2, math.ceil(math.log10(count + 1)))
        return [f"{pfx}_{str(i + 1).zfill(pad)}" for i in range(count)]

    # -----------------------------------------------------------------------
    # run() — point d'entree appele par run_pipeline.py
    # -----------------------------------------------------------------------

    def run(self, count: int, seed: int | None, out_dir: str, prefix: str | None = None) -> list[Path]:
        """
        Genere `count` assets et sauvegarde leurs JSON dans out_dir.
        Retourne la liste des fichiers crees.

        Le seed global derive des seeds individuels de facon deterministe :
        meme seed global => toujours les memes assets dans le meme ordre.
        """
        master_seed = seed if seed is not None else random.randint(0, 2**31)
        master_rng  = random.Random(master_seed)

        out = Path(out_dir)
        ensure_dir(out)

        ids   = self._make_ids(count, prefix)
        paths = []

        for asset_id in ids:
            asset_seed = master_rng.randint(0, 2**31)
            data = self.generate_one(asset_id, asset_seed)

            if not self.validate(data):
                log(f"Validation failed for {asset_id}, skipping", "WARN")
                continue

            path = save_json(data, out / f"{asset_id}.json")
            log(f"Generated {asset_id} -> {path}", "OK")
            paths.append(path)

        return paths