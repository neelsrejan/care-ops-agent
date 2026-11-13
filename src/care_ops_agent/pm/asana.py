"""Asana client boundary.

``ASANA_BACKEND=offline`` (the default) writes a CSV in Asana's importer shape
and a JSON file of SIM- tasks. It does not open a socket.

``ASANA_BACKEND=live`` builds a client that talks to ``https://app.asana.com/api/1.0``.
That path needs ``ASANA_ACCESS_TOKEN`` and ``ASANA_WORKSPACE_GID``. Nothing in
the default demo or the tests selects it.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

ASANA_API = "https://app.asana.com/api/1.0"
CSV_FIELDS = ["Name", "Description", "Section/Column", "Tags", "Assignee", "Due Date"]


class AsanaNotConfigured(RuntimeError):
    """Live Asana was requested and the environment does not have the credentials."""


class OfflineAsanaClient:
    """Write tasks locally. Gids are SIM- so they cannot be confused with a real board."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.tasks: list[dict[str, Any]] = []

    def create_tasks(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        saved = []
        for i, task in enumerate(tasks, 1):
            saved.append({
                "gid": f"SIM-{i:04d}",
                "name": task["name"],
                "notes": task.get("notes", ""),
                "section": task.get("section", "Program"),
                "assignee": task.get("assignee", ""),
                "due_on": task.get("due_on", ""),
                "tags": task.get("tags", "synthetic"),
                "label": "SYNTHETIC",
            })
        self.tasks = saved
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / "tasks.json").write_text(json.dumps(saved, indent=2) + "\n")
        self.write_import_csv(self.folder / "asana_import.csv")
        return saved

    def write_import_csv(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for task in self.tasks:
                writer.writerow({
                    "Name": task["name"],
                    "Description": task["notes"],
                    "Section/Column": task["section"],
                    "Tags": task["tags"],
                    "Assignee": task["assignee"],
                    "Due Date": task["due_on"],
                })
        return path


class LiveAsanaClient:
    """Thin REST wrapper. Constructed only when a token is present. Not used by default."""

    def __init__(self, token: str, workspace_gid: str, base: str = ASANA_API):
        if not token or not workspace_gid:
            raise AsanaNotConfigured("ASANA_ACCESS_TOKEN and ASANA_WORKSPACE_GID are both required")
        self._token = token
        self.workspace_gid = workspace_gid
        self.base = base.rstrip("/")

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        import httpx

        payload: dict[str, Any] = {
            "name": task["name"],
            "workspace": self.workspace_gid,
            "notes": task.get("notes", ""),
        }
        if task.get("due_on"):
            payload["due_on"] = task["due_on"]
        response = httpx.post(
            f"{self.base}/tasks",
            headers={"Authorization": f"Bearer {self._token}"},
            json={"data": payload},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["data"]


def asana_client_from_env(folder: Path) -> OfflineAsanaClient | LiveAsanaClient:
    backend = os.environ.get("ASANA_BACKEND", "offline").strip().lower()
    if backend in {"", "offline", "fake", "local"}:
        return OfflineAsanaClient(folder)
    if backend == "live":
        token = os.environ.get("ASANA_ACCESS_TOKEN", "").strip()
        workspace = os.environ.get("ASANA_WORKSPACE_GID", "").strip()
        if not token or not workspace:
            raise AsanaNotConfigured(
                "ASANA_BACKEND=live needs ASANA_ACCESS_TOKEN and ASANA_WORKSPACE_GID in the environment"
            )
        return LiveAsanaClient(token, workspace)
    raise AsanaNotConfigured(f"ASANA_BACKEND must be offline or live, got {backend!r}")
