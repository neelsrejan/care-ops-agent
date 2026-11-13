"""Match a question to one approved entry, or flag it.

Scoring is token overlap against the entry title and body. There is no
embedding model and no network call. A weak or tied match is flagged so the
draft is not invented. A cited draft must contain the entry id.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from care_ops_agent.rfp.bank import ENTRIES, questions

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "and", "for", "that", "this", "with", "from", "into", "your", "you",
    "are", "was", "were", "does", "did", "not", "but", "can", "any", "all",
    "what", "when", "where", "which", "how", "who", "will", "its", "our",
    "per", "via", "out", "one", "two", "may", "must", "should", "would",
    "have", "has", "had", "been", "being", "than", "then", "them", "they",
    "their", "only", "also", "before", "after", "about", "each", "such",
    "does", "did", "don", "isn",
}
THRESHOLD = 0.34
MARGIN = 0.08
TRACK_START = date(2026, 11, 16)


def load_bank() -> dict[str, Any]:
    return {"entries": [dict(entry) for entry in ENTRIES], "questions": questions()}


def _tokens(text: str) -> set[str]:
    return {word for word in _WORD.findall(text.lower()) if len(word) >= 4 and word not in _STOP}


def score_entry(question: str, entry: dict[str, str]) -> float:
    q = _tokens(question)
    if not q:
        return 0.0
    body = _tokens(entry["title"] + " " + entry["body"])
    return len(q & body) / len(q)


def retrieve(question: str, entries: list[dict[str, str]] | None = None) -> dict[str, Any]:
    entries = entries if entries is not None else [dict(entry) for entry in ENTRIES]
    ranked = sorted(((score_entry(question, entry), entry) for entry in entries), key=lambda pair: -pair[0])
    best, winner = ranked[0]
    second = ranked[1][0] if len(ranked) > 1 else 0.0
    if best < THRESHOLD or best - second < MARGIN:
        return {"status": "flagged", "entry": None, "score": best, "runner_up": second}
    return {"status": "cited", "entry": winner, "score": best, "runner_up": second}


def draft_answer(question: str, hit: dict[str, Any]) -> dict[str, Any]:
    if hit["status"] != "cited" or hit["entry"] is None:
        return {
            "status": "flagged",
            "text": "No library entry cleared the overlap bar. Flagged for a person. Do not invent an answer. SYNTHETIC.",
            "cites": [],
            "score": hit["score"],
        }
    entry = hit["entry"]
    text = f"Cite {entry['id']}. {entry['body']} SYNTHETIC SIMULATION."
    if entry["id"] not in text:
        raise RuntimeError("cited draft is missing its entry id")
    return {"status": "cited", "text": text, "cites": [entry["id"]], "score": hit["score"]}


def answer_question(question: str) -> dict[str, Any]:
    return draft_answer(question, retrieve(question))


def tracker(as_of: date = TRACK_START) -> list[dict[str, Any]]:
    rows = []
    for index, question in enumerate(questions()):
        due = as_of + timedelta(days=7 + (index % 5) * 3)
        rows.append({
            "id": question["id"],
            "section": question["section"],
            "owner": question["owner"],
            "due_date": due.isoformat(),
            "question": question["question"],
            "status": "open",
            "label": "SYNTHETIC",
        })
    return rows


def answer_all() -> list[dict[str, Any]]:
    rows = []
    for question in questions():
        hit = retrieve(question["question"])
        draft = draft_answer(question["question"], hit)
        rows.append({
            "id": question["id"],
            "expect": question["expect"],
            "status": draft["status"],
            "cites": ",".join(draft["cites"]),
            "score": round(draft["score"], 3),
            "correct": (draft["cites"][0] == question["expect"]) if question["expect"] else draft["status"] == "flagged",
            "label": "SYNTHETIC",
        })
    return rows
