#!/usr/bin/env python3
"""Build the static academy pages. Quiz keys are salted hashes, not letters."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import random
import sys
from collections import Counter
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[2]
ACADEMY = ROOT / "academy"
SITE = ACADEMY / "site"
sys.path.insert(0, str(ACADEMY))
sys.path.insert(0, str(ACADEMY / "content"))

from bank import QUIZZES  # noqa: E402
from course import SESSIONS  # noqa: E402
from quiz_checks import assert_guessers, assert_uniform_options  # noqa: E402

REPO = "https://github.com/neelsrejan/care-ops-agent"
MD = markdown.Markdown(extensions=["extra", "sane_lists"], output_format="html5")
N_SESSIONS = 10


def md(text: str) -> str:
    MD.reset()
    return MD.convert(text)


def salt_for(session: int, qid: str) -> str:
    return hashlib.sha256(f"coa-quiz|{session}|{qid}|v1".encode()).hexdigest()[:16]


def answer_hash(salt: str, choice: str) -> str:
    return hashlib.sha256(f"{salt}|{choice}".encode()).hexdigest()


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def repo_path(file_field: str) -> str:
    text = file_field.replace("\\", "/")
    marker = "src/"
    idx = text.find(marker)
    if idx >= 0:
        return text[idx:]
    name = Path(text).name
    return name


def load_clips(session: int) -> list[dict]:
    folder = ACADEMY / "narration" / f"session-{session}"
    clips = []
    for script in sorted(folder.glob("*.yaml")):
        spec = yaml.safe_load(script.read_text())
        path = repo_path(spec["file"])
        seconds = clip_seconds(session, script.stem)
        overview = " ".join(str(spec.get("overview", "")).split())
        if len(overview) < 40:
            raise SystemExit(f"{script} is missing an architecture overview")
        clips.append(
            {
                "stem": script.stem,
                "title": spec.get("title") or script.stem,
                "path": path,
                "seconds": seconds,
                "overview": overview,
                "src": f"videos/session-{session}/{script.stem}.mp4",
                "blob": f"{REPO}/blob/main/{path}",
            }
        )
    if len(clips) < 2:
        raise SystemExit(f"session {session} needs at least two narration clips")
    return clips


def clip_seconds(session: int, stem: str):
    manifest = ACADEMY / "content" / "durations.json"
    key = f"session-{session}/{stem}"
    if manifest.exists():
        data = json.loads(manifest.read_text())
        if key in data:
            return data[key]
    sidecar = ACADEMY / "build" / "videos" / f"session-{session}" / f"{stem}.json"
    if sidecar.exists():
        return json.loads(sidecar.read_text()).get("seconds")
    return None


def clock(seconds: float | None) -> str:
    if seconds is None:
        return "duration after render"
    total = int(round(seconds))
    return f"{total // 60}:{total % 60:02d}"


def published_choices(q: dict, salt: str) -> tuple[dict[str, str], str]:
    correct_text = q["choices"][q["correct"]]
    texts = [q["choices"][key] for key in "abcd"]
    random.Random(salt).shuffle(texts)
    labeled = {letter: texts[i] for i, letter in enumerate("abcd")}
    published = next(letter for letter, text in labeled.items() if text == correct_text)
    return labeled, published


def quiz_payload() -> dict:
    payload = {}
    if set(QUIZZES) != set(range(1, N_SESSIONS + 1)):
        raise SystemExit(f"expected quizzes 1..{N_SESSIONS}")
    for session, questions in QUIZZES.items():
        if len(questions) != 6:
            raise SystemExit(f"session {session} has {len(questions)} questions; want 6")
        built = []
        for i, q in enumerate(questions, 1):
            choices = q["choices"]
            if set(choices) != {"a", "b", "c", "d"}:
                raise SystemExit(f"session {session} q{i} choices {set(choices)}")
            if q["correct"] not in choices:
                raise SystemExit(f"session {session} q{i} missing correct")
            qid = f"s{session}q{i}"
            salt = salt_for(session, qid)
            labeled, published = published_choices(q, salt)
            built.append(
                {
                    "id": qid,
                    "prompt": q["prompt"],
                    "choices": [{"id": key, "text": labeled[key]} for key in "abcd"],
                    "salt": salt,
                    "answerHash": answer_hash(salt, published),
                    "explain": b64(q["why"]),
                }
            )
        payload[str(session)] = {"passMark": 0.8, "questions": built}
    return payload


def graded_items(payload: dict) -> list[dict]:
    items = []
    for session, pack in payload.items():
        for question in pack["questions"]:
            winner = None
            for choice in question["choices"]:
                if answer_hash(question["salt"], choice["id"]) == question["answerHash"]:
                    if winner is not None:
                        raise SystemExit(f"{question['id']} hashes to two letters")
                    winner = choice
            if winner is None:
                raise SystemExit(f"{question['id']} hash matches no choice")
            items.append(
                {
                    "session": int(session),
                    "prompt": question["prompt"],
                    "choices": question["choices"],
                    "correct": winner["id"],
                }
            )
    return items


def nav(active: int) -> str:
    by_id = {s["id"]: s for s in SESSIONS}
    parts = [
        '<a class="brand" href="index.html"><div class="mark">co</div><div><strong>care-ops-agent</strong><span>Academy</span></div></a>',
        f'<a class="item{" active" if active == 0 else ""}" href="index.html">Home</a>',
    ]
    weeks = ((1, (1, 2, 3)), (2, (4, 5, 6, 7)), (3, (8, 9, 10)))
    for week, ids in weeks:
        parts.append(f'<div class="week">Week {week}</div>')
        for n in ids:
            title = html.escape(by_id[n]["title"])
            active_cls = " active" if n == active else ""
            parts.append(
                f'<a class="item{active_cls}" data-session="{n}" href="session-{n}.html">'
                f'<i class="dot"></i>S{n} · {title}</a>'
            )
    parts.append('<div class="nav-foot" id="nav-progress">Progress stays in this browser</div>')
    return "\n".join(parts)


def page(title: str, body: str, *, session: int, page_name: str) -> str:
    lock = ""
    if session > 1:
        lock = f"""
