#!/usr/bin/env python3
"""Render narration YAML to MP4. No git tags: clips read the working tree."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACADEMY = ROOT / "academy"
sys.path.insert(0, str(ACADEMY))

from render_walkthrough import render  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=int, action="append", dest="sessions")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    wanted = args.sessions or list(range(1, 11))
    out_root = ACADEMY / "build" / "videos"
    for n in wanted:
        folder = ACADEMY / "narration" / f"session-{n}"
        scripts = sorted(folder.glob("*.yaml"))
        if not scripts:
            raise SystemExit(f"no narration in {folder}")
        for script in scripts:
            dest = out_root / f"session-{n}" / f"{script.stem}.mp4"
            if dest.exists() and dest.stat().st_size > 100_000 and not args.force:
                print(f"keep {dest}")
                continue
            last = None
            for attempt in range(1, 4):
                try:
                    render(script, dest)
                    last = None
                    break
                except Exception as exc:  # noqa: BLE001
                    last = exc
                    print(f"retry {attempt} for {script.name}: {exc}", file=sys.stderr)
                    dest.unlink(missing_ok=True)
                    dest.with_suffix(".json").unlink(missing_ok=True)
            if last is not None:
                raise SystemExit(f"failed {script}: {last}")


if __name__ == "__main__":
    main()
