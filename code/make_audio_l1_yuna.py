#!/usr/bin/env python3
"""Re-record clips with the macOS Korean voice Yuna.

Why a separate script: the bulk of the deck is edge-tts (online, one female/male
voice), but L1 is only 26 cards and the user prefers the sound of Apple's own
`Yuna` for single letters. Keeping this as its own script means
`make_audio.py --force` still regenerates the whole deck with edge-tts without
silently flattening the L1 override — run this one afterwards.

    /usr/bin/python3 code/make_audio_l1_yuna.py            # L1 letters only
    /usr/bin/python3 code/make_audio_l1_yuna.py --scope all  # the whole deck

Writes audio/{syl,jamo}/<cp>.mp3 (mono 24 kHz 48 kbps, same as make_audio.py) and
updates data/audio-manifest.json (voice, engine, duration, sha256).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "data", "audio-manifest.json")
VOICE = "Yuna"
VOICE_LABEL = "Yuna (macOS ko_KR)"
ENGINE = "macos-say"
LICENSE = "Apple system voice - personal use only, not redistributable"

# Same filter chain as make_audio.py: trim leading/trailing silence (keeping
# 60 ms of lead-in and 120 ms of tail so a vowel can decay), then normalise.
AF = (
    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.06,"
    "areverse,"
    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.12,"
    "areverse,loudnorm=I=-16:TP=-1.5:LRA=11"
)


def pcm_duration(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "24000", "-"],
        capture_output=True,
    ).stdout
    return round(len(raw) / 2 / 24000, 4)


def synth(entry, out_path):
    aiff = tempfile.mktemp(suffix=".aiff")
    subprocess.run(["say", "-v", VOICE, "-o", aiff, entry["spoken"]], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", aiff, "-af", AF,
         "-ac", "1", "-ar", "24000", "-b:a", "48k", out_path],
        check=True,
    )
    os.unlink(aiff)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scope", choices=["l1", "all"], default="l1",
                    help="l1 = the 26 letters (default), all = every clip in the deck")
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    if args.scope == "l1":
        l1 = [e for e in manifest if e["category"] in ("L1c", "L1v", "L1")]
        if len(l1) != 26:
            sys.exit(f"expected 26 L1 cards, found {len(l1)}")
    else:
        l1 = list(manifest)

    changed = []
    for e in l1:
        out = os.path.join(ROOT, e["file"])
        if args.dry_run:
            print(f"would record {e['cp']} {e['char']:2} <- {e['spoken']}")
            continue
        synth(e, out)
        e["voice"], e["engine"], e["license"] = VOICE_LABEL, ENGINE, LICENSE
        e["duration"] = pcm_duration(out)
        e["sha256"] = hashlib.sha256(open(out, "rb").read()).hexdigest()
        changed.append((e["cp"], e["char"], e["spoken"], e["duration"]))
        print(f"  {len(changed):>3}/{len(l1)} {e['cp']} {e['char']:2} {e['spoken']:4} {e['duration']:.3f}s", flush=True)

    if args.dry_run:
        return
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\n{len(changed)} clips re-recorded with {VOICE_LABEL}; manifest updated")
    print(f"duration range: {min(c[3] for c in changed):.3f}-{max(c[3] for c in changed):.3f}s")


if __name__ == "__main__":
    main()
