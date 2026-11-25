# Journal d'avancement

## 2026-11-25 — Création du dépôt
- Structure du projet créée : bible, fiches des personnages, modèle d'épisode, outils de montage FFmpeg.
- Épisode 01 : dossier créé avec synopsis et squelette des 14 plans.
- **À faire** : importer depuis le PC le scénario, les dialogues, les 14 prompts, le titre, la description et la miniature de l'épisode 01.
- **Ensuite** : générer les références des personnages → images des plans → voix → animation → montage.

## 2026-11-25 — Arc de saison + épisode 02
- **Arc de la saison 1** proposé dans `docs/arc-saison-01.md` : le Cœur de Niani, la légende des Éclairs, 2 nouveaux personnages (Mama Djénéba, Nafi Sonko) et le synopsis des épisodes 2 à 10. **À valider.**
- **Épisode 02 « La nuit des pulsations »** : scénario, dialogues avec indications vocales, 14 plans avec prompts (`plans.yaml`), fiche des sons, titre, description, chapitres et miniature.
- Animatic de l'épisode 02 monté et vérifié (cartons + sous-titres, 3 min 04 s, sans voix ni musique).
- Bible : ajout de l'atelier d'Awa, de la vieille fontaine et d'une variante de prompt pour les scènes de nuit.
- **Toujours à faire** : importer le contenu de l'épisode 01 depuis le PC.
- **Ensuite** : générer les feuilles de référence des personnages → images des plans des épisodes 01 et 02 → voix.

## 2026-11-25 — Feuilles de référence des personnages
- Awa et Malik : feuilles de face, de trois-quarts, de profil et de dos générées avec Canva (liens dans les fiches). **À valider**, puis à télécharger en pleine résolution dans `personnages/references/`.
- Sira : non générée, le quota de crédits Canva est épuisé.
- ElevenLabs : génération d'images refusée, le compte gratuit est désactivé et il faut un abonnement payant. Rien n'a été facturé.

## 2026-11-25 — Choix : Stable Diffusion en local
- Décision : les images seront générées **en local avec Stable Diffusion** (Forge + DreamShaper XL Lightning), gratuitement et sans quota.
- Nouvel outil `outils/generer_images.py` : il lit les prompts dans `plans.yaml` et dans les fiches des personnages, appelle l'API de Forge, enregistre les variantes et note les seeds. Testé ici avec un faux serveur, puis vérifié avec `assembler.py`.
- Guide d'installation pour Windows : `docs/stable-diffusion.md`.
- **Prochaine action (sur le PC)** : installer Forge et le modèle, puis générer la feuille de référence de Sira et les 14 plans de l'épisode 02.
