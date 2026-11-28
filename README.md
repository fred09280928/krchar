# KRChar — Korean Dubeolsik typing drill

**Live:** https://krchar-d1.fred0928.workers.dev/ · **Repo:** https://github.com/fred09280928/krchar

Drill table of Korean Hangul characters with the exact 두벌식 (Dubeolsik) keystrokes that
produce each one, filtered down to characters that actually occur in Korean text.

## Layout

```
KRChar/
├── README.md
├── code/
│   └── validate_krchar.py      # recomputes every key sequence -> character
└── data/
    ├── KRChar.csv              # the drill data (833 rows)
    ├── KRChar.json             # same data as records
    ├── syllable-coverage.json  # attestation per character
    ├── ko_full.txt.gz          # Korean frequency corpus (688,129 word forms)
    └── kengdic.tsv.gz          # Korean–English dictionary (133,765 entries)
```

## Source of truth

- Google Sheet **HermesLang** (owner: happykero3000@gmail.com)
  `https://docs.google.com/spreadsheets/d/1rMfAD58GaWRvqzuKXC8woAFX3QJqW2UV8mLXYasLfzk/edit`
- Tab **KRChar** (`sheetId 1667330595`), columns `A:category | B:Hangul | C:RR | D:Dubeolsik key | E:memo`
- `data/` holds a snapshot export; edits made in the sheet must be re-exported.

## Files

| File | What it is |
|---|---|
| `data/KRChar.csv` | Snapshot export of the tab (header + 833 data rows) — the drill data |
| `data/KRChar.json` | Same data as records, for scripted use |
| `data/syllable-coverage.json` | Per-syllable evidence: corpus hits, distinct words, attested flag; letter rows carry `kind: jamo` |
| `code/validate_krchar.py` | Self-check: rebuilds every key sequence through the layout and compares with the Hangul column |
| `data/ko_full.txt.gz` | Korean word-frequency list, OpenSubtitles 2018, 688,129 forms (`hermitdave/FrequencyWords`, `content/2018/ko/ko_full.txt`) |
| `data/kengdic.tsv.gz` | Korean–English dictionary dump, 133,765 entries (`garfieldnate/kengdic`, `kengdic.tsv`) |

## Data model

`Dubeolsik key` is the literal keystroke sequence — press these keys and the IME emits the
character in `Hangul`, nothing more, nothing fewer. Lowercase = the key as-is; uppercase =
same key with Shift (`W`=Shift+w=ㅉ, `R`=Shift+r=ㄲ, `O`=Shift+o=ㅒ, `P`=Shift+p=ㅖ).
No spaces, no `+`, no commas. One standalone jamo is a single letter (`r` = ㄱ); a syllable
concatenates its jamo (`rk` = 가, `Rnfg` = 꿇, `ahrt` = 몫).

## Categories (current: 833 rows)

Alphabet units — 40 rows:

- `L1c` 13 — consonants that Korean speakers do type alone: ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅅ ㅇ ㅈ ㅊ ㅋ ㅌ ㅎ (ㅋㅋㅋ, ㅇㅇ, ㄱㄱ, ㄹㅇ, ㅁㅊ, ㅅㄱ, ㅈㅅ, ㅂㅂ, ㄷㄷ, ㅊㅋ, ㅌㅌ)
- `L1v` 3 — vowels typed alone as emoticons: ㅠㅠ, ㅜㅜ, ㅗ
- `L0c` 6 — consonants that never stand alone: ㄲ ㄸ ㅃ ㅆ ㅉ ㅍ
- `L0v` 7 — vowels that never stand alone: ㅏ ㅑ ㅓ ㅕ ㅛ ㅡ ㅣ
- `L0d` 11 — compound vowels / y-vowels, only ever inside a syllable: ㅐ ㅒ ㅔ ㅖ ㅘ ㅙ ㅚ ㅝ ㅞ ㅟ ㅢ

Syllables — 793 rows:

