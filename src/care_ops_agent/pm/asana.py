"""Asana client boundary.

``ASANA_BACKEND=offline`` (the default) writes a CSV in Asana's importer shape
and a JSON file of SIM- tasks. It does not open a socket.

``ASANA_BACKEND=live`` builds a client that talks to ``https://app.asana.com/api/1.0``.
That path needs ``ASANA_ACCESS_TOKEN`` and ``ASANA_WORKSPACE_GID``. The public
page only reads. ``python -m care_ops_agent.pm.asana seed`` is the owner command
that creates the project and tasks.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

ASANA_API = "https://app.asana.com/api/1.0"
CSV_FIELDS = ["Name", "Description", "Section/Column", "Tags", "Assignee", "Due Date"]
PROJECT_NAME = "Care-gap work plan"


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

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def _paginate(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        import httpx

        items: list[dict[str, Any]] = []
        query = dict(params)
        while True:
            response = httpx.get(
                f"{self.base}{path}", headers=self._headers(), params=query, timeout=30.0,
            )
            response.raise_for_status()
            body = response.json()
            items.extend(body.get("data") or [])
            offset = (body.get("next_page") or {}).get("offset")
            if not offset:
                return items
            query["offset"] = offset

    def find_project(self, name: str) -> dict[str, Any] | None:
        """Return the workspace project whose name matches exactly, or None."""
        projects = self._paginate(
            f"/workspaces/{self.workspace_gid}/projects",
            {"opt_fields": "name,permalink_url", "limit": 100, "archived": "false"},
        )
        for project in projects:
            if project.get("name") == name:
                return project
        return None

    def create_project(self, name: str) -> dict[str, Any]:
        import httpx

        response = httpx.post(
            f"{self.base}/projects",
            headers=self._headers(),
            json={"data": {"name": name, "workspace": self.workspace_gid}},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["data"]

    def list_tasks(self, project_gid: str) -> list[dict[str, Any]]:
        return self._paginate(
            f"/projects/{project_gid}/tasks",
            {"opt_fields": "name,completed,permalink_url", "limit": 100},
        )

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        import httpx

        payload: dict[str, Any] = {
            "name": task["name"],
            "workspace": self.workspace_gid,
            "notes": task.get("notes", ""),
        }
        if task.get("due_on"):
            payload["due_on"] = task["due_on"]
        if task.get("project_gid"):
            payload["projects"] = [task["project_gid"]]
        response = httpx.post(
            f"{self.base}/tasks",
            headers=self._headers(),
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


def project_url(project: dict[str, Any]) -> str:
    permalink = str(project.get("permalink_url") or "").strip()
    if permalink:
        return permalink
    return f"https://app.asana.com/0/{project['gid']}/list"


def seed_plan(client: Any, tasks: list[dict[str, Any]], name: str = PROJECT_NAME) -> dict[str, Any]:
    """Find or create the project, then create only tasks whose names are absent.

    A second call with the same names creates nothing. Callers pass the client
    so tests can use a fake. This function does not read the environment.
    """
    project = client.find_project(name)
    created_project = project is None
    if project is None:
        project = client.create_project(name)
    present = {str(row.get("name")) for row in client.list_tasks(project["gid"])}
    created = 0
    for task in tasks:
        if task["name"] in present:
            continue
        client.create_task({**task, "project_gid": project["gid"]})
        present.add(task["name"])
        created += 1
    return {
        "project_name": name,
        "project_gid": project["gid"],
        "project_url": project_url(project),
        "created_project": created_project,
        "created": created,
        "already_present": len(tasks) - created,
    }


def read_plan(client: Any, name: str = PROJECT_NAME) -> dict[str, Any]:
    """Read the seeded project. Does not create a project or a task."""
    project = client.find_project(name)
    if project is None:
        return {
            "ok": True,
            "summary": (
                f"Asana is connected. Project {name} is not in the workspace yet. "
                "The owner creates it with python -m care_ops_agent.pm.asana seed."
            ),
            "url": "",
            "link_label": "",
            "tasks": [],
            "open_count": 0,
            "complete_count": 0,
        }
    tasks = client.list_tasks(project["gid"])
    complete = sum(1 for task in tasks if task.get("completed"))
    open_count = len(tasks) - complete
    return {
        "ok": True,
        "summary": (
            f"Asana project {name}. Tasks: {len(tasks)}. "
            f"Open: {open_count}. Complete: {complete}."
        ),
        "url": project_url(project),
        "link_label": "Open the Asana project",
        "tasks": [
            {"name": task.get("name") or "", "completed": bool(task.get("completed"))}
            for task in tasks
        ],
        "open_count": open_count,
        "complete_count": complete,
    }


def seed_summary(result: dict[str, Any]) -> str:
    action = "created" if result["created_project"] else "found"
    return (
        f"Project {action}: {result['project_name']}\n"
        f"URL: {result['project_url']}\n"
        f"Tasks created: {result['created']}\n"
        f"Tasks already present: {result['already_present']}"
    )


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args != ["seed"]:
        raise SystemExit("Usage: python -m care_ops_agent.pm.asana seed")
    client = asana_client_from_env(Path("."))
    if not isinstance(client, LiveAsanaClient):
        raise AsanaNotConfigured(
            "python -m care_ops_agent.pm.asana seed requires ASANA_BACKEND=live, "
            "ASANA_ACCESS_TOKEN, and ASANA_WORKSPACE_GID. The public page does not create tasks."
        )
    from care_ops_agent.controls.plan import build_plan

    result = seed_plan(client, build_plan()["asana_tasks"])
    print(seed_summary(result))


if __name__ == "__main__":
    main()
