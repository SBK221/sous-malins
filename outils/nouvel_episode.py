"""Crée le dossier d'un nouvel épisode à partir de templates/episode.

Usage :
    python outils/nouvel_episode.py 2 "la-nuit-des-pulsations" --titre "La nuit des pulsations" [--saison 1]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("numero", type=int)
    ap.add_argument("slug", help="titre-en-minuscules-avec-tirets")
    ap.add_argument("--titre", default=None, help="Titre affiché (défaut : dérivé du slug)")
    ap.add_argument("--saison", type=int, default=1)
    a = ap.parse_args()

    num = f"{a.numero:02d}"
    titre = a.titre or a.slug.replace("-", " ").capitalize()
    cible = RACINE / "saisons" / f"saison-{a.saison:02d}" / f"ep{num}-{a.slug}"
    if cible.exists():
        sys.exit(f"Existe déjà : {cible}")
    shutil.copytree(RACINE / "templates" / "episode", cible)
    for f in cible.glob("*.*"):
        if f.suffix in (".md", ".yaml"):
            f.write_text(f.read_text(encoding="utf-8")
                         .replace("{{NUM}}", num).replace("{{TITRE}}", titre), encoding="utf-8")
    print(f"✅ Épisode créé : {cible}")


if __name__ == "__main__":
    main()
