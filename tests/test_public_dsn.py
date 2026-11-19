import pytest

from care_ops_agent.public.dsn import (
    HostedDatabaseRequired,
    assert_synthetic_stays_local,
    public_text,
    redact,
    require_hosted_dsn,
)


def test_hosted_dsn_is_required(monkeypatch):
    monkeypatch.delenv("CARE_OPS_PG_DSN", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(HostedDatabaseRequired, match="CARE_OPS_PG_DSN"):
        require_hosted_dsn()


def test_localhost_is_not_the_demo(monkeypatch):
    monkeypatch.setenv("CARE_OPS_PG_DSN", "postgresql://postgres@localhost:5433/care_ops")
    monkeypatch.delenv("CARE_OPS_ALLOW_LOCAL", raising=False)
    with pytest.raises(HostedDatabaseRequired, match="local"):
        require_hosted_dsn()


def test_localhost_allowed_for_ci(monkeypatch):
    monkeypatch.setenv("CARE_OPS_PG_DSN", "postgresql://postgres@localhost:5433/care_ops")
    monkeypatch.setenv("CARE_OPS_ALLOW_LOCAL", "1")
    assert require_hosted_dsn().endswith("/care_ops")


def test_remote_synthea_load_is_refused(monkeypatch):
    monkeypatch.delenv("CARE_OPS_ALLOW_SYNTHETIC_UPLOAD", raising=False)
    url = "postgresql://owner:secret-token@ep-example.neon.tech/neondb?sslmode=require"
    with pytest.raises(RuntimeError, match="non-local") as caught:
        assert_synthetic_stays_local(url)
    assert "secret-token" not in str(caught.value)


def test_redact_strips_the_password():
    text = "failed postgresql://owner:secret-token@ep-example.neon.tech/neondb"
    assert "secret-token" not in redact(text)
    assert "owner" in redact(text)


def test_public_text_hides_server_paths_and_keeps_urls():
    text = (
        "Traceback /home/ubuntu/app/streamlit_app.py and /opt/cursor/artifacts/x. "
        "See https://data.hrsa.gov/topics/health-centers/uds. "
        "postgresql://owner:secret-token@ep-example.neon.tech/neondb"
    )
    shown = public_text(text)
    assert "/home/ubuntu" not in shown
    assert "/opt/cursor" not in shown
    assert "secret-token" not in shown
    assert "https://data.hrsa.gov/topics/health-centers/uds" in shown
