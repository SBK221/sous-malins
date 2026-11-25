# Sous-Malins — Studio de dessins animés

Dépôt de production de la série animée **« Les Éclairs de Niani »** (titre de travail) : aventure, humour, inventions et suspense dans une ville fictive d'Afrique de l'Ouest.

- **Format** : 3D cartoon colorée et cinématographique, 16:9 horizontal, environ 3 min par épisode
- **Saison 1** : 10 épisodes
- **Langue** : français

## Arborescence

```
sous-malins/
├── docs/                    Bible de la série, workflow, journal d'avancement
├── personnages/             Fiches de référence (Awa, Malik, Sira) + fragments de prompt
├── saisons/saison-01/
│   ├── episodes.md          Liste et statut des 10 épisodes
│   └── ep01-le-marche-decolle/
│       ├── script.md        Scénario + dialogues
│       ├── plans.yaml       Découpage plan par plan (source unique pour le montage)
│       ├── sons.md          Bruitages et musique
│       ├── publication.md   Titre, description, tags, miniature
│       ├── images/          Images générées (non versionnées)
│       ├── animations/      Clips animés (non versionnés)
│       ├── audio/voix|sons|musique/
│       └── rendu/           Vidéo finale + sous-titres (non versionnés)
├── templates/episode/       Modèle copié pour chaque nouvel épisode
└── outils/                  Scripts Python (FFmpeg) : nouvel épisode, montage, vérification
```

Les médias lourds (images, audio, vidéos) sont **exclus de Git** par le fichier `.gitignore`. Seuls les textes, les prompts et les scripts sont versionnés.

## Démarrage rapide (Windows / PowerShell)

```powershell
git clone https://github.com/SBK221/sous-malins.git
cd sous-malins
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Vérifier les médias d'un épisode (fichiers manquants, durées, résolutions)
python outils\verifier_episode.py saisons\saison-01\ep01-le-marche-decolle

# 2. Monter l'épisode (les plans sans image deviennent des cartons « animatic »)
python outils\assembler.py saisons\saison-01\ep01-le-marche-decolle

# 3. Créer l'épisode suivant à partir du modèle
python outils\nouvel_episode.py 2 "titre-de-l-episode"
```

Le résultat est écrit dans `saisons\saison-01\ep01-le-marche-decolle\rendu\`.

## Pipeline

Idée → Script → Voix → Images → Animation → Montage FFmpeg → Sous-titres → Miniature → Métadonnées → Publication → Analyse

Détails dans [`docs/workflow.md`](docs/workflow.md). Avancement dans [`docs/avancement.md`](docs/avancement.md).
