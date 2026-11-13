#!/usr/bin/env python3
"""Turn a code file plus a narration script into a narrated MP4 walkthrough.

Visual style matches the Session 1 reference renderer: syntax-highlighted code,
the current line or block highlighted, and a caption bar. Speech is edge-tts
only (en-US-AndrewNeural by default). Other engines are not a fallback.

Usage: python3 academy/render_walkthrough.py script.yaml -o out.mp4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer, get_lexer_for_filename
from pygments.styles import get_style_by_name

W, H = 1280, 720
TITLE_H, CAP_H = 52, 120
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG, GUTTER_BG = (30, 31, 38), (24, 25, 31)
HL_BG, HL_BAR = (62, 68, 92), (255, 196, 0)
DIM = 0.55
FPS = 5


def hexrgb(h, default=(220, 220, 220)):
    if not h:
        return default
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def tokenize(code, filename, style_name):
    try:
        lexer = get_lexer_for_filename(filename, stripnl=False)
    except Exception:
        lexer = PythonLexer(stripnl=False)
    style = get_style_by_name(style_name)
    lines, cur = [], []
    for ttype, val in lex(code, lexer):
        while ttype not in style.styles and ttype.parent is not None:
            ttype = ttype.parent
        st = style.style_for_token(ttype)
        color = hexrgb(st["color"])
        parts = val.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                lines.append(cur)
                cur = []
            if part:
                cur.append((part.replace("\t", "    "), color, st["bold"]))
    lines.append(cur)
    n = len(code.rstrip("\n").split("\n"))
    return lines[:n]


def parse_range(r):
    if isinstance(r, int):
        return r, r
    if isinstance(r, (list, tuple)):
        return int(r[0]), int(r[-1])
    s = str(r).strip()
    if "-" in s:
        a, b = s.split("-", 1)
        return int(a), int(b)
    return int(s), int(s)


def wrap_px(draw, text, font, maxw):
    words, out, line = text.split(), [], ""
    for w in words:
        t = (line + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            line = t
        else:
            if line:
                out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def render_frame(lines, hl, top, cfg, caption, idx, total, path):
    fs = int(cfg["font_size"])
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    small = ImageFont.truetype(SANS, 20)
    cap_font = ImageFont.truetype(SANS, 22)
    d.rectangle([0, 0, W, TITLE_H], fill=(18, 18, 24))
    d.text((20, 14), cfg["title"], font=small, fill=(235, 235, 235))
    prog = (
        f"{idx}/{total}  ·  lines {hl[0]}–{hl[1]}"
        if hl[0] != hl[1]
        else f"{idx}/{total}  ·  line {hl[0]}"
    )
    d.text((W - 20 - d.textlength(prog, font=small), 14), prog, font=small, fill=(255, 196, 0))

    area_top, area_bot = TITLE_H + 10, H - CAP_H - 6
    # Shrink the code face until the visible lines fit. The picture stays 720p.
    gutter_w = 0
    font = bold = None
    lh = visible = 0
    while fs >= 13:
        font = ImageFont.truetype(FONT_PATH, fs)
        bold = ImageFont.truetype(FONT_BOLD, fs)
        lh = int(fs * 1.45)
        gutter_w = int(d.textlength("0000", font=font)) + 28
        visible = max(1, (area_bot - area_top) // lh)
        widest = 0
        for i in range(top, min(len(lines), top + visible)):
            x = 0
            for txt, _col, b in lines[i]:
                face = bold if b else font
                x += d.textlength(txt, font=face)
            widest = max(widest, x)
        if gutter_w + 18 + widest <= W - 12:
            break
        fs -= 1

    d.rectangle([0, TITLE_H, gutter_w, H - CAP_H], fill=GUTTER_BG)
    for i in range(top, min(len(lines), top + visible)):
        ln = i + 1
        y = area_top + (i - top) * lh
        on = hl[0] <= ln <= hl[1]
        if on:
            d.rectangle([gutter_w, y - 2, W, y + lh - 2], fill=HL_BG)
            d.rectangle([gutter_w, y - 2, gutter_w + 5, y + lh - 2], fill=HL_BAR)
        num = str(ln)
        d.text(
            (gutter_w - 12 - d.textlength(num, font=font), y),
            num,
            font=font,
            fill=(255, 196, 0) if on else (110, 112, 125),
        )
        x = gutter_w + 16
        for txt, col, b in lines[i]:
            c = col if on else tuple(int(v * DIM + BG[k] * (1 - DIM)) for k, v in enumerate(col))
            f = bold if b else font
            d.text((x, y), txt, font=f, fill=c)
            x += d.textlength(txt, font=f)
    d.rectangle([0, H - CAP_H, W, H], fill=(14, 14, 18))
    if cfg["captions"]:
        cl = wrap_px(d, caption, cap_font, W - 60)
        if len(cl) > 4:
            cl = cl[:4]
            cl[-1] = (cl[-1][: max(0, len(cl[-1]) - 1)] + "…") if cl[-1] else "…"
        y0 = H - CAP_H + (CAP_H - len(cl) * 28) // 2
        for j, t in enumerate(cl):
            d.text((30, y0 + j * 28), t, font=cap_font, fill=(230, 230, 230))
    img.save(path)
    return visible


async def _tts_one(text, voice, rate, out, sem):
    import edge_tts

    async with sem:
        last = None
        for attempt in range(5):
            try:
                await asyncio.wait_for(
                    edge_tts.Communicate(text, voice, rate=rate).save(out),
                    timeout=40,
                )
                if os.path.getsize(out) > 8000:
                    return "edge-tts"
                last = RuntimeError("audio too small")
            except Exception as exc:  # noqa: BLE001 — retry then fail closed
                last = exc
                print(
                    f"  edge-tts attempt {attempt + 1} failed ({exc.__class__.__name__}: {exc})",
                    file=sys.stderr,
                )
                await asyncio.sleep(1.6 * (attempt + 1))
        raise RuntimeError(f"edge-tts failed for a segment: {last}")


def synthesize_all(texts, cfg, paths):
    sem = asyncio.Semaphore(2)

    async def run():
        return await asyncio.gather(
            *[_tts_one(t, cfg["voice"], cfg["rate"], str(p), sem) for t, p in zip(texts, paths)]
        )

    engines = asyncio.run(run())
    bad = sorted({e for e in engines if e != "edge-tts"})
    if bad:
        raise RuntimeError(f"refusing mixed TTS engines: {bad}")
    return engines


def duration(path):
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def encode_clip(png, mp3, mp4, pad):
    dur = duration(str(mp3)) + pad
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(png),
            "-i",
            str(mp3),
            "-af",
            f"apad=pad_dur={pad}",
            "-t",
            f"{dur:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-ar",
            "44100",
            "-ac",
            "1",
            str(mp4),
        ],
        check=True,
    )
    return dur


def render(script: Path, out: Path, voice: str | None = None, keep: bool = False) -> dict:
    spec = (json.loads if script.suffix == ".json" else yaml.safe_load)(script.read_text())
    code_path = (script.parent / spec["file"]).resolve()
    if not code_path.is_file():
        raise SystemExit(f"code file not found: {code_path}")
    code = code_path.read_text()
    nlines = len(code.splitlines())
    cfg = {
        "title": spec.get("title", code_path.name)[:110],
        "voice": voice or spec.get("voice", "en-US-AndrewNeural"),
        "rate": spec.get("rate", "+0%"),
        "style": spec.get("style", "monokai"),
        "font_size": int(spec.get("font_size", 20)),
        "captions": spec.get("captions", True),
        "pad": float(spec.get("pause", 0.35)),
    }
    if cfg["voice"] != "en-US-AndrewNeural":
        # Academy standard. A script may not silently switch voices.
        print(f"overriding voice {cfg['voice']} -> en-US-AndrewNeural", file=sys.stderr)
        cfg["voice"] = "en-US-AndrewNeural"
    lines = tokenize(code, code_path.name, cfg["style"])
    segs = spec["segments"]
    work = Path(tempfile.mkdtemp(prefix="wt_"))
    lh = int(cfg["font_size"] * 1.45)
    visible = (H - CAP_H - 6 - TITLE_H - 10) // lh
    ranges = []
    texts = []
    for s in segs:
        hl = parse_range(s.get("lines", s.get("range")))
        if hl[0] < 1 or hl[1] > nlines or hl[0] > hl[1]:
            raise SystemExit(f"{script.name}: line range {hl} outside 1..{nlines}")
        ranges.append(hl)
        texts.append(" ".join(str(s["say"] if "say" in s else s["text"]).split()))
    mp3s = [work / f"a{i:03}.mp3" for i in range(1, len(segs) + 1)]
    print(f"speaking {len(segs)} segments with edge-tts…", flush=True)
    engines = synthesize_all(texts, cfg, mp3s)
    clips = []
    top = 0
    from concurrent.futures import ThreadPoolExecutor

    jobs = []
    for i, s in enumerate(segs, 1):
        hl = ranges[i - 1]
        if hl[0] - 1 < top + 1 or hl[1] > top + visible - 2:
            top = max(
                0,
                min(
                    hl[0] - 1 - max(2, (visible - (hl[1] - hl[0] + 1)) // 3),
                    max(0, len(lines) - visible),
                ),
            )
        png = work / f"f{i:03}.png"
        mp4 = work / f"c{i:03}.mp4"
        render_frame(lines, hl, top, cfg, s.get("caption", texts[i - 1]), i, len(segs), png)
        jobs.append((png, mp3s[i - 1], mp4, cfg["pad"], hl))
        clips.append(mp4)
    with ThreadPoolExecutor(max_workers=2) as pool:
        durs = list(pool.map(lambda job: encode_clip(job[0], job[1], job[2], job[3]), jobs))
    for i, (dur, hl) in enumerate(zip(durs, ranges), 1):
        print(f"[{i}/{len(segs)}] lines {hl[0]}-{hl[1]}  {dur:.1f}s", flush=True)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(out),
        ],
        check=True,
    )
    dur = duration(out)
    size = out.stat().st_size
    print(f"wrote {out}  ({dur:.1f}s, {size/1e6:.1f} MB, tts: edge-tts)")
    if size > 100 * 1024 * 1024:
        raise SystemExit(f"{out} is over 100 MB")
    info = {
        "file": str(out),
        "seconds": round(dur, 2),
        "bytes": size,
        "engine": "edge-tts",
        "voice": cfg["voice"],
        "segments": len(segs),
        "engines": sorted(set(engines)),
    }
    out.with_suffix(".json").write_text(json.dumps(info, indent=2) + "\n")
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print("frames kept in", work)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("-o", "--out", default="walkthrough.mp4")
    ap.add_argument("--voice")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    info = render(Path(a.script), Path(a.out), voice=a.voice, keep=a.keep)
    sidecar = Path(a.out).with_suffix(".json")
    sidecar.write_text(json.dumps(info, indent=2) + "\n")


if __name__ == "__main__":
    main()