- `L1` 10 — ㅇ + basic vowel (아 야 어 여 오 요 우 유 으 이)
- `L2` 11 — ㅇ + ㅐ/ㅔ family (애 얘 에 예 와 왜 외 워 웨 위 의)
- `L3` 174 — consonant + simple vowel (가 갸 거 겨 …)
- `L4` 155 — consonant + ㅐ/ㅔ/ㅒ/ㅖ vowels (개 걔 게 계 …)
- `L5` 409 — consonant + vowel + final consonant (각 간 갈 감 …)
- `L6` 34 — double batchim (몫 넋 앉 값 없 꿇 …)

## Inclusion rule

A syllable stays in the table only if it occurs in **either** source:

1. the OpenSubtitles 2018 Korean frequency list (688,129 word forms), or
2. the kengdic Korean–English dictionary (133,765 headwords).

The union is 2,364 syllables. Using both matters: the subtitle corpus alone drops real
words such as 홰 (횃불), 몌, 좨, which the dictionary keeps.

Filtered out from the original 884 rows (51 total):

- 1 duplicate: L5 `구` (already present as L3)
- 41 L4 rows with no occurrence in either source: 끠 냬 댸 뚸 뛔 럐 먜 뫠 믜 뱨 볘 붜 붸 뼤 뽸 뾔 뿨 쀄 쀠 쁴 싀 썌 쒜 즤 쪠 쮀 쯰 챼 쳬 촤 츼 컈 킈 턔 톄 톼 퍠 퐤 푀 풰 픠
- 4 L3 rows with no occurrence in either source: 꾜 뚀 뜌 뺘
- 5 rows surviving only on archaic/dialect dictionary entries: 툐 (교툐 표지), 퍄, 몌 (썅몌), 좨 (좨치다), 훙 (허훙)

Kept despite being dictionary-only: 홰 (홰치다, 횃불 — modern).

## Key column repairs

Nine cells were corrected so the keys actually produce the stated character:
`삯 tkr→tkrt`, `많 dksg→aksg`, `읽 dlf→dlfr`, `얇 dlfq→difq`, `싫 tlfh→tlfg`, `잃 dlfh→dlfg`
(ㅎ is `g`, not `h`), and the uppercase-only rule restored on `끓/뚫/꿇` (`RmfG→Rmfg`,
`EnfG→Enfg`, `RnfG→Rnfg`). Rows 2–62 were also rewritten from the verbose
`Shift + r` / `d + h + k` notation to the compact `R` / `dhk` form. `ㅒ`/`ㅖ` are single
keystrokes (`O`, `P`) — the earlier `Shift + o, i` form would have typed an extra ㅑ.

## Memo column (memory aids)

Column E is a hint, not data: each cell reads `<pictures> = keys`, one picture word per key press and
then the literal characters to type — copied from column D, so uppercase there really means Shift.

- **Uppercase picture = Shift held.** `dog orange` = 애 (d, o); `dog ORANGE` = 얘 (d, O).
- The picture words come from one fixed set of 26, so learning 26 words decodes every row:

```
a apple   b ball    c cat     d dog     e egg     f fish    g gun
h hat     i ink     j jam     k kite    l lion    m moon    n nose
o orange  p pen     q queen   r rabbit  s snake   t tiger   u umbrella
v violin  w whale   x x-ray   y yoyo    z zebra
```

- Single letters are just one picture: ㄱ `r` → `rabbit = r`, ㅠ `b` → `ball = b`.
- The part after `=` is the key sequence verbatim: `꾸` → `RABBIT nose = Rn` (Shift on the first key only).
- A few rows use a real English word whose consonants are the keys, kept as exceptions:
  아 `duke`, 가 `ark`, 강 `arked` (ark + d).
- **L0 rows are deliberately left blank** — the letter layer is never drilled, so it needs no hint.
- Memos are hints, not the answer key: for a real test, hide column E.

## Audio (pronunciation for each quiz question)

Every quiz-able row has one short clip: 793 syllables + 13 consonant names + 3 vowel sounds
= **809 clips, ~2 MB**. L0 rows get no audio (never quizzed).

