#!/usr/bin/env python3
"""Turn the ㅅ·ㅈ·ㅊ listening drill into a video: black screen, white character.

The character changes exactly when its clip starts (a tenth of a second early so
the eye is already there when the sound arrives) and stays on screen through the
pause that follows it, so there is nothing to read during silence.

    /usr/bin/python3 code/make_confusable_drill_video.py \
        --timeline practice/ㅅㅈㅊ-drill.timeline.json \
        --audio practice/ㅅㅈㅊ-drill.mp3 \
        --out practice/ㅅㅈㅊ-drill.mp4
"""
import argparse
import json
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_INDEX = 6          # Apple SD Gothic Neo Bold
SIZE = 1080
BG = (0, 0, 0)
FG = (255, 255, 255)
FILL_RATIO = 0.78       # character occupies ~78 % of the frame height
LEAD, TAIL = 0.4, 0.8   # must match make_confusable_drill.py
EARLY = 0.10            # show the character slightly before its sound


def biggest_font(draw, ch, target_w, target_h):
    lo, hi, best = 40, 1400, 40
    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(FONT, mid, index=FONT_INDEX)
        box = draw.textbbox((0, 0), ch, font=font)
        w, h = box[2] - box[0], box[3] - box[1]
        if w <= target_w and h <= target_h:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def render(ch, path):
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    size = biggest_font(draw, ch, SIZE * FILL_RATIO, SIZE * FILL_RATIO)
    font = ImageFont.truetype(FONT, size, index=FONT_INDEX)
    draw.text((SIZE / 2, SIZE / 2), ch, font=font, fill=FG, anchor="mm")
    img.save(path)
    return size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="practice/ㅅㅈㅊ-drill.timeline.json")
    ap.add_argument("--audio", default="practice/ㅅㅈㅊ-drill.mp3")
    ap.add_argument("--out", default="practice/ㅅㅈㅊ-drill.mp4")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tl = json.load(open(os.path.join(root, args.timeline), encoding="utf-8"))

    # start time of every clip, straight from the drill's own timeline
    starts, t = [], LEAD
    for item in tl:
        t += item["gap_before"]
        starts.append(t)
        t += item["dur"]
    total = t + TAIL

    tmp = tempfile.mkdtemp()
    frames, last_ch = {}, None
    concat = []
    for i, item in enumerate(tl):
        ch = item["clip"].split("(")[0]          # 시옷(ㅅ) -> ㅅ
        if ch not in frames:
            path = os.path.join(tmp, f"f{len(frames):02d}.png")
            px = render(ch, path)
            frames[ch] = path
            print(f"  {ch}  font {px}px")
        begin = max(0.0, starts[i] - EARLY)
        end = (starts[i + 1] - EARLY) if i + 1 < len(tl) else total
        concat.append((frames[ch], round(end - begin, 3)))
        last_ch = frames[ch]

    list_path = os.path.join(tmp, "list.txt")
    with open(list_path, "w", encoding="utf-8") as fh:
        for path, dur in concat:
            fh.write(f"file '{path}'\nduration {dur}\n")
        fh.write(f"file '{last_ch}'\n")           # concat needs the last frame repeated

    silent = os.path.join(tmp, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", list_path, "-vf", "fps=30", "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", "-crf", "20", silent], check=True)

    out = os.path.join(root, args.out)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent,
                    "-i", os.path.join(root, args.audio),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", out], check=True)

    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration,size:stream=codec_type,width,height",
                            "-of", "json", out], capture_output=True, text=True).stdout
    info = json.loads(probe)
    streams = {s["codec_type"]: s for s in info["streams"]}
    print(f"\nvideo: {streams['video']['width']}x{streams['video']['height']} "
          f"{float(info['format']['duration']):.1f}s "
          f"{int(info['format']['size'])/1e6:.1f} MB")
    print(f"clips: {len(tl)}  distinct characters: {len(frames)}  out: {args.out}")


if __name__ == "__main__":
    main()
