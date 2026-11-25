"""Monte un épisode complet à partir de plans.yaml avec FFmpeg.

Usage :
    python outils/assembler.py saisons/saison-01/ep01-le-marche-decolle [--apercu] [--garder-temp]

Pour chaque plan : animations/PXX.mp4 > images/PXX.png (zoom/pan) > carton animatic.
Audio : voix audio/voix/PXX.* + bruitages, musique abaissée sous les voix, -14 LUFS.
Sortie : rendu/epXX_AAAAMMJJ-HHMM.mp4 + .srt
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import (EXT_AUDIO, EXT_IMAGES, charger_plans, duree_media,  # noqa: E402
                    police_par_defaut, trouver)

FONDU = 0.5
COULEUR_CARTON = "0x2a1b3d"


def ffmpeg(args: list[str], cwd: Path) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"Échec FFmpeg :\n  {' '.join(cmd)}")


def rel(p: Path, base: Path) -> str:
    """Chemin relatif avec / : évite les problèmes de « C: » dans les filtres FFmpeg."""
    return p.resolve().relative_to(base.resolve()).as_posix()


def filtre_mouvement(mouvement: str, n: int, w: int, h: int, fps: int) -> str:
    centre_x, centre_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    z, x, y = "1", centre_x, centre_y
    if mouvement == "zoom_avant":
        z = f"1+0.15*on/{n}"
    elif mouvement == "zoom_arriere":
        z = f"1.15-0.15*on/{n}"
    elif mouvement == "pan_gauche":
        z, x = "1.15", f"(iw-iw/zoom)*(1-on/{n})"
    elif mouvement == "pan_droite":
        z, x = "1.15", f"(iw-iw/zoom)*on/{n}"
    # Agrandissement préalable x2 : zoom fluide, sans tremblement.
    return (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={w}x{h}:fps={fps}")


def construire_plan(plan: dict, idx: int, ep: Path, tmp: Path, w: int, h: int,
                    fps: int, preset: str) -> tuple[Path, float]:
    pid = plan["id"]
    voix = trouver(ep, "audio/voix", pid, EXT_AUDIO)
    duree = float(plan.get("duree", 5))
    if voix:
        dv = duree_media(voix) or 0
        if dv + 0.3 > duree:
            print(f"  {pid} : durée allongée {duree:.1f}s → {dv + 0.3:.1f}s (voix)")
            duree = dv + 0.3
    n = max(1, round(duree * fps))
    duree = n / fps

    entrees: list[str] = []
    clip = trouver(ep, "animations", pid, (".mp4", ".mov", ".webm"))
    image = trouver(ep, "images", pid, EXT_IMAGES)
    if clip:
        entrees += ["-stream_loop", "-1", "-i", rel(clip, ep)]
        fv = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"fps={fps},setsar=1")
        source = "animation"
    elif image:
        entrees += ["-i", rel(image, ep)]
        fv = f"[0:v]{filtre_mouvement(plan.get('mouvement', 'fixe'), n, w, h, fps)},setsar=1"
        source = "image"
    else:
        texte = tmp / f"{pid}_carton.txt"
        texte.write_text(f"{pid}\n{plan.get('description', '')}", encoding="utf-8")
        entrees += ["-f", "lavfi", "-i", f"color=c={COULEUR_CARTON}:s={w}x{h}:r={fps}:d={duree}"]
        police = police_par_defaut()
        font = f"fontfile='{police}':" if police else ""
        fv = (f"[0:v]drawtext={font}textfile='{rel(texte, ep)}':fontcolor=white:"
              f"fontsize={h // 18}:line_spacing=20:x=(w-text_w)/2:y=(h-text_h)/2,setsar=1")
        source = "carton"
    fv += f",trim=duration={duree},format=yuv420p"
    if plan.get("transition", "coupe") == "fondu":
        fv += f",fade=t=in:st=0:d={FONDU}"
    fv += "[v]"

    # Audio : voix + bruitages, complété en silence jusqu'à la durée du plan.
    pistes: list[str] = []
    filtres_a: list[str] = []
    k = 1
    if voix:
        entrees += ["-i", rel(voix, ep)]
        filtres_a.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{k}]")
        pistes.append(f"[a{k}]")
        k += 1
    for son in plan.get("sons") or []:
        f = ep / son["fichier"]
        if not f.exists():
            print(f"  ⚠ {pid} : bruitage manquant {son['fichier']}")
            continue
        entrees += ["-i", rel(f, ep)]
        retard = int(float(son.get("debut", 0)) * 1000)
        filtres_a.append(
            f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"volume={son.get('volume', 1.0)},adelay={retard}|{retard}[a{k}]")
        pistes.append(f"[a{k}]")
        k += 1
    if pistes:
        mix = (f"{''.join(pistes)}amix=inputs={len(pistes)}:normalize=0"
               if len(pistes) > 1 else f"{pistes[0]}anull")
        filtres_a.append(f"{mix},apad,atrim=duration={duree}[a]")
    else:
        entrees += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        filtres_a.append(f"[{k}:a]atrim=duration={duree}[a]")

    sortie = tmp / f"{idx:03d}_{pid}.mp4"
    ffmpeg([*entrees, "-filter_complex", ";".join([fv, *filtres_a]),
            "-map", "[v]", "-map", "[a]", "-t", f"{duree}",
            "-c:v", "libx264", "-preset", preset, "-crf", "18", "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            rel(sortie, ep)], ep)
    print(f"  {pid} ✓ {duree:5.1f}s ({source}{', voix' if voix else ''})")
    return sortie, duree


def horodatage(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ecrire_srt(plans: list[dict], durees: list[float], fichier: Path) -> bool:
    lignes, t, n = [], 0.0, 0
    for plan, d in zip(plans, durees):
        texte = (plan.get("sous_titre") or "").strip()
        if texte:
            n += 1
            lignes += [str(n), f"{horodatage(t)} --> {horodatage(t + d - 0.1)}", texte, ""]
        t += d
    fichier.write_text("\n".join(lignes), encoding="utf-8")
    return n > 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Monte un épisode à partir de plans.yaml")
    ap.add_argument("episode", type=Path, help="Dossier de l'épisode")
    ap.add_argument("--apercu", action="store_true", help="Rendu rapide en 960x540")
    ap.add_argument("--garder-temp", action="store_true", help="Conserver rendu/tmp")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("FFmpeg introuvable dans le PATH.")
    ep = args.episode.resolve()
    data = charger_plans(ep)
    fmt = data.get("format", {})
    w, h, fps = int(fmt.get("largeur", 1920)), int(fmt.get("hauteur", 1080)), int(fmt.get("fps", 30))
    preset = "medium"
    if args.apercu:
        w, h, preset = 960, 540, "ultrafast"

    rendu = ep / "rendu"
    tmp = rendu / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    plans = data["plans"]
    print(f"Épisode {data.get('episode')} — {data.get('titre')} : {len(plans)} plans, {w}x{h}")

    segments, durees = [], []
    for i, plan in enumerate(plans, 1):
        s, d = construire_plan(plan, i, ep, tmp, w, h, fps, preset)
        segments.append(s)
        durees.append(d)

    liste = tmp / "liste.txt"
    liste.write_text("".join(f"file '{s.name}'\n" for s in segments), encoding="utf-8")
    brut = tmp / "assemble.mp4"
    ffmpeg(["-f", "concat", "-safe", "0", "-i", rel(liste, ep), "-c", "copy", rel(brut, ep)], ep)

    total = sum(durees)
    nom = f"ep{data.get('episode', 'XX')}_{datetime.now():%Y%m%d-%H%M}{'_apercu' if args.apercu else ''}"
    srt = rendu / f"{nom}.srt"
    a_sous_titres = ecrire_srt(plans, durees, srt)

    entrees = ["-i", rel(brut, ep)]
    musique_cfg = data.get("musique") or {}
    musique = ep / musique_cfg["fichier"] if musique_cfg.get("fichier") else None
    if musique and musique.exists():
        entrees += ["-stream_loop", "-1", "-i", rel(musique, ep)]
        vol = musique_cfg.get("volume", 0.25)
        fondu_fin = max(0.0, total - 3)
        fa = (f"[0:a]asplit=2[voix][cle];"
              f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={vol},"
              f"atrim=duration={total},afade=t=out:st={fondu_fin}:d=3[mus];"
              f"[mus][cle]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[mduck];"
              f"[voix][mduck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        if musique:
            print(f"  ⚠ Musique absente : {musique_cfg['fichier']} (montage sans musique)")
        fa = "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"

    fv = "[0:v]null[v]"
    if a_sous_titres and data.get("sous_titres_incrustes", True):
        style = ("FontName=Arial,FontSize=22,Bold=1,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=40")
        fv = f"[0:v]subtitles='{rel(srt, ep)}':force_style='{style}'[v]"

    final = rendu / f"{nom}.mp4"
    ffmpeg([*entrees, "-filter_complex", f"{fv};{fa}", "-map", "[v]", "-map", "[a]",
            "-t", f"{total}", "-c:v", "libx264", "-preset", preset, "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", rel(final, ep)], ep)

    if not args.garder_temp:
        shutil.rmtree(tmp, ignore_errors=True)
    if not a_sous_titres:
        srt.unlink(missing_ok=True)
    m, s = divmod(int(round(total)), 60)
    print(f"\n✅ {final}  ({m} min {s:02d} s)")


if __name__ == "__main__":
    main()