| Row kind | Clip | Example |
|---|---|---|
| syllable | the syllable itself | 가 → `audio/syl/AC00 가.mp3` |
| consonant letter | its letter name | ㄱ → `audio/jamo/3131 ㄱ.mp3`, spoken 「기역」 |
| vowel letter | the syllable carrying it | ㅏ → `audio/jamo/314F ㅏ.mp3`, spoken 「아」 |

**The audio is committed** (`audio/`, 3.2 MB) so the published page can play it. It is
synthesised by Microsoft Edge TTS (`ko-KR-HyunsuMultilingualNeural`), which is an unofficial client of
the Edge Read Aloud service: Microsoft publishes no licence granting redistribution, so the
clips are "personal use" in spirit and the project owner accepted the residual risk. If a
takedown is ever requested, the fix is one commit:

```bash
rm -rf audio/                       # drop the clips
git commit -am "remove TTS audio"    # page stays fully usable, just silent
```

The app treats a missing clip as "no sound" rather than an error, so nothing else changes.
`data/audio-manifest.json` (character, code point, spoken text, duration, sha256) stays in
the repository either way — it is plain metadata and it is what a future re-recording or a
licensed replacement would be built from.

```bash
pip install -U 'edge-tts>=7.3'      # older versions get HTTP 403 from the service
python3 code/make_audio.py          # only missing clips; --force to redo all
python3 code/make_audio.py --limit 50   # batch it
```

On this Mac a working 7.3.1 lives in `~/.venvs/edge-tts/bin/` (the Homebrew 7.2.7 returns
403); pass it explicitly with `--edge-tts ~/.venvs/edge-tts/bin/edge-tts`.

Voice: every clip (809 + the correct-answer bell) is recorded with the macOS Korean voice
`Yuna` via `say -v Yuna`, driven by `code/make_audio_l1_yuna.py --scope all`. The edge-tts pipeline
(`make_audio.py`, `ko-KR-HyunsuMultilingualNeural`) is kept as the fallback for re-recording, but the
male voices were rejected by ear — the user found them irritating during long listening drills. The
manifest records `voice`/`engine` per clip and flags the Apple voice as personal use only.

The script trims leading/trailing silence, normalises to −16 LUFS, and writes mono
24 kHz 48 kbps MP3 (0.29–0.79 s per clip, 809 clips ≈ 3.2 MB). Quiz flow: show the
question, play its clip, then accept the keystrokes.

**Known audio quirks (voice, not data).** 32 clip pairs are byte-identical, and most are
correct Korean: a double batchim is neutralised in isolation (값 = 갑, 몫 = 목, 싫 = 실,
많 = 만, 없 = 업 …) and ㅢ after a consonant is pronounced ㅣ (긔 = 기, 씌 = 씨). Harmless
here because the quiz shows the character and asks for the keystrokes. A few are the
voice's own normalisation and are arguably wrong — 읽 came out as 일 (should be 익),
읊 as 을, and 져/쇼/쳐 were merged with 저/쇼/처. Regenerate those rows with a different
engine if they matter.

If the voice or licensing needs to change, swap `VOICE` (edge-tts), or replace the file
writer with a local engine — MeloTTS KR in `~/Documents/Hermes/myProject/AI/TTS` is
MIT-licensed and its output *may* be redistributed, but its Korean voice is
single-speaker female (measured F0 ≈ 172 Hz).

## Database (Cloudflare D1)

The long-term home for the data is a D1 database, not the Google Sheet — the sheet was the
draft, and once the table is frozen the whole thing lives here.

- D1 `krchar` — `database_id 550364a8-da18-43a9-9291-76107bbb1760` — region APAC
- Tables: `cards` (`cp` PK, `hangul`, `category`, `rr`, `keys`, `memo`, `ord`),
  `card_stats` (`owner`, `cp`, `weight`, `correct`, `wrong`, `last`),
  `reviews`, `meta`
- Seeded 2026-11-26: **833 rows**, 809 with memo, category counts identical to the CSV

```bash
python3 code/export_seed.py                                  # CSV -> d1/seed.sql
npx wrangler d1 execute krchar --remote --file=d1/schema.sql
npx wrangler d1 execute krchar --remote --file=d1/seed.sql
```

