"""Génère les images avec Stable Diffusion en local (API de Forge / AUTOMATIC1111).

Prérequis : Forge lancé avec l'API active (voir docs/stable-diffusion.md).

Usage :
    # Feuilles de référence des personnages (prompts lus dans personnages/*.md)
    python outils/generer_images.py --references [--personnages sira]

    # Images des plans d'un épisode (prompts lus dans plans.yaml)
    python outils/generer_images.py saisons/saison-01/ep02-la-nuit-des-pulsations [--plans P01,P07]

Options utiles : --variantes 4 (choisir la meilleure), --ecraser, --seed 1234, --url http://127.0.0.1:7860

Sorties :
    images/PXX.png                     image retenue par le montage (variante 1)
    images/variantes/PXX_v2.png …      autres variantes : renommer en PXX.png celle qu'on préfère
    images/generation.json             seed et réglages de chaque image (pour la refaire à l'identique)
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import charger_plans  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent

# Réglages adaptés à DreamShaper XL Lightning (modèle conseillé). Modifiables en ligne de commande.
DEFAUTS = {"steps": 6, "cfg_scale": 2.0, "sampler_name": "DPM++ SDE", "scheduler": "Karras",
           "width": 1344, "height": 768}
NEGATIF = ("photorealistic, photo, 2d, flat, sketch, anime, lowres, blurry, deformed, disfigured, "
           "extra limbs, extra fingers, bad hands, bad anatomy, mutated, duplicate characters, "
           "text, letters, watermark, signature, logo, cropped, out of frame")


def appel_api(url: str, chemin: str, donnees: dict | None = None, delai: int = 600) -> dict:
    corps = json.dumps(donnees).encode() if donnees is not None else None
    req = urllib.request.Request(url.rstrip("/") + chemin, data=corps,
                                 headers={"Content-Type": "application/json"},
                                 method="POST" if corps else "GET")
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        sys.exit(f"API Stable Diffusion injoignable sur {url} ({e}).\n"
                 "→ Lancez Forge avec l'option --api (voir docs/stable-diffusion.md).")


def generer(url: str, prompt: str, reglages: dict, seed: int, n: int, modele: str | None) -> tuple[list[bytes], int]:
    charge = {**reglages, "prompt": prompt, "negative_prompt": NEGATIF, "seed": seed,
              "batch_size": 1, "n_iter": n, "send_images": True, "save_images": False}
    if modele:
        charge["override_settings"] = {"sd_model_checkpoint": modele}
    rep = appel_api(url, "/sdapi/v1/txt2img", charge)
    images = [base64.b64decode(i.split(",", 1)[-1]) for i in rep.get("images", [])][:n]
    if not images:
        sys.exit("L'API n'a renvoyé aucune image.")
    try:
        seed_reel = int(json.loads(rep.get("info", "{}")).get("seed", seed))
    except (ValueError, TypeError):
        seed_reel = seed
    return images, seed_reel


def ecrire(images: list[bytes], principal: Path, dossier_var: Path) -> None:
    principal.parent.mkdir(parents=True, exist_ok=True)
    principal.write_bytes(images[0])
    for k, img in enumerate(images[1:], 2):
        dossier_var.mkdir(parents=True, exist_ok=True)
        (dossier_var / f"{principal.stem}_v{k}.png").write_bytes(img)


def journal(fichier: Path, cle: str, infos: dict) -> None:
    data = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}
    data[cle] = infos
    fichier.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def prompt_reference(fiche: Path) -> str | None:
    """Extrait le bloc de code qui suit le titre « Feuille de référence »."""
    m = re.search(r"##\s*Feuille de r[ée]f[ée]rence.*?```[^\n]*\n(.*?)```", fiche.read_text(encoding="utf-8"), re.S)
    return " ".join(m.group(1).split()) if m else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Génère les images avec Stable Diffusion en local")
    ap.add_argument("episode", type=Path, nargs="?", help="Dossier de l'épisode")
    ap.add_argument("--references", action="store_true", help="Générer les feuilles de référence des personnages")
    ap.add_argument("--personnages", help="Liste séparée par des virgules (défaut : tous)")
    ap.add_argument("--plans", help="Liste de plans, ex. P01,P07 (défaut : tous)")
    ap.add_argument("--variantes", type=int, default=4, help="Images par prompt (défaut : 4)")
    ap.add_argument("--seed", type=int, default=-1, help="Seed de départ (-1 = aléatoire)")
    ap.add_argument("--ecraser", action="store_true", help="Regénérer même si l'image existe")
    ap.add_argument("--url", default="http://127.0.0.1:7860")
    ap.add_argument("--modele", help="Nom du checkpoint à charger (défaut : celui de Forge)")
    ap.add_argument("--steps", type=int, default=DEFAUTS["steps"])
    ap.add_argument("--cfg", type=float, default=DEFAUTS["cfg_scale"])
    ap.add_argument("--largeur", type=int, default=DEFAUTS["width"])
    ap.add_argument("--hauteur", type=int, default=DEFAUTS["height"])
    a = ap.parse_args()
    if not a.references and not a.episode:
        ap.error("indiquez un dossier d'épisode ou --references")

    reglages = {**DEFAUTS, "steps": a.steps, "cfg_scale": a.cfg, "width": a.largeur, "height": a.hauteur}
    modele = appel_api(a.url, "/sdapi/v1/options", delai=30).get("sd_model_checkpoint", "?")
    print(f"Stable Diffusion OK ({a.url}) — modèle : {a.modele or modele}")

    taches: list[tuple[str, str, Path, Path, Path]] = []  # (clé, prompt, image, variantes, journal)
    if a.references:
        voulus = {p.strip().lower() for p in a.personnages.split(",")} if a.personnages else None
        refs = RACINE / "personnages" / "references"
        for fiche in sorted((RACINE / "personnages").glob("*.md")):
            if voulus and fiche.stem.lower() not in voulus:
                continue
            p = prompt_reference(fiche)
            if not p:
                print(f"  ⚠ {fiche.name} : pas de bloc « Feuille de référence »")
                continue
            taches.append((fiche.stem, p, refs / f"{fiche.stem}_turnaround.png", refs / "variantes",
                           refs / "generation.json"))
    if a.episode:
        ep = a.episode.resolve()
        voulus = {p.strip().upper() for p in a.plans.split(",")} if a.plans else None
        for plan in charger_plans(ep)["plans"]:
            if voulus and plan["id"] not in voulus:
                continue
            if not (plan.get("prompt") or "").strip():
                print(f"  ⚠ {plan['id']} : prompt vide, ignoré")
                continue
            taches.append((plan["id"], plan["prompt"].strip(), ep / "images" / f"{plan['id']}.png",
                           ep / "images" / "variantes", ep / "images" / "generation.json"))

    faites = 0
    for i, (cle, prompt, image, dossier_var, fichier_journal) in enumerate(taches):
        if image.exists() and not a.ecraser:
            print(f"  {cle} : existe déjà ({image.name}), ignoré (--ecraser pour refaire)")
            continue
        seed = a.seed + i * 1000 if a.seed >= 0 else -1
        print(f"  {cle} : génération de {a.variantes} variante(s)…", flush=True)
        images, seed_reel = generer(a.url, prompt, reglages, seed, a.variantes, a.modele)
        ecrire(images, image, dossier_var)
        journal(fichier_journal, cle, {"seed": seed_reel, "variantes": len(images), "modele": a.modele or modele,
                                       **{k: reglages[k] for k in ("steps", "cfg_scale", "sampler_name", "width", "height")},
                                       "prompt": prompt, "date": f"{datetime.now():%Y-%m-%d %H:%M}"})
        print(f"  {cle} ✓ {image.relative_to(RACINE)} (+{len(images) - 1} variante(s), seed {seed_reel})")
        faites += 1
    print(f"\n✅ {faites} prompt(s) générés.")
    if faites and any(t[3].exists() for t in taches):
        print("Choisissez la meilleure variante : renommez-la en PXX.png (ou nom_turnaround.png).")


if __name__ == "__main__":
    main()
