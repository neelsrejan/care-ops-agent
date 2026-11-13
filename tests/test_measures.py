from care_ops_agent.metrics.measures import met_rate


def test_met_rate_counts_missing_as_gap():
    rows = [{"met": True}] * 6 + [{"met": False}] * 3 + [{"met": None}]
    r = met_rate(rows)
    assert r["denominator"] == 10 and r["numerator"] == 6 and abs(r["met_rate"] - 0.6) < 1e-12
    assert r["no_result"] == 1 and r["ci_low"] < 0.6 < r["ci_high"]


def test_empty():
    assert met_rate([])["met_rate"] is None