Content (`cards`, including `memo`) is shared; `weight` and the answering history are
per owner, exactly like `esflash-d1`. No write-back to the sheet is needed any more, so
there is no `sheet_pending` queue and no `row_no` column.

## Web app (Worker + D1)

`worker/` is the drill itself: `src/index.js` (API) and `public/index.html` (quiz) plus
`public/table.html` (browse/edit all 833 cards). Static pages and `/audio/*` are served by
the same Worker, so there is no CORS and no second host.

Run it locally:

```bash
cd worker
npx wrangler d1 execute krchar --local --file=../d1/schema.sql
npx wrangler d1 execute krchar --local --file=../d1/seed.sql
../scripts/sync_audio.sh                  # copies audio/ into worker/public/audio/ (gitignored)
echo 'ADMIN_TOKEN=dev-token' > .dev.vars  # lets ✏️ edits work locally
npx wrangler dev --port 8799
```

Then `node scripts/smoke.mjs http://127.0.0.1:8799` — 17 assertions covering level pools,
weight changes, key validation, the admin token and today's counters.

Answer modes: the prompt is always the character; **Dubeolsik** grades the physical keys
(`R` = Shift+r) captured on `keydown`, **RR** grades the romanisation from `r` column C.
Levels are cumulative — L2 drills L1\* + L2 (37 cards), L3 → 211, L4 → 366. L0 never appears. Picking is weight roulette and never serves the same card twice in a row.

Keys: Enter submits; with the answer on screen (third wrong, or the 2 s window after a correct
answer) Enter also advances to the next card, so the Next button never needs the mouse.

File names are `<codepoint> <hangul>.mp3` — the codepoint first so sorting and matching by cp still
work, the character after the space so you can tell at a glance which clip is which. URLs are
percent-encoded in the page (`AC00 가.mp3` → `AC00%20%EA%B0%80.mp3`); renaming is done by
`code/rename_audio_files.py`, which also rewrites the manifest.

Listening drill for confusable letters: `code/make_confusable_drill.py` splices the existing clips into
`practice/ㅅㅈㅊ-drill.mp3` — letter names ㅅ·ㅈ·ㅊ three rounds, then ㅓ/ㅡ/ㅗ/ㅜ/ㅣ/ㅏ groups (서저처,
스즈츠, 소조초, 수주추, 시지치, 사자차) each three times, 1 s between clips and 2 s between rounds.
No new audio: it concatenates the files already in `audio/`.

Video version of the drill: `code/make_confusable_drill_video.py` renders one white character per clip
(1080×1080, black background, Apple SD Gothic Neo Bold, auto-sized to ~78 % of the frame) and muxes it
with the mp3 using the drill's timeline, so each character appears 0.1 s before its sound.
`make_confusable_drill.py` records decoded-PCM durations — using the manifest's ffprobe durations
drags the picture ~3 s behind the audio over 63 clips.

Answer feedback: a correct answer plays a short bell (`audio/ui/ding.mp3`, 0.5 s) the moment it is
judged, then the 2 s advance and the next pronunciation; a wrong answer stays silent and replays
the word instead.

Deploy: `cd worker && npx wrangler secret put ADMIN_TOKEN && npx wrangler deploy`.

## Verify

```
cd code && python3 validate_krchar.py
```

Expected: `RESULT: PASS` — 833 rows, 0 mismatch, 0 unparseable, no duplicates, all
syllables attested. The script reads `../data/KRChar.csv` by default and also cross-checks
`../data/syllable-coverage.json`; pass a path as argv[1] to check a different file.

The table is settled; this check is only needed after an edit.

## Updating

1. Edit the Google Sheet.
2. Re-export `A1:E` of the KRChar tab to `data/KRChar.csv` / `data/KRChar.json`.
3. Re-run `code/validate_krchar.py`; fix any row whose keys no longer produce its character.
4. For new syllables, check occurrence against the two gzipped sources and refresh
   `data/syllable-coverage.json`.

Note: this folder lives in iCloud Drive. Hermes' lifecycle guard refuses to execute scripts
from cloud-synced paths — copy the folder somewhere local (e.g. `~/Documents/myCode/KRChar`)
if the validator must run under Hermes.
