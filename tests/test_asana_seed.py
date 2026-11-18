import os

from care_ops_agent.controls.plan import build_plan
from care_ops_agent.pm.asana import PROJECT_NAME, read_plan, seed_plan
from care_ops_agent.public.secrets import apply_secret_values
from care_ops_agent.public.status import checklist


class FakeAsana:
    """In-memory Asana. Writes are recorded so a read can be shown to avoid them."""

    def __init__(self):
        self.projects: dict[str, dict] = {}
        self.tasks: dict[str, list[dict]] = {}
        self.writes: list[str] = []

    def find_project(self, name: str):
        for project in self.projects.values():
            if project["name"] == name:
                return project
        return None

    def create_project(self, name: str):
        self.writes.append("create_project")
        gid = f"p{len(self.projects) + 1}"
        project = {
            "gid": gid,
            "name": name,
            "permalink_url": f"https://app.asana.com/0/{gid}/list",
        }
        self.projects[gid] = project
        self.tasks[gid] = []
        return project

    def list_tasks(self, project_gid: str):
        return list(self.tasks[project_gid])

    def create_task(self, task: dict):
        self.writes.append("create_task")
        saved = {
            "gid": f"t{1 + sum(len(rows) for rows in self.tasks.values())}",
            "name": task["name"],
            "completed": False,
        }
        self.tasks[task["project_gid"]].append(saved)
        return saved


def test_seed_creates_once_and_then_creates_nothing():
    client = FakeAsana()
    tasks = build_plan()["asana_tasks"]
    first = seed_plan(client, tasks)
    assert first["created"] == len(tasks)
    assert first["created"] > 0
    assert first["already_present"] == 0
    assert first["project_name"] == PROJECT_NAME
    assert first["project_url"].startswith("https://app.asana.com/0/")
    created_writes = client.writes.count("create_task")
    second = seed_plan(client, tasks)
    assert second["created"] == 0
    assert second["already_present"] == len(tasks)
    assert second["created_project"] is False
    assert client.writes.count("create_task") == created_writes


def test_public_read_never_calls_a_write_method():
    client = FakeAsana()
    tasks = build_plan()["asana_tasks"]
    seed_plan(client, tasks)
    client.tasks[next(iter(client.projects))][0]["completed"] = True
    client.writes.clear()
    status = read_plan(client)
    assert client.writes == []
    assert status["complete_count"] == 1
    assert status["open_count"] == len(tasks) - 1
    assert status["url"].startswith("https://app.asana.com/0/")
    assert len(status["tasks"]) == len(tasks)


def test_secrets_fill_asana_and_database_without_replacing_env(monkeypatch):
    monkeypatch.delenv("CARE_OPS_PG_DSN", raising=False)
    monkeypatch.delenv("ASANA_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("ASANA_WORKSPACE_GID", "already-set")
    apply_secret_values({
        "CARE_OPS_PG_DSN": "postgresql://db.example/care_ops",
        "ASANA_BACKEND": "live",
        "ASANA_ACCESS_TOKEN": "from-secrets",
        "ASANA_WORKSPACE_GID": "from-secrets",
    })
    assert os.environ["CARE_OPS_PG_DSN"] == "postgresql://db.example/care_ops"
    assert os.environ["ASANA_ACCESS_TOKEN"] == "from-secrets"
    assert os.environ["ASANA_BACKEND"] == "live"
    assert os.environ["ASANA_WORKSPACE_GID"] == "already-set"


def test_connected_asana_status_line_is_not_pending(monkeypatch):
    monkeypatch.setenv("ASANA_BACKEND", "live")
    monkeypatch.setenv("ASANA_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("ASANA_WORKSPACE_GID", "1")
    row = next(item for item in checklist() if item["name"] == "Asana")
    assert row["ready"] == "yes"
    assert "pending owner credentials" not in row["detail"].lower()
    assert "seed" in row["detail"]