<script>
(function () {{
  var session = {session};
  var ok = false;
  try {{
    var raw = localStorage.getItem("coa-academy-progress-v1");
    var data = raw ? JSON.parse(raw) : null;
    var prev = data && data.sessions && data.sessions[String(session - 1)];
    ok = !!(prev && prev.passed);
  }} catch (e) {{ ok = false; }}
  if (!ok) document.documentElement.classList.add("is-locked");
}})();
</script>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="css/academy.css">
{lock}
</head>
<body data-page="{page_name}" data-session="{session}">
<div class="app">
<aside class="nav">
{nav(session)}
</aside>
<main class="main">
{body}
</main>
</div>
<script src="js/site-config.js"></script>
<script src="js/quiz-data.js"></script>
<script src="js/academy.js"></script>
</body>
</html>
"""


def home_body() -> str:
    cards = []
    for s in SESSIONS:
        cards.append(
            f"""<a class="session-card" data-session="{s['id']}" href="session-{s['id']}.html">
<div class="num">{s['id']:02d}</div>
<div><h3>{html.escape(s['title'])}</h3>
<div class="meta">Week {s['week']} · {html.escape(s['minutes'])} min · {html.escape(s['artifact'])}</div></div>
<div class="pill">Open</div>
</a>"""
        )
    return f"""
<p class="kicker">Care-gap program · ten sessions · synthetic data</p>
<h1>Learn the care-ops-agent, session by session.</h1>
<p class="lede">A simulated provider network, narrated against the code that runs it. Each clip opens with what that file is responsible for, then walks the lines. Rates are computed in Python. The pages, the quizzes, and the videos are static files.</p>
<div class="progress-row">
  <div class="ring" data-progress style="--p:0"><span id="ring-label">0/10</span></div>
  <div>
    <strong id="progress-label">0 of 10 sessions passed</strong>
    <div class="bar" data-progress style="--p:0"><i></i></div>
    <p class="note" id="progress-detail">Pass a quiz at 80% or better (5 of 6) to open the next session. Retries are unlimited.</p>
    <p class="note" id="lock-note"></p>
  </div>
