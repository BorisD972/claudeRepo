"""words.json (transcribe.py) + voice.wav  ->  src/<episode>/subs.ts

Usage :  python3 scripts/gen-subs.py <episode> [words.json] [voice.wav]
         (par défaut : work/<episode>/words.json et work/<episode>/voice.wav)

RÈGLE CRITIQUE : on n'utilise jamais les timestamps whisper bruts (jitter d'environ ±150 ms
par mot, qu'aucun décalage global ne corrige). On lit la waveform : enveloppe par pas de 5 ms,
seuil relatif au 98e centile, et le début de chaque mot est recalé sur l'attaque physique la
plus proche. Les mots sans frontière nette (liaisons, mots enchaînés) prennent le biais médian
mesuré sur les mots recalés (« onset-snapping »).

Blocs de 1 à 2 mots maximum : on casse sur un silence > 0.35 s, sur la ponctuation, ou quand
le bloc dépasserait 14 caractères.
"""
import json
import os
import re
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Corrections (à remplir au fil des épisodes) --------------------------------------------
TEXT_FIX: dict[str, str] = {}  # mot tel que transcrit -> texte affiché (ex. "climaster": "Clim Master")
TIME_FIX: dict[int, float] = {}  # index du mot -> décalage manuel en secondes (+ = plus tard)
BREAK_BEFORE: set[int] = set()  # index des mots qui doivent ouvrir un nouveau bloc
NO_BREAK_BEFORE: set[int] = set()  # index des mots à garder avec le précédent

# --- Réglages de l'onset-snapping et du découpage ------------------------------------------
HOP = 0.005  # pas de l'enveloppe (5 ms)
THRESH_REL = 0.12  # seuil = 12 % du 98e centile de l'enveloppe
QUIET_BEFORE = 0.03  # une attaque = passage au-dessus du seuil après >= 30 ms en dessous
SNAP_WINDOW = 0.18  # on cherche l'attaque à ±180 ms du timestamp whisper
MAX_WORDS, MAX_CHARS, GAP_BREAK = 2, 14, 0.35
TAIL = 0.15  # tenue du dernier bloc avant un silence
MIN_WORD = 0.04  # durée minimale d'un mot après recalage


def envelope(wav_path):
    with wave.open(wav_path) as w:
        rate, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    hop = max(1, int(rate * HOP))
    frames = len(data) // hop
    env = np.abs(data[: frames * hop]).reshape(frames, hop).max(axis=1)
    return env


def onsets(env):
    thr = THRESH_REL * np.percentile(env, 98)
    above = env >= thr
    quiet = int(QUIET_BEFORE / HOP)
    out = []
    for i in range(quiet, len(env)):
        if above[i] and not above[i - quiet:i].any():
            out.append(i * HOP)
    return np.array(out)


def snap(words, onset_times):
    # Chaque attaque ne sert qu'à un mot, et dans l'ordre : un mot ne peut pas se recaler
    # avant l'attaque déjà prise par le mot précédent.
    starts, biases, last = [], [], -1.0
    for w in words:
        near = [t for t in onset_times if abs(t - w["start"]) <= SNAP_WINDOW and t > last]
        if near:
            s = float(min(near, key=lambda t: abs(t - w["start"])))
            biases.append(s - w["start"])
            starts.append(s)
            last = s
        else:
            starts.append(None)
    median = float(np.median(biases)) if biases else 0.0
    out = []
    for i, w in enumerate(words):
        s = starts[i] if starts[i] is not None else w["start"] + median
        s += TIME_FIX.get(i, 0.0)
        out.append({**w, "start": round(max(0.0, s), 3), "end": round(max(s, w["end"] + median), 3),
                    "snapped": starts[i] is not None})
    for a, b in zip(out, out[1:]):  # ordre parlé, pas de chevauchement, 40 ms minimum par mot
        b["start"] = max(b["start"], round(a["start"] + MIN_WORD, 3))
        a["end"] = min(max(a["end"], a["start"] + MIN_WORD), b["start"])
        b["end"] = max(b["end"], b["start"] + MIN_WORD)
    return out, median, sum(1 for s in starts if s is not None)


def chunks(words):
    blocks, cur = [], []
    for i, w in enumerate(words):
        text = TEXT_FIX.get(w["word"].lower(), w["word"])
        if cur:
            prev = cur[-1]
            candidate = " ".join(x["text"] for x in cur) + " " + text
            brk = (len(cur) >= MAX_WORDS or w["start"] - prev["end"] > GAP_BREAK
                   or re.search(r"[.,;:!?…]$", prev["text"]) or len(candidate) > MAX_CHARS or i in BREAK_BEFORE)
            if brk and i not in NO_BREAK_BEFORE:
                blocks.append(cur)
                cur = []
        cur.append({**w, "text": text})
    if cur:
        blocks.append(cur)
    subs = []
    for j, b in enumerate(blocks):
        start = b[0]["start"]
        nxt = blocks[j + 1][0]["start"] if j + 1 < len(blocks) else None
        end = b[-1]["end"] + TAIL
        if nxt is not None and nxt - b[-1]["end"] <= GAP_BREAK:
            end = nxt
        elif nxt is not None:
            end = min(end, nxt)
        text = re.sub(r"[.,;:…]+$", "", " ".join(x["text"] for x in b)).strip()
        subs.append({"text": text, "start": round(start, 3), "end": round(end, 3)})
    return subs


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    episode = sys.argv[1]
    words_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "work", episode, "words.json")
    wav_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "work", episode, "voice.wav")
    raw = json.load(open(words_path, encoding="utf-8"))
    words = [{"word": (w.get("word") or w.get("text", "")).strip(), "start": w["start"], "end": w["end"]} for w in raw]
    words = [w for w in words if w["word"]]
    merged = []  # élisions/traits d'union découpés par whisper : "n" + "'est" -> "n'est"
    for w in words:
        if merged and w["word"][:1] in ("'", "’", "-"):
            merged[-1] = {**merged[-1], "word": merged[-1]["word"] + w["word"], "end": w["end"]}
        else:
            merged.append(w)
    words = merged

    snapped, median, n = snap(words, onsets(envelope(wav_path)))
    subs = chunks(snapped)

    out_dir = os.path.join(ROOT, "src", episode)
    os.makedirs(out_dir, exist_ok=True)
    lines = ["// GÉNÉRÉ par scripts/gen-subs.py — ne pas éditer à la main (relancer le script).",
             f"// {len(words)} mots, {n} recalés sur une attaque, biais médian {median * 1000:+.0f} ms.",
             "import type {Sub} from '../lib/types';", "", "export const subs: Sub[] = ["]
    lines += [f"  {{text: {json.dumps(s['text'], ensure_ascii=False)}, start: {s['start']}, end: {s['end']}}},"
              for s in subs]
    lines += ["];", ""]
    open(os.path.join(out_dir, "subs.ts"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"{len(subs)} blocs -> src/{episode}/subs.ts  ({n}/{len(words)} mots recalés, biais médian "
          f"{median * 1000:+.0f} ms)")


if __name__ == "__main__":
    main()
