# Studio de montage (Remotion)

## Installer sur ton Mac (une seule fois)

1. Installer les outils : `brew install node ffmpeg` (Homebrew : https://brew.sh), puis
   `xcode-select --install` pour `swiftc` (détourage).
2. Récupérer le projet : `git clone https://github.com/BorisD972/claudeRepo.git && cd claudeRepo`
3. `npm install` puis `pip3 install -r scripts/requirements.txt`
4. Copier `.env.example` en `.env` et coller ta clé OpenAI après `OPENAI_API_KEY=`
   (le fichier `.env` ne part jamais sur GitHub).
5. `npm run dev` : le Studio s'ouvre dans ton navigateur.

## Faire un épisode

1. Dérushe dans CapCut, exporte la vidéo propre dans `public/<episode>/video.mp4`.
2. `python3 scripts/transcribe.py public/<episode>/video.mp4`
3. `python3 scripts/gen-subs.py <episode>`
4. Demande à Claude de monter l'épisode : il règle tout dans `src/<episode>/data.ts`.
5. Rends depuis le Studio (bouton Render).

Texte derrière toi (Mac) : `scripts/gen-matte.sh public/<episode>/video.mp4`.
