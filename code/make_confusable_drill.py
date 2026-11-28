#!/usr/bin/env python3
"""Build a listen-and-repeat drill for the confusable trio ㅅ · ㅈ · ㅊ.

Uses the clips already in audio/ (no new TTS). Sequence, as agreed:

  Part 1 — letter names, 3 rounds:  시옷 · 지읒 · 치읓  (×3 rounds)
  Part 2 — 18 syllables, per vowel in the order ㅓ ㅡ ㅗ ㅜ ㅣ ㅏ:
           서저처 ×3, 스즈츠 ×3, 소조초 ×3, 수주추 ×3, 시지치 ×3, 사자차 ×3

Gaps: 1 s between clips inside a round, 2 s between rounds and between vowel
groups (a 2 s break is what makes "that was round one" audible).

    /usr/bin/python3 code/make_confusable_drill.py [--out practice/ㅅㅈㅊ-drill.mp3]
"""
import argparse
import array
import json
import os
import subprocess
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "data", "audio-manifest.json")
RATE = 24000
GAP_CLIP = 1.0      # between two clips of the same round
GAP_SET = 2.0       # between rounds / between vowel groups
LEAD, TAIL = 0.4, 0.8

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
CONSONANTS = "ㅅㅈㅊ"
VOWELS = "ㅓㅡㅗㅜㅣㅏ"
JAMO_CP = {"ㅅ": "3145", "ㅈ": "3148", "ㅊ": "314A"}


def silence(seconds):
    return array.array("h", bytes(2 * int(RATE * seconds)))


def pcm(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(RATE), "-"],
        capture_output=True, check=True).stdout
    a = array.array("h")
    a.frombytes(raw)
    return a


def build(manifest):
    """Return [(label, pcm), ...] already interleaved with silence."""
    by_cp = {e["cp"]: e for e in manifest}
    out, script = [], []
    added = 0

    def add(label, cp, gap_before):
        nonlocal added
        e = by_cp[cp]
        if added and gap_before:
            out.append(silence(gap_before))
        out.append(pcm(os.path.join(ROOT, e["file"])))
        script.append((label, gap_before if added else 0.0, e["duration"]))
        added += 1

    out.append(silence(LEAD))

    # Part 1: letter names, three rounds
    for _ in range(3):
        for i, ch in enumerate(CONSONANTS):
            add(f"{ch}({by_cp[JAMO_CP[ch]]['spoken']})", JAMO_CP[ch],
                GAP_CLIP if i else GAP_SET)

    # Part 2: consonant × vowel, each group three times
    for v in VOWELS:
        for _ in range(3):
            for i, ch in enumerate(CONSONANTS):
                cp = f"{0xAC00 + (CHO.index(ch) * 21 + JUNG.index(v)) * 28:04X}"
                add(chr(int(cp, 16)), cp, GAP_CLIP if i else GAP_SET)

    out.append(silence(TAIL))
    return out, script


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join("practice", "ㅅㅈㅊ-drill.mp3"))
    ap.add_argument("--json", help="write the clip timeline here for checking")
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    chunks, script = build(manifest)
    total = sum(len(c) for c in chunks) / RATE

    wav_path = os.path.join(ROOT, "practice", "ㅅㅈㅊ-drill.wav")
    os.makedirs(os.path.dirname(wav_path), exist_ok=True)
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        for c in chunks:
            w.writeframes(c.tobytes())

    out_path = os.path.join(ROOT, args.out)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path,
                    "-ac", "1", "-ar", str(RATE), "-b:a", "64k", out_path], check=True)

    clips = len(script)
    gaps = sum(1 for s in script if s[1] > 0)
    print(f"clips: {clips}  gaps: {gaps}  total: {total:.1f}s ({int(total//60)}:{total%60:04.1f})")
    print(f"wav: {wav_path}  ({os.path.getsize(wav_path)/1e6:.1f} MB)")
    print(f"mp3: {out_path}  ({os.path.getsize(out_path)/1e3:.0f} KB)")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump([{"clip": s[0], "gap_before": s[1], "dur": round(s[2], 3)} for s in script],
                      fh, ensure_ascii=False, indent=1)
        print(f"timeline: {args.json}")


if __name__ == "__main__":
    main()