</div>
<div class="cards">
  <a class="link-card" id="link-github" href="{REPO}"><div class="label">Repository</div><strong>GitHub</strong><p>neelsrejan/care-ops-agent. Clips cite the files on main.</p></a>
  <a class="link-card" href="{REPO}/blob/main/docs/EVAL_REPORT.md"><div class="label">Score</div><strong>Held-out eval</strong><p>The scaling rule and the resume numbers live in the eval report.</p></a>
  <a class="link-card" href="{REPO}/blob/main/docs/tableau/DASHBOARD_SPEC.md"><div class="label">Dashboard</div><strong>Tableau spec</strong><p>Extracts and a written spec. Publishing waits on an account.</p></a>
</div>
<h2>How to run it locally</h2>
<div class="panel">
<p>The default path needs no key and no model. Deterministic templates plus the numbers Python already computed.</p>
<pre>python -m pip install -e ".[dev]"
python -m pytest
python -m care_ops_agent.run_program</pre>
<p class="note">Practice edits stay on a branch you create from main. Do not merge them.</p>
</div>
<h2>Sessions</h2>
<div class="session-grid">
{''.join(cards)}
</div>
<h2>Move progress between computers</h2>
<div class="panel">
<p>Quiz scores live in this browser. Export a code, and paste it on the other machine. The code is a checksummed copy of your scores, not an account.</p>
<div class="row">
  <button type="button" id="export-btn">Export progress</button>
  <button type="button" class="secondary" id="reset-btn">Clear this browser</button>
</div>
<textarea id="export-code" rows="3" readonly placeholder="Your code appears here"></textarea>
<label for="import-code">Paste a code from your other computer</label>
<textarea id="import-code" rows="3" placeholder="COA1...."></textarea>
<div class="row"><button type="button" id="import-btn">Import progress</button></div>
<p class="note" id="transfer-msg"></p>
</div>
"""


def session_body(session: dict, clips: list[dict]) -> str:
    n = session["id"]
    reads = "".join(f"<li>{html.escape(item)}</li>" for item in session["read"])
    clip_html = []
    for i, clip in enumerate(clips, 1):
        clip_html.append(
            f"""<article class="clip">
<h3>{i}. {html.escape(clip['title'])}</h3>
<div class="overview"><h4>Architecture</h4><p>{html.escape(clip['overview'])}</p></div>
<video controls preload="metadata" src="{html.escape(clip['src'])}">
<a href="{html.escape(clip['src'])}">Download clip {i}</a>
</video>
<p class="meta">{clock(clip['seconds'])} · Andrew · <a href="{html.escape(clip['blob'])}">{html.escape(clip['path'])}</a> on <code>main</code></p>
</article>"""
        )
    files = []
    seen = set()
    for clip in clips:
        if clip["path"] in seen:
            continue
        seen.add(clip["path"])
        files.append(f'<li><a href="{html.escape(clip["blob"])}"><code>{html.escape(clip["path"])}</code></a></li>')
    trace_path = ROOT / "docs" / "sessions" / f"session-{n}" / "LOGIC_TRACE.md"
    trace = md(trace_path.read_text())
    practice = md(session["practice"])
    tree = f"{REPO}/tree/main"
    trace_blob = f"{REPO}/blob/main/docs/sessions/session-{n}/LOGIC_TRACE.md"
    return f"""
