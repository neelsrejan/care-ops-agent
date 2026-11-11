"""Catch quiz layouts a student can pass without knowing the material.

These checks run on the built questions (after the letter shuffle). They are a
self-study guard on the item writing, not a security control.
"""
from __future__ import annotations

import re
from collections import Counter

_SENTENCE_SPLIT = re.compile(r"(?<!\d)[.!?](?:\s+|$)")
_WORD = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "and", "for", "that", "this", "with", "from", "into", "onto", "over",
    "under", "than", "then", "them", "they", "their", "there", "these", "those",
    "what", "when", "where", "which", "while", "whose", "why", "how", "who",
    "are", "was", "were", "been", "being", "have", "has", "had", "does", "did",
    "not", "but", "you", "your", "its", "it's", "can", "cannot", "any", "all",
    "only", "also", "because", "before", "after", "about", "above", "across",
    "between", "each", "every", "other", "such", "same", "both", "one", "two",
    "per", "via", "out", "off", "our", "his", "her", "she", "him", "may", "must",
    "should", "would", "could", "will", "just", "still", "even", "else", "once",
    "here", "back", "down", "up", "own", "too", "very", "more", "most", "some",
    "none", "nor", "yet", "let", "get", "got", "use", "used", "using", "set",
}


def sentence_count(text: str) -> int:
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(text.strip()) if part.strip()]
    return len(parts)


def _words(text: str) -> list[str]:
    return [word for word in _WORD.findall(text.lower()) if len(word) >= 4 and word not in _STOP]


def _clauses(text: str) -> set[str]:
    found: set[str] = set()
    for chunk in re.split(r"[.;]", text):
        for piece in [chunk, *chunk.split(",")]:
            norm = " ".join(piece.lower().split()).strip(" -")
            if len(norm.split()) >= 4:
                found.add(norm)
    return found


def _feature_clauses(text: str) -> int:
    """Commas plus semicolon breaks. A bare sentence scores 0."""
    return text.count(",") + text.count(";")


def _visible(text: str) -> str:
    """Length the browser shows. Runs of spaces collapse to one."""
    return " ".join(text.split())


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def assert_uniform_options(items: list[dict]) -> None:
    """Every option is one sentence, and lengths stay near the question median."""
    for item in items:
        raw = [choice["text"] for choice in item["choices"]]
        for text in raw:
            if "  " in text:
                raise SystemExit(
                    f"session {item['session']} option contains a double space: {text[:80]}"
                )
        texts = [_visible(text) for text in raw]
        for text in texts:
            if sentence_count(text) != 1:
                raise SystemExit(
                    f"session {item['session']} option is not one sentence: {text[:80]}"
                )
        lengths = [len(text) for text in texts]
        median = _median(lengths)
        for text, length in zip(texts, lengths):
            if length < 0.75 * median or length > 1.25 * median:
                raise SystemExit(
                    f"session {item['session']} length {length} is outside ±25% of median {median:.0f}: {text[:80]}"
                )


