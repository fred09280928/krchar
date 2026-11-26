#!/usr/bin/env python3
"""Validate KRChar.csv — every Dubeolsik key sequence must reproduce its Hangul.

Usage:
    python3 validate_krchar.py [path/to/KRChar.csv]

Checks, in order:
  1. key sequence -> jamo -> composed character == Hangul column
  2. duplicate Hangul syllables
  3. rows with an empty Hangul / key cell
  4. category counts
  5. optional: syllable-coverage.json says the syllable occurs in Korean
     (corpus or dictionary). Missing coverage file -> check skipped.

Exit code 0 = all checks passed. No third-party packages required.
"""
import csv
import json
import os
import re
import sys

KEY = {
    'q': 'ㅂ', 'w': 'ㅈ', 'e': 'ㄷ', 'r': 'ㄱ', 't': 'ㅅ', 'y': 'ㅛ', 'u': 'ㅕ',
    'i': 'ㅑ', 'o': 'ㅐ', 'p': 'ㅔ', 'a': 'ㅁ', 's': 'ㄴ', 'd': 'ㅇ', 'f': 'ㄹ',
    'g': 'ㅎ', 'h': 'ㅗ', 'j': 'ㅓ', 'k': 'ㅏ', 'l': 'ㅣ', 'z': 'ㅋ', 'x': 'ㅌ',
    'c': 'ㅊ', 'v': 'ㅍ', 'b': 'ㅠ', 'n': 'ㅜ', 'm': 'ㅡ',
    'Q': 'ㅃ', 'W': 'ㅉ', 'E': 'ㄸ', 'R': 'ㄲ', 'T': 'ㅆ', 'O': 'ㅒ', 'P': 'ㅖ',
}
INI = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
MED = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
FIN = [''] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")
VV = {'ㅗㅏ': 'ㅘ', 'ㅗㅐ': 'ㅙ', 'ㅗㅣ': 'ㅚ', 'ㅜㅓ': 'ㅝ', 'ㅜㅔ': 'ㅞ',
      'ㅜㅣ': 'ㅟ', 'ㅡㅣ': 'ㅢ', 'ㅑㅣ': 'ㅒ', 'ㅕㅣ': 'ㅖ', 'ㅏㅣ': 'ㅐ', 'ㅓㅣ': 'ㅔ'}
CC = {'ㄱㅅ': 'ㄳ', 'ㄴㅈ': 'ㄵ', 'ㄴㅎ': 'ㄶ', 'ㄹㄱ': 'ㄺ', 'ㄹㅁ': 'ㄻ',
      'ㄹㅂ': 'ㄼ', 'ㄹㅅ': 'ㄽ', 'ㄹㅌ': 'ㄾ', 'ㄹㅍ': 'ㄿ', 'ㄹㅎ': 'ㅀ', 'ㅂㅅ': 'ㅄ'}


def syllable(ini, med, fin=''):
    return chr(0xAC00 + (INI.index(ini) * 21 + MED.index(med)) * 28 + FIN.index(fin))


def compose(keys):
    """Keystrokes -> the character a Korean IME produces, or None if impossible."""
    if not keys or any(c not in KEY for c in keys):
        return None
    j = [KEY[c] for c in keys]
    if len(j) == 1:
        return j[0]                                  # single jamo (ㄱ, ㅏ, ㅒ ...)
    if j[0] in MED:                                  # vowel cluster (ㅘ = hk)
        med = j[0]
        for nxt in j[1:]:
            if nxt in MED and (med + nxt) in VV:
                med = VV[med + nxt]
            else:
                return None
        return med
    if j[0] not in INI or j[1] not in MED:
        return None
    med, rest = j[1], j[2:]
    if rest and rest[0] in MED and (med + rest[0]) in VV:   # C + compound vowel
        med = VV[med + rest[0]]
        rest = rest[1:]
    if not rest:
        return syllable(j[0], med)
    if len(rest) == 1 and rest[0] in FIN:
        return syllable(j[0], med, rest[0])
    if len(rest) == 2 and (rest[0] + rest[1]) in CC:        # double batchim
        return syllable(j[0], med, CC[rest[0] + rest[1]])
    return None


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    default_csv = os.path.join(base, '..', 'data', 'KRChar.csv')
    path = sys.argv[1] if len(sys.argv) > 1 else default_csv
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    bad, unparsed, empty, seen = [], [], [], {}
    counts = {}
    for n, r in enumerate(rows, start=2):
        syl = (r.get('Hangul') or '').strip()
        keys = (r.get('Dubeolsik key') or '').strip()
        cat = (r.get('category') or '').strip()
        counts[cat] = counts.get(cat, 0) + 1
        if not syl or not keys:
            empty.append((n, syl, keys))
            continue
        got = compose(keys)
        if got is None:
            unparsed.append((n, syl, keys))
        elif got != syl:
            bad.append((n, syl, keys, got))
        seen[syl] = seen.get(syl, 0) + 1

    dups = {s: c for s, c in seen.items() if c > 1}
    # RR column: it is the answer key in RR mode, so it must be a single lowercase
    # ASCII token — no spaces, no slashes, no "ng / silent" style commentary.
    bad_rr = []
    for n, r in enumerate(rows, start=2):
        rr = (r.get('RR') or '').strip()
        if not rr or not re.fullmatch(r'[a-z]+', rr):
            bad_rr.append((n, (r.get('Hangul') or '').strip(), rr))
    total = len(rows)
    print(f"file      : {path}")
    print(f"rows      : {total}")
    print(f"categories: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda x: (len(x[0]), x[0]))))
    print(f"key check : {total - len(bad) - len(unparsed) - len(empty)} pass, {len(bad)} mismatch, {len(unparsed)} unparseable, {len(empty)} empty")
    print(f"rr check  : {total - len(bad_rr)} clean, {len(bad_rr)} malformed (expect single [a-z]+ token)")
    print(f"duplicates: {dups if dups else 'none'}")

    for n, syl, keys, got in bad[:20]:
        print(f"  MISMATCH  row {n}: {syl}  keys={keys!r} -> {got}")
    for n, syl, keys in unparsed[:20]:
        print(f"  UNPARSE   row {n}: {syl}  keys={keys!r}")
    for n, syl, keys in empty[:20]:
        print(f"  EMPTY     row {n}: hangul={syl!r} keys={keys!r}")
    for n, syl, rr in bad_rr[:20]:
        print(f"  BAD RR    row {n}: {syl}  rr={rr!r}")

    cov_path = os.path.join(os.path.dirname(os.path.abspath(path)), 'syllable-coverage.json')
    if os.path.exists(cov_path):
        cov = json.load(open(cov_path, encoding='utf-8'))
        syl_rows = [s for s in seen if cov.get(s, {}).get('kind') != 'jamo']
        jamo_rows = len(seen) - len(syl_rows)
        missing = [s for s in syl_rows if not cov.get(s, {}).get('in_corpus_or_dict')]
        unknown = [s for s in syl_rows if s not in cov]
        print(f"coverage  : {len(syl_rows) - len(missing)} syllables attested, "
              f"{len(missing)} unverified, {jamo_rows} jamo rows (not applicable), "
              f"{len(unknown)} not annotated")
        if missing:
            print("  NOT IN CORPUS OR DICTIONARY:", " ".join(missing[:40]))

    ok = not bad and not unparsed and not empty and not dups and not bad_rr
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
