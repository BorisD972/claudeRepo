#!/usr/bin/env bash
# gen-matte.sh — fabrique une vidéo « personne détourée » avec transparence (macOS uniquement).
#
# Usage :  scripts/gen-matte.sh public/<episode>/video.mp4 [public/<episode>/person.webm]
#
# Étapes : ffmpeg -> PNG (30 fps) -> person_matte (Vision) -> alphamerge -> webm VP9 yuva420p
# encodé avec -g 1 (une image-clé par frame : sinon Remotion décode mal au seek).
# Montage : <OffthreadVideo src={staticFile('<episode>/person.webm')} transparent /> AU-DESSUS
# du texte, lui-même au-dessus de la vidéo normale -> le texte passe DERRIÈRE la personne.
set -euo pipefail

SRC="${1:?usage: scripts/gen-matte.sh <video> [sortie.webm]}"
EPISODE="$(basename "$(dirname "$SRC")")"
OUT="${2:-$(dirname "$SRC")/person.webm}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$ROOT/scripts/bin/person_matte"
WORK="$ROOT/work/$EPISODE/matte"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Le détourage utilise le framework Vision d'Apple : à lancer sur un Mac." >&2
  exit 1
fi

if [[ ! -x "$BIN" || "$ROOT/scripts/person_matte.swift" -nt "$BIN" ]]; then
  echo "Compilation de person_matte..."
  mkdir -p "$(dirname "$BIN")"
  swiftc -O "$ROOT/scripts/person_matte.swift" -o "$BIN"
fi

rm -rf "$WORK" && mkdir -p "$WORK/src" "$WORK/mask"
echo "1/3 Extraction des images..."
ffmpeg -loglevel error -y -i "$SRC" -vf fps=30 "$WORK/src/%06d.png"

echo "2/3 Détourage (Vision, qualité accurate)..."
"$BIN" "$WORK/src" "$WORK/mask"

echo "3/3 Encodage webm VP9 avec alpha..."
ffmpeg -loglevel error -y \
  -framerate 30 -i "$WORK/src/%06d.png" \
  -framerate 30 -i "$WORK/mask/%06d.png" \
  -filter_complex "[1:v]format=gray[m];[0:v][m]alphamerge,format=yuva420p[v]" -map "[v]" \
  -c:v libvpx-vp9 -pix_fmt yuva420p -g 1 -auto-alt-ref 0 -b:v 0 -crf 24 -row-mt 1 \
  "$OUT"

echo "ok -> $OUT"
echo "Vérifie l'alpha : ffprobe -v error -show_entries stream_tags=alpha_mode -of csv=p=0 \"$OUT\"  (doit afficher 1)"