def _questions(items: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for item in items:
        grouped.setdefault(int(item["session"]), []).append(item)
    return grouped


def _pick_expected(item: dict, score_of) -> float:
    """Expected accuracy when the guesser picks uniformly among the top score."""
    scores = [(score_of(choice), choice["id"] == item["correct"]) for choice in item["choices"]]
    best = max(score for score, _correct in scores)
    tied = [correct for score, correct in scores if score == best]
    if not tied or True not in tied:
        return 0.0
    return 1.0 / len(tied)


def _binomial_pass_rate(probs: list[float], need: int = 7) -> float:
    """P(X >= need) for independent Bernoulli questions."""
    total = 0.0
    n = len(probs)
    for mask in range(1 << n):
        prob = 1.0
        correct = 0
        for index, chance in enumerate(probs):
            if (mask >> index) & 1:
                prob *= chance
                correct += 1
            else:
                prob *= 1.0 - chance
        if correct >= need:
            total += prob
    return total


def _strike_probs(items: list[dict]) -> dict[int, list[float]]:
    """Strike options that carry a word or clause seen only on distractors."""
    word_correct: Counter = Counter()
    word_wrong: Counter = Counter()
    clause_correct: Counter = Counter()
    clause_wrong: Counter = Counter()
    for item in items:
        for choice in item["choices"]:
            is_correct = choice["id"] == item["correct"]
            bag = word_correct if is_correct else word_wrong
            for word in set(_words(choice["text"])):
                bag[word] += 1
            cbag = clause_correct if is_correct else clause_wrong
            for clause in _clauses(choice["text"]):
                cbag[clause] += 1
    # A content word is a steer once it shows up on six or more distractors and on
    # no correct answer. Two or three ordinary overlaps do not decide a session;
    # a word that keeps marking the wrong options does. Clauses are stricter:
    # one repeated clause is enough.
    tells = {
        word
        for word, count in word_wrong.items()
        if count >= 6 and word_correct[word] == 0
    }
    tells |= {
        clause
        for clause, count in clause_wrong.items()
        if count >= 2 and clause_correct[clause] == 0
    }
    by_session: dict[int, list[float]] = {}
    for item in items:
        remaining = []
        for choice in item["choices"]:
            words = set(_words(choice["text"]))
            clauses = _clauses(choice["text"])
            if words & {tell for tell in tells if " " not in tell} or clauses & {tell for tell in tells if " " in tell}:
                continue
            remaining.append(choice["id"] == item["correct"])
        if remaining and any(remaining):
            chance = 1.0 / len(remaining)
        else:
            chance = 0.0
        by_session.setdefault(int(item["session"]), []).append(chance)
    return by_session


def guesser_probs(items: list[dict]) -> dict[str, dict[int, list[float]]]:
    """Per guesser, per session, probability of landing the correct option."""
    grouped = _questions(items)
    names = [
        "longest",
        "shortest",
        "most_sentences",
        "most_commas",
        "stem_overlap",
        "letter_a",
        "letter_b",
        "letter_c",
        "letter_d",
    ]
    out: dict[str, dict[int, list[float]]] = {name: {} for name in names}
    for session, questions in grouped.items():
        out["longest"][session] = [
            _pick_expected(item, lambda choice: len(_visible(choice["text"]))) for item in questions
        ]
        out["shortest"][session] = [
            _pick_expected(item, lambda choice: -len(_visible(choice["text"]))) for item in questions
        ]
        out["most_sentences"][session] = [
            _pick_expected(item, lambda choice: sentence_count(choice["text"])) for item in questions
        ]
        out["most_commas"][session] = [
            _pick_expected(item, lambda choice: _feature_clauses(choice["text"])) for item in questions
        ]
        out["stem_overlap"][session] = [
            _pick_expected(
                item,
                lambda choice, stem=item["prompt"]: len(set(_words(choice["text"])) & set(_words(stem))),
            )
            for item in questions
        ]
        for letter in "abcd":
            out[f"letter_{letter}"][session] = [
                1.0 if item["correct"] == letter else 0.0 for item in questions
            ]
    strike = _strike_probs(items)
    out["strike_distractor_only"] = strike
    return out


def assert_guessers(items: list[dict]) -> dict[str, dict[int, float]]:
    """Fail if any guesser expects 50%+ on a session, or passes 7 of 8 over 5%."""
    probs = guesser_probs(items)
    expected: dict[str, dict[int, float]] = {}
    failures: list[str] = []
    for name, by_session in probs.items():
        expected[name] = {}
        for session, chances in sorted(by_session.items()):
            mean = sum(chances) / len(chances)
            expected[name][session] = mean
            need = (len(chances) * 8 + 9) // 10  # ceil(0.8 * n) without floats
            pass_rate = _binomial_pass_rate(chances, need=need)
            if mean >= 0.50:
                failures.append(f"{name} session {session} expects {mean:.0%}")
            if pass_rate > 0.05:
                failures.append(f"{name} session {session} passes {need} of {len(chances)} with probability {pass_rate:.1%}")
    if failures:
        raise SystemExit("quiz guesser check failed: " + "; ".join(failures))
    return expected
