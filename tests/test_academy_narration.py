from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NARRATION = ROOT / "academy" / "narration"


def _range(spec):
    if isinstance(spec, int):
        return spec, spec
    if isinstance(spec, list):
        return int(spec[0]), int(spec[-1])
    text = str(spec)
    if "-" in text:
        start, end = text.split("-", 1)
        return int(start), int(end)
    return int(text), int(text)


def test_every_session_has_two_clips_with_overviews():
    for session in range(1, 11):
        clips = sorted((NARRATION / f"session-{session}").glob("*.yaml"))
        assert len(clips) >= 2, session
        for clip in clips:
            data = yaml.safe_load(clip.read_text())
            assert len(" ".join(str(data["overview"]).split())) > 40
            code = (clip.parent / data["file"]).resolve()
            assert code.is_file(), code
            nlines = len(code.read_text().splitlines())
            assert data["segments"]
            for segment in data["segments"]:
                start, end = _range(segment["lines"])
                assert 1 <= start <= end <= nlines, (clip.name, start, end, nlines)
                assert str(segment["say"]).strip()
