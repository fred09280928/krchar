#!/usr/bin/env python3
"""Rename every clip to "<cp> <hangul>.mp3" so the folder is readable by eye.

    audio/jamo/314C.mp3  ->  audio/jamo/314C ㅌ.mp3

The codepoint prefix stays first so scripts and the manifest can still sort and
match by cp; the character after the space is for the human browsing the folder.
Run from the project root. Updated in place: data/audio-manifest.json `file`.

    /usr/bin/python3 code/rename_audio_files.py [--dry-run]
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "data", "audio-manifest.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    seen, renamed, skipped = set(), 0, 0
    for e in manifest:
        old_rel = e["file"]
        old = os.path.join(ROOT, old_rel)
        name = f"{e['cp']} {e['char']}.mp3"
        new_rel = os.path.join(os.path.dirname(old_rel), name).replace(os.sep, "/")
        new = os.path.join(ROOT, new_rel)

        if old_rel == new_rel:
            skipped += 1
            continue
        if not os.path.exists(old):
            sys.exit(f"missing source file: {old_rel}")
        if new_rel in seen:
            sys.exit(f"duplicate target name: {new_rel}")
        seen.add(new_rel)
        if args.dry_run:
            print(f"{old_rel}  ->  {new_rel}")
            continue
        if os.path.exists(new):
            sys.exit(f"target already exists: {new_rel}")
        os.rename(old, new)
        e["file"] = new_rel
        renamed += 1

    print(f"\n{renamed} renamed, {skipped} already named")
    if args.dry_run:
        return
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("manifest updated")


if __name__ == "__main__":
    main()
