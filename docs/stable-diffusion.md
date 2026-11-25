# Stable Diffusion en local (Windows) — installation et utilisation

Objectif : générer gratuitement, sur le PC, les feuilles de référence et les images des plans directement à partir de `plans.yaml`.

## 1. Matériel requis

| | Minimum | Conseillé |
|---|---|---|
| Carte graphique | NVIDIA, 6 Go de VRAM | NVIDIA RTX, 8 à 12 Go de VRAM ou plus |
| Mémoire vive | 16 Go | 32 Go |
| Disque | 25 Go libres (SSD) | 50 Go libres |

Vérifier sa carte graphique (PowerShell) :
```powershell
nvidia-smi --query-gpu=name,memory.total --format=csv
```
Si la commande échoue, la carte n'est pas NVIDIA ou ses pilotes ne sont pas installés. Dans ce cas, se reporter à la section 6.

## 2. Installer Forge (interface + API)

Forge est une version optimisée de Stable Diffusion WebUI. Il fonctionne avec les modèles SDXL et Flux et consomme peu de mémoire graphique.

1. Ouvrir https://github.com/lllyasviel/stable-diffusion-webui-forge et, dans la section « Installing Forge », télécharger le **paquet en un clic** (fichier `.7z`, version CUDA 12.x).
2. Le décompresser dans `C:\IA\forge` avec 7-Zip. Éviter les chemins qui contiennent des espaces ou des accents.
3. Lancer une première fois :
   ```powershell
   cd C:\IA\forge
   .\update.bat
   .\run.bat
   ```
   Le premier lancement télécharge les dépendances, ce qui prend 10 à 20 minutes. Quand l'interface s'ouvre sur http://127.0.0.1:7860, fermer la fenêtre.

## 3. Télécharger le modèle

Modèle conseillé : **DreamShaper XL Lightning**. Il donne un bon rendu 3D cartoon, il est rapide (6 étapes par image) et sa licence permet l'usage commercial (openrail++).

```powershell
$dest = "C:\IA\forge\webui\models\Stable-diffusion\DreamShaperXL_Lightning.safetensors"
Invoke-WebRequest -Uri "https://huggingface.co/Lykon/dreamshaper-xl-lightning/resolve/main/DreamShaperXL_Lightning.safetensors" -OutFile $dest
```
Le fichier pèse environ 6,5 Go. Si le dossier `webui\models` n'existe pas, utiliser `C:\IA\forge\models\Stable-diffusion\`.

## 4. Activer l'API

Ouvrir `C:\IA\forge\webui\webui-user.bat` avec le Bloc-notes et modifier la ligne suivante :
```bat
set COMMANDLINE_ARGS=--api
```
Relancer `C:\IA\forge\run.bat`. Dans l'interface, choisir **DreamShaperXL_Lightning** dans la liste « Checkpoint », en haut à gauche, puis laisser la fenêtre ouverte.

Tester l'API dans une autre fenêtre PowerShell :
```powershell
Invoke-RestMethod http://127.0.0.1:7860/sdapi/v1/options | Select-Object sd_model_checkpoint
```

## 5. Générer les images du projet

```powershell
cd C:\chemin\vers\sous-malins
.\.venv\Scripts\Activate.ps1

# Feuille de référence de Sira (4 variantes)
python outils\generer_images.py --references --personnages sira

# Les 14 plans de l'épisode 02 (4 variantes par plan)
python outils\generer_images.py saisons\saison-01\ep02-la-nuit-des-pulsations

# Refaire seulement deux plans, avec une seed fixe
python outils\generer_images.py saisons\saison-01\ep02-la-nuit-des-pulsations --plans P07,P13 --ecraser --seed 1234

# Monter l'épisode avec les images
python outils\assembler.py saisons\saison-01\ep02-la-nuit-des-pulsations
```

- La variante 1 est enregistrée sous `images\PXX.png` : c'est elle qu'utilise le montage. Les autres sont dans `images\variantes\`. Pour en choisir une autre, il suffit de la renommer en `PXX.png`.
- `images\generation.json` garde la seed et les réglages de chaque plan, ce qui permet de refaire une image à l'identique. Les variantes suivantes utilisent les seeds +1, +2 et +3.
- Une image existante n'est jamais écrasée sans l'option `--ecraser`.
- Temps indicatif : 3 à 10 secondes par image sur une RTX 3060, soit environ 5 minutes pour les 56 images d'un épisode.

## 6. Pas de carte NVIDIA ?

- **Carte AMD** : utiliser la version Forge ou SD.Next compatible ZLUDA/DirectML, plus lente et plus délicate à installer.
- **Ordinateur sans carte graphique** : louer un GPU à l'heure (RunPod, Vast.ai, environ 0,30 $/h) avec un modèle Forge déjà prêt, puis utiliser `--url https://…` dans le script. Autre solution : Google Colab.

## 7. Cohérence des personnages

Les descriptions d'apparence sont recopiées mot pour mot dans chaque prompt, mais cela ne garantit pas des visages identiques d'un plan à l'autre. Étapes suivantes possibles, une fois les feuilles de référence validées :
1. **IP-Adapter** (intégré à Forge, onglet ControlNet) : chaque plan est conditionné par la feuille de référence du personnage.
2. **LoRA par personnage** : un petit modèle entraîné sur 15 à 20 images validées de chaque personnage. C'est la solution la plus fiable pour une saison de 10 épisodes.
