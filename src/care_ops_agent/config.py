"""Runtime settings (adapted from invalid-agent config.py).

No tracker/CRM credentials yet: the PM tool is pending a tool-choice pass (2026-11-03),
so the backlog stays a portable CSV/Markdown file.
Program constants are SIMULATION targets, labeled as such.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# SIMULATION targets (synthetic program, not a real contract or official measure benchmark).
PROGRAM_PARTNERS = 8
GO_LIVE_WEEKS = 4
# Simplified measure targets used by the sim (documented in docs/MEASURES.md).
MEASURE_TARGETS = {
    "hba1c_control": 0.60,       # share of diabetic patients with latest HbA1c < 8.0%
    "bp_control": 0.65,          # share of hypertensive patients with latest BP < 140/90
    "breast_cancer_screening": 0.70,  # share of eligible women with a mammogram in 27 months
}


_LLM_BACKENDS = {"deterministic", "ollama"}
DEFAULT_LLM_MODEL = "qwen2.5:7b"


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [Path.cwd(), *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "care_ops_agent").is_dir():
            return candidate
    return here.parents[2]


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    llm_backend: str
    llm_model: str
    ollama_host: str
    repo_root: Path
    out_dir: Path

    @property
    def rules_only(self) -> bool:
        return self.llm_backend == "deterministic"

    def redacted(self) -> dict[str, object]:
        return {
            "llm_backend": self.llm_backend,
            "llm_model": self.llm_model,
            "ollama_host": self.ollama_host,
            "repo_root": str(self.repo_root),
            "out_dir": str(self.out_dir),
        }

    def __repr__(self) -> str:
        return f"Settings(llm_backend={self.llm_backend!r})"


def load_settings() -> Settings:
    backend = _env("LLM_BACKEND", "deterministic").lower()
    if backend in {"rules", "rules-only", "mock", "offline"}:
        backend = "deterministic"
    if backend not in _LLM_BACKENDS:
        backend = "deterministic"
    root = find_repo_root()
    return Settings(
        llm_backend=backend,
        llm_model=_env("LLM_MODEL", DEFAULT_LLM_MODEL),
        ollama_host=_env("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/"),
        repo_root=root,
        out_dir=Path(_env("CARE_OPS_OUT", str(root / "out"))),
    )
