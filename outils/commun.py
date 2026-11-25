"""Fonctions partagées par les outils du studio."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML manquant : lancez  pip install -r requirements.txt")

EXT_IMAGES = (".png", ".jpg", ".jpeg", ".webp")
EXT_AUDIO = (".wav", ".mp3", ".m4a", ".flac", ".ogg")


def charger_plans(dossier: Path) -> dict:
    fichier = dossier / "plans.yaml"
    if not fichier.exists():
        sys.exit(f"Introuvable : {fichier}")
    with fichier.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or not data.get("plans"):
        sys.exit(f"Aucun plan dans {fichier}")
    return data


def trouver(dossier: Path, sous_dossier: str, nom: str, extensions) -> Path | None:
    for ext in extensions:
        p = dossier / sous_dossier / f"{nom}{ext}"
        if p.exists():
            return p
    return None


def duree_media(fichier: Path) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(fichier)],
            capture_output=True, text=True, check=True,
        ).stdout
        return float(json.loads(out)["format"]["duration"])
    except Exception:
        return None


def resolution(fichier: Path) -> tuple[int, int] | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(fichier)],
            capture_output=True, text=True, check=True,
        ).stdout
        s = json.loads(out)["streams"][0]
        return int(s["width"]), int(s["height"])
    except Exception:
        return None


def police_par_defaut() -> str | None:
    """Fichier de police pour drawtext (Windows n'a pas fontconfig)."""
    if os.name == "nt":
        for nom in ("arialbd.ttf", "arial.ttf", "segoeui.ttf"):
            p = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / nom
            if p.exists():
                return p.as_posix()
    return None
