import pytest

psycopg = pytest.importorskip("psycopg")


def _con():
    from care_ops_agent import db
    try:
        return db.connect()
    except Exception:
        pytest.skip("no local PostgreSQL")


def test_sql_tests_pass_and_views_exist():
    from care_ops_agent import db
    con = _con()
    try:
        con.execute("SELECT 1 FROM mart.v_bp_control LIMIT 1")
    except Exception:
        pytest.skip("views not built; run python -m care_ops_agent.data.load")
    assert all(v == 0 for v in db.run_sql_tests(con).values())
