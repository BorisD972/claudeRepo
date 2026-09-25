# Studio de montage vidéo — Remotion piloté par Claude

L'utilisateur n'est pas développeur : parler simplement, une étape à la fois, écrire tout le
code soi-même.

## Format et structure

- Réels 9:16 : compositions 1080×1920, 30 fps.
- Chaque vidéo (« épisode ») vit dans `src/<episode>/` avec TROIS fichiers :
  - `data.ts` — la télécommande : tous les réglages (timings en secondes via `F(sec)`, textes,
    couleurs, positions). C'est ici qu'on itère.
  - `subs.ts` — GÉNÉRÉ par `scripts/gen-subs.py`, jamais édité à la main.
  - `Episode.tsx` — le rendu, qui lit tout dans les deux autres. Aucune valeur magique en dur.
- Chaque épisode est déclaré dans `src/Root.tsx`. Médias dans `public/<episode>/`, fichiers de
  travail (wav, words.json, mattes) dans `work/<episode>/` (ignorés par git).
- La clé OpenAI est dans `.env` (ignoré par git). Elle ne doit JAMAIS finir dans git.

## Workflow

1. Dérush manuel par l'utilisateur (CapCut…) → vidéo propre dans `public/<episode>/`.
2. `python3 scripts/transcribe.py public/<episode>/video.mp4` → `work/<episode>/words.json` + `voice.wav`.
3. `python3 scripts/gen-subs.py <episode>` → `src/<episode>/subs.ts`.
4. Montage dans `src/<episode>/data.ts` (+ `Episode.tsx`).
5. Rendu par l'utilisateur, depuis l'interface du Studio (`npm run dev`).

## Règles permanentes (durement apprises — ne pas assouplir)

- Le dérush est MANUEL : l'utilisateur coupe lui-même ses ratés dans son éditeur (CapCut…) et
  amène une vidéo déjà propre. Ne jamais proposer de l'automatiser.
- `startFrom={1}` UNIQUEMENT sur les sources AAC/mp4 (compensation du priming). Sur un WAV c'est
  un bug : la voix joue ~33 ms en avance.
- Jamais de timestamps whisper bruts → onset-snapping (cf. `scripts/gen-subs.py`).
- Entrée de sous-titre ≤ 5-6 frames, déclenchée sur l'attaque (lead ~0.1 s) : une apparition plus
  longue est PERÇUE désync même si le timing est juste. Si un cas résiste : forced alignment
  (WhisperX).
- `startFrom`, pas `trimBefore`. Mezzanine 30 fps CFR avant montage (le VFR des téléphones fait
  dériver le son). Toujours scaler par `width/1080`.
- Médias pré-accélérés par ffmpeg (`setpts`/`atempo`), jamais `playbackRate`.
- Vidéos alpha : webm VP9 yuva420p `-g 1`, monté via `<OffthreadVideo transparent />`.
- Juger la fluidité au RENDER, jamais au preview (le Studio saccade par nature). C'est
  l'utilisateur qui rend, depuis l'interface du Studio.
- Sous-titres : toujours demander à l'utilisateur quel style utiliser. JAMAIS de couleur dans
  les subs — le contraste est typographique (poids, taille, italique), pas chromatique.
- Sound design : piocher dans une banque de SFX locale (pas de synthèse), volume 0.2–0.4 sous la
  voix, calé sur les beats de la voix.
- Motion library : le jour où l'utilisateur valide un motion réutilisable, proposer de le
  documenter dans une fiche (`docs/library/` : nom, description, fichier source, props,
  contexte). Un motion validé jamais documenté = travail perdu.

## Mezzanine (avant montage)

```bash
ffmpeg -i brut.mov -vf fps=30 -r 30 -c:v libx264 -crf 16 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -fps_mode cfr public/<episode>/video.mp4
```

## Détourage (Mac uniquement)

`scripts/gen-matte.sh public/<episode>/video.mp4` → `public/<episode>/person.webm`
(Vision `VNGeneratePersonSegmentationRequest` qualité `.accurate`, compilé par `swiftc -O`).
Ordre des calques : vidéo → texte → `person.webm` transparent : le texte passe derrière la personne.
