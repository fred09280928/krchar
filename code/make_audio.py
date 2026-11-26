#!/usr/bin/env python3
"""Generate one audio clip per drill row (Korean pronunciation for each character).

Engine : Microsoft Edge TTS, voice ko-KR-InJoonNeural (male)
Output : audio/syl/<CODEPOINT>.mp3   for syllables   (가 ->  AC00.mp3)
         audio/jamo/<CODEPOINT>.mp3  for single letters (ㄱ -> 3131.mp3, spoken "기역")
Manifest: data/audio-manifest.json    (char, codepoint, kind, spoken text, duration, sha256)

The audio files are NOT committed to the repository: Edge TTS output is licensed for
personal use only (see README, "Audio"). The manifest is committed, so a fresh clone
can regenerate identical clips with this script.

Requires: edge-tts >= 7.3 (older versions get HTTP 403 from the service) and ffmpeg.

Usage:
    python3 make_audio.py                 # only missing clips
    python3 make_audio.py --force         # regenerate all
    python3 make_audio.py --limit 100     # stop after 100 clips (batching)
    python3 make_audio.py --edge-tts /path/to/edge-tts
"""
import argparse
import asyncio
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid

VOICE = "ko-KR-InJoonNeural"

# Single letters have no sound of their own: consonants are spoken by their letter name,
# vowels by the syllable that carries them (ㅏ -> 아).
CONSONANT_NAME = {
    "ㄱ": "기역", "ㄲ": "쌍기역", "ㄴ": "니은", "ㄷ": "디귿", "ㄸ": "쌍디귿",
    "ㄹ": "리을", "ㅁ": "미음", "ㅂ": "비읍", "ㅃ": "쌍비읍", "ㅅ": "시옷",
    "ㅆ": "쌍시옷", "ㅇ": "이응", "ㅈ": "지읒", "ㅉ": "쌍지읒", "ㅊ": "치읓",
    "ㅋ": "키읔", "ㅌ": "티읕", "ㅍ": "피읖", "ㅎ": "히읗",
}
VOWEL_SYLLABLE = {
    "ㅏ": "아", "ㅐ": "애", "ㅑ": "야", "ㅒ": "얘", "ㅓ": "어", "ㅔ": "에",
    "ㅕ": "여", "ㅖ": "예", "ㅗ": "오", "ㅘ": "와", "ㅙ": "왜", "ㅚ": "외",
    "ㅛ": "요", "ㅜ": "우", "ㅝ": "워", "ㅞ": "웨", "ㅟ": "위", "ㅠ": "유",
    "ㅡ": "으", "ㅢ": "의", "ㅣ": "이",
}


def spoken_text(ch):
    """What to say for this cell: the syllable itself, a letter name, or a vowel sound."""
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3:
        return ch, "syllable"
    if ch in CONSONANT_NAME:
        return CONSONANT_NAME[ch], "consonant-name"
    if ch in VOWEL_SYLLABLE:
        return VOWEL_SYLLABLE[ch], "vowel-sound"
    return None, None


def out_path(base, ch):
    sub = "syl" if 0xAC00 <= ord(ch) <= 0xD7A3 else "jamo"
    return os.path.join(base, "audio", sub, "%04X.mp3" % ord(ch))


def probe(path):
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    return (round(float(dur), 3) if dur else None), digest


async def synth(edge, text, dest, tmpdir):
    """edge-tts -> raw mp3, then trim silence, normalise loudness, mono 24 kHz."""
    raw = os.path.join(tmpdir, "%s.mp3" % uuid.uuid4().hex)   # unique: calls run concurrently
    proc = await asyncio.create_subprocess_exec(
        edge, "--voice", VOICE, "--text", text, "--write-media", raw,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    _, err = await proc.communicate()
    if proc.returncode != 0 or not os.path.exists(raw) or os.path.getsize(raw) == 0:
        raise RuntimeError(f"edge-tts failed for {text!r}: {err.decode()[-200:]}")
    af = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08,"
          "areverse,"
          "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08,"
          "areverse,loudnorm=I=-16:TP=-1.5:LRA=11")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    p = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af,
        "-ac", "1", "-ar", "24000", "-b:a", "48k", dest,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    _, err = await p.communicate()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {text!r}: {err.decode()[-200:]}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="regenerate clips that already exist")
    ap.add_argument("--limit", type=int, default=0, help="stop after N clips (batching)")
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--edge-tts", default=shutil.which("edge-tts") or "edge-tts")
    args = ap.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base, "data", "KRChar.csv")
    manifest_path = os.path.join(base, "data", "audio-manifest.json")
    tmpdir = os.path.join(base, "audio", ".tmp")
    os.makedirs(tmpdir, exist_ok=True)

    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cat = (r.get("category") or "").strip()
            ch = (r.get("Hangul") or "").strip()
            if not ch or cat.startswith("L0"):
                continue        # L0 letter layer is never quizzed -> no audio
            text, kind = spoken_text(ch)
            if not text:
                print(f"  skip {ch}: no pronunciation rule", file=sys.stderr)
                continue
            rows.append({"char": ch, "cp": "%04X" % ord(ch), "kind": kind,
                         "spoken": text, "category": cat, "file": out_path(base, ch)})

    todo = [r for r in rows if args.force or not os.path.exists(r["file"])]
    if args.limit:
        todo = todo[:args.limit]
    print(f"rows with audio: {len(rows)} | to generate now: {len(todo)} | voice {VOICE}")

    sem = asyncio.Semaphore(args.concurrency)

    async def one(r):
        async with sem:
            for attempt in (1, 2, 3):
                try:
                    await synth(args.edge_tts, r["spoken"], r["file"], tmpdir)
                    return r, None
                except Exception as exc:                      # noqa: BLE001
                    if attempt == 3:
                        return r, str(exc)
                    await asyncio.sleep(1.5 * attempt)

    done, failed = 0, []
    for chunk_start in range(0, len(todo), args.concurrency * 4):
        batch = todo[chunk_start:chunk_start + args.concurrency * 4]
        results = await asyncio.gather(*(one(r) for r in batch))
        for r, err in results:
            if err:
                failed.append((r["char"], err))
            else:
                done += 1
        print(f"  {done}/{len(todo)} ok" + (f", {len(failed)} failed" if failed else ""))

    # rebuild the manifest from every clip that exists
    manifest = []
    for r in rows:
        if not os.path.exists(r["file"]):
            continue
        dur, digest = probe(r["file"])
        manifest.append({
            "char": r["char"], "cp": r["cp"], "kind": r["kind"], "spoken": r["spoken"],
            "category": r["category"],
            "file": os.path.relpath(r["file"], base),
            "duration": dur, "sha256": digest,
            "voice": VOICE, "engine": "edge-tts",
            "license": "personal use only - not redistributable (see README)",
        })
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    shutil.rmtree(tmpdir, ignore_errors=True)
    total = sum(os.path.getsize(m["file"] and os.path.join(base, m["file"])) for m in manifest)
    print(f"manifest: {manifest_path} ({len(manifest)} entries, {total/1e6:.2f} MB of audio)")
    if failed:
        print(f"FAILED ({len(failed)}):", file=sys.stderr)
        for ch, err in failed[:10]:
            print(f"  {ch}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
