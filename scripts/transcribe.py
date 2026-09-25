"""Transcription mot à mot d'une vidéo (déjà dérushée) via l'API OpenAI whisper-1.

Usage :  python3 scripts/transcribe.py public/<episode>/video.mp4 [sortie.json]
Sortie :  work/<episode>/words.json   -> [{"word": "...", "start": s, "end": s}, ...]
          work/<episode>/voice.wav    -> audio 16 kHz mono (utilisé par gen-subs.py)

La clé est lue dans OPENAI_API_KEY (variable d'environnement ou fichier .env à la racine).
Au-delà de 25 Mo (limite de l'API), on envoie un mp3 64k mono extrait par ffmpeg.
"""
import json
import mimetypes
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
MAX_BYTES = 25 * 1024 * 1024


def api_key():
    key = os.environ.get("OPENAI_API_KEY")
    env = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.strip().startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("Clé manquante : mets OPENAI_API_KEY dans .env (voir .env.example).")
    return key


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def multipart(fields, path):
    boundary = uuid.uuid4().hex
    body = []
    for name, value in fields:
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    body.append(
        (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(path)}"\r\n'
         f"Content-Type: {ctype}\r\n\r\n").encode() + open(path, "rb").read() + b"\r\n")
    body.append(f"--{boundary}--\r\n".encode())
    return b"".join(body), f"multipart/form-data; boundary={boundary}"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    episode = os.path.basename(os.path.dirname(os.path.abspath(src))) or "episode"
    work = os.path.join(ROOT, "work", episode)
    os.makedirs(work, exist_ok=True)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(work, "words.json")

    # WAV de référence pour l'onset-snapping (gen-subs.py lit la waveform).
    ffmpeg("-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", os.path.join(work, "voice.wav"))

    upload = src
    if os.path.getsize(src) > MAX_BYTES:
        upload = os.path.join(work, "upload.mp3")
        ffmpeg("-i", src, "-vn", "-ac", "1", "-b:a", "64k", upload)

    body, ctype = multipart([("model", "whisper-1"), ("response_format", "verbose_json"),
                             ("timestamp_granularities[]", "word"), ("timestamp_granularities[]", "segment")],
                            upload)
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": ctype, "User-Agent": "studio-montage/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erreur API OpenAI {e.code} : {e.read().decode(errors='replace')[:400]}")

    words = [{"word": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
             for w in result.get("words", [])]
    json.dump(words, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(words)} mots -> {out}")
    print(result.get("text", "").strip())


if __name__ == "__main__":
    main()
