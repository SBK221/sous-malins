"""Vérifie les médias d'un épisode avant le montage.

Usage :
    python outils/verifier_episode.py saisons/saison-01/ep01-le-marche-decolle
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import EXT_AUDIO, EXT_IMAGES, charger_plans, duree_media, resolution, trouver  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", type=Path)
    ep = ap.parse_args().episode.resolve()
    data = charger_plans(ep)
    fmt = data.get("format", {})
    w, h = int(fmt.get("largeur", 1920)), int(fmt.get("hauteur", 1080))
    ratio = w / h

    print(f"Épisode {data.get('episode')} — {data.get('titre')}\n")
    print(f"{'Plan':<5} {'Durée':>6}  {'Visuel':<10} {'Voix':>7}  {'Prompt':<6} Remarques")
    print("-" * 78)
    total, manque_visuel, manque_voix, sans_prompt, alertes = 0.0, 0, 0, 0, 0
    ids = set()
    for plan in data["plans"]:
        pid = plan.get("id", "?")
        notes = []
        if pid in ids:
            notes.append("ID EN DOUBLE")
            alertes += 1
        ids.add(pid)
        duree = float(plan.get("duree", 0))
        clip = trouver(ep, "animations", pid, (".mp4", ".mov", ".webm"))
        image = trouver(ep, "images", pid, EXT_IMAGES)
        visuel = "animation" if clip else "image" if image else "—"
        if not (clip or image):
            manque_visuel += 1
        media = clip or image
        if media:
            r = resolution(media)
            if r and abs(r[0] / r[1] - ratio) > 0.02:
                notes.append(f"ratio {r[0]}x{r[1]} (sera recadré)")
            elif r and r[0] < w:
                notes.append(f"résolution faible {r[0]}x{r[1]}")
        voix = trouver(ep, "audio/voix", pid, EXT_AUDIO)
        dv = duree_media(voix) if voix else None
        if not voix:
            manque_voix += 1
        elif dv and dv + 0.3 > duree:
            notes.append(f"voix plus longue que le plan → {dv + 0.3:.1f}s")
            duree = dv + 0.3
        for son in plan.get("sons") or []:
            if not (ep / son["fichier"]).exists():
                notes.append(f"son manquant {son['fichier']}")
                alertes += 1
        if not (plan.get("prompt") or "").strip():
            sans_prompt += 1
        total += duree
        print(f"{pid:<5} {duree:5.1f}s  {visuel:<10} {f'{dv:.1f}s' if dv else '—':>7}  "
              f"{'oui' if (plan.get('prompt') or '').strip() else 'non':<6} {'; '.join(notes)}")

    musique = (data.get("musique") or {}).get("fichier")
    print("-" * 78)
    m, s = divmod(int(round(total)), 60)
    n = len(data["plans"])
    print(f"Durée estimée : {m} min {s:02d} s   |   {n} plans")
    print(f"Visuels : {n - manque_visuel}/{n}   Voix : {n - manque_voix}/{n}   "
          f"Prompts : {n - sans_prompt}/{n}")
    print(f"Musique : {'OK' if musique and (ep / musique).exists() else 'absente'}")
    if alertes:
        print(f"⚠ {alertes} alerte(s) bloquante(s)")
        sys.exit(1)
    prets = manque_visuel == 0 and manque_voix == 0
    print("✅ Prêt pour le montage final." if prets
          else "ℹ Montage possible en animatic (cartons pour les plans sans visuel).")


if __name__ == "__main__":
    main()