<p class="kicker">Week {session['week']} · Session {n}</p>
<h1>{html.escape(session['title'])}</h1>
<p class="lede">{html.escape(session['blurb'])}</p>
<p class="note">Ticket {html.escape(session['ticket'])} · about {html.escape(session['minutes'])} minutes · artifact: {html.escape(session['artifact'])}</p>
<div class="lock-screen">
  <div class="panel">
    <h2>This session is locked</h2>
    <p>Pass Session {n - 1} at 80% or better (5 of 6) to open the videos, the logic trace, the practice task, and this quiz. Retries on the earlier quiz are unlimited. If you already passed it on another computer, import that progress code from the home page.</p>
    <p><a class="button" href="session-{n - 1}.html">Go to Session {n - 1}</a> <a class="button secondary" href="index.html">Home</a></p>
  </div>
</div>
<div class="lesson">
<h2>Read first</h2>
<ul>{reads}</ul>
<h2>Watch in this order</h2>
<p class="note">Read the architecture note, then play the clip. The note says what the file is for. The video walks the lines. Line numbers match <code>main</code> as this site was built.</p>
{''.join(clip_html)}
<h2>Logic trace</h2>
<p class="note"><a href="{html.escape(trace_blob)}">LOGIC_TRACE.md</a></p>
<div class="prose">{trace}</div>
<h2>Code on main</h2>
<p><a href="{tree}">Browse the repository</a></p>
<ul>{''.join(files)}</ul>
<h2>Practice, on a private branch</h2>
<div class="prose">{practice}</div>
<h2>Quiz</h2>
<p class="note">Six questions on architecture and design. 5 of 6 to pass. Explanations show after you submit. The salted hash is a self-study speed bump, not protection.</p>
<div id="quiz"></div>
</div>
"""


def write_answer_key(payload: dict) -> None:
    lines = [
        "# Academy quiz letters",
        "",
        "These are the letters after `build_site.py` shuffles each question.",
        "The salted hash on the page is a self-study speed bump, not protection.",
        "Reading this file, or trying all four choices, bypasses it.",
        "The prose quizzes in `docs/sessions/` are a separate set and are not these letters.",
        "",
    ]
    for session in range(1, N_SESSIONS + 1):
        lines.append(f"## Session {session}")
        lines.append("")
        for index, question in enumerate(payload[str(session)]["questions"], 1):
            winner = next(
                choice
                for choice in question["choices"]
                if answer_hash(question["salt"], choice["id"]) == question["answerHash"]
            )
            lines.append(f"{index}. **{winner['id'].upper()}.** {winner['text']}")
            lines.append("")
    (ACADEMY / "content" / "QUIZ_ANSWERS.md").write_text("\n".join(lines))


def main() -> None:
    payload = quiz_payload()
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    for forbidden in ('"correct"', '"answer":', "Qwen", "qwen"):
        if forbidden in blob:
            raise SystemExit(f"quiz payload contains {forbidden}")
    items = graded_items(payload)
    assert_uniform_options(items)
    expected = assert_guessers(items)
    letters: Counter = Counter(item["correct"] for item in items)
    n = len(items)
    for letter, count in sorted(letters.items()):
        if count / n > 0.40:
            raise SystemExit(f"letter {letter} is {count}/{n} answers, over 40%")
        print(f"letter {letter}: {count}/{n}")
    for name, by_session in expected.items():
        bits = " ".join(f"s{session}={by_session[session]:.1%}" for session in range(1, N_SESSIONS + 1))
        print(f"guesser {name}: {bits}")
    write_answer_key(payload)
    (SITE / "js").mkdir(parents=True, exist_ok=True)
    (SITE / "js" / "quiz-data.js").write_text("window.QUIZZES = " + blob + ";\n")
    (SITE / "index.html").write_text(page("care-ops-agent Academy", home_body(), session=0, page_name="home"))
    (SITE / ".nojekyll").write_text("")
    for session in SESSIONS:
        clips = load_clips(session["id"])
        body = session_body(session, clips)
        (SITE / f"session-{session['id']}.html").write_text(
            page(f"Session {session['id']} · {session['title']}", body, session=session["id"], page_name="session")
        )
        print(f"session {session['id']}: {len(clips)} clips")
    print("wrote", SITE)


if __name__ == "__main__":
    main()
