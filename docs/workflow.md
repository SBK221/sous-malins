# Workflow de production d'un épisode

Chaque étape écrit dans le dossier de l'épisode. Le fichier `plans.yaml` est la **source unique** : le montage, les sous-titres et la vérification le lisent.

| # | Étape | Sortie | Outil conseillé (gratuit ou peu coûteux) |
|---|---|---|---|
| 1 | Histoire + dialogues | `script.md` | Claude |
| 2 | Découpage en plans | `plans.yaml` (prompt, durée, mouvement, réplique) | Claude |
| 3 | Références personnages | `personnages/references/*.png` | Flux / Stable Diffusion local, Ideogram |
| 4 | Images des plans | `images/P01.png` … | Flux / SD avec les références (IP-Adapter, LoRA) |
| 5 | Voix | `audio/voix/P01.wav` … | ElevenLabs (qualité) ; repli local : XTTS-v2, F5-TTS |
| 6 | Animation | `animations/P01.mp4` … (facultatif) | Kling, Hailuo, Wan 2.x local ; sinon zoom/pan FFmpeg |
| 7 | Bruitages + musique | `audio/sons/`, `audio/musique/` | Freesound, Pixabay Audio, bibliothèque audio YouTube |
| 8 | Vérification | rapport console | `outils/verifier_episode.py` |
| 9 | Montage + sous-titres | `rendu/epXX_*.mp4` + `.srt` | `outils/assembler.py` (FFmpeg) |
| 10 | Miniature | `rendu/miniature.png` (1280×720) | Canva / Figma |
| 11 | Métadonnées | `publication.md` | Claude, vidIQ |
| 12 | Publication | lien de la vidéo publiée | YouTube Studio, puis Postiz |
| 13 | Analyse | `docs/avancement.md` | YouTube Analytics |

## Règles de nommage

- Plans : `P01`, `P02`… Le même identifiant sert pour l'image, le clip, la voix et la ligne de `plans.yaml`.
- Voix : un fichier par plan (`audio/voix/P03.wav`), qui contient toutes les répliques du plan.
- Épisodes : `epNN-titre-en-minuscules`.

## Montage automatique (`outils/assembler.py`)

Pour chaque plan :
1. Utilise `animations/PXX.mp4` s'il existe ; sinon `images/PXX.png` avec le mouvement demandé ; sinon un **carton animatic** (fond coloré + numéro et description du plan).
2. Mixe la voix et les bruitages du plan.
3. Ajuste automatiquement la durée si la voix est plus longue que la durée prévue.

Puis : concaténation, musique de fond abaissée automatiquement sous les voix (ducking), normalisation du volume à −14 LUFS (standard YouTube), sous-titres `.srt` générés et incrustés.

Pendant le développement, on peut donc produire un **animatic complet** avant d'avoir la moindre image, puis remplacer progressivement les cartons par les vrais visuels.

## Validation avant publication

- [ ] Durée conforme (environ 3 min)
- [ ] Voix audible et non couverte par la musique
- [ ] Personnages cohérents d'un plan à l'autre
- [ ] Sous-titres synchronisés et sans faute
- [ ] Miniature lisible sur téléphone
- [ ] Ne supprimer les fichiers temporaires qu'**après** la publication confirmée
