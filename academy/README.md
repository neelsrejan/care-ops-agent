# care-ops-agent Academy

Static course for sessions 1–10. Quizzes, progress, and videos have no backend and no paid service.

Each clip starts with a short architecture note: what that file is responsible for, and why it sits where it does. The video under that note is a line-by-line walkthrough, same method as the invalid-agent Academy: syntax-highlighted code, the current lines highlighted, captions, and speech from edge-tts only (`en-US-AndrewNeural`). There is no fallback voice.

S1–S4 were imported as one commit, so clips cite the file on `main` rather than a historical `session-N` tag. Later sessions did not rewrite those files except where a later session had to extend them (`sim/network.py` grew a multi-injection path; FHIR upload was blocked).

Quizzes are architecture and design questions. They do not ask for syntax or for a line number. Pass at 80% (5 of 6) to unlock the next session. Progress stays in `localStorage` under `coa-academy-progress-v1`. Export copies a checksummed code (`COA1.…`).

## Rebuild

```bash
pip install -r academy/requirements.txt
python3 academy/scripts/emit_narration.py
python3 academy/scripts/render_all.py
python3 academy/scripts/build_site.py
```

`academy/content/durations.json` lets the HTML rebuild without the MP4s present. CI runs `build_site.py` and fails if `academy/site/` or `academy/content/QUIZ_ANSWERS.md` drift.

## Pages

Workflow `.github/workflows/pages.yml` deploys `academy/site` (including `videos/`) with GitHub Actions. In the repo settings, set Pages to GitHub Actions if it is not already. The URL is `https://neelsrejan.github.io/care-ops-agent/`.

`academy/content/bank.py` is the authoring copy. The build shuffles the four choices and writes a salted SHA-256 of the published letter. That hash is a self-study speed bump, not protection.
