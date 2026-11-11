from pathlib import Path

from care_ops_agent.eval.catalog import DEV_IDS, heldout_scenarios
from care_ops_agent.eval.harness import decision, eval_report_markdown, resume_bullets, run_eval

ROOT = Path(__file__).resolve().parents[1]


def test_heldout_catalog_shape():
    rows = heldout_scenarios()
    assert len(rows) == 20
    assert not ({row["id"] for row in rows} & DEV_IDS)
    families = {}
    for row in rows:
        families[row["family"]] = families.get(row["family"], 0) + 1
    assert families == {
        "clinic_gap": 3,
        "partner_gap": 3,
        "missing_feed": 3,
        "other_measure_feed": 2,
        "stall": 2,
        "mixed": 2,
        "no_signal": 3,
        "near_threshold": 2,
    }


def test_heldout_eval_keeps_the_strict_gate():
    report = run_eval()
    call = decision(report)
    failed = [gate["gate"] for gate in call["gates"] if not gate["passed"]]
    # Seed 701 has one chance flag in a cell that was not the injected shift.
    # The scaling rule requires zero of those, so the workbook stays NO-GO.
    assert failed == ["false_alarms"]
    assert call["decision"] == "NO-GO"
    assert report["false_alarms"] == 1
    assert report["top1_correct"] == report["top1_total"] == 11
    assert report["partner_leaks"] == 0
    assert report["fidelity_ok"] == report["fidelity_checked"] == 20
    bullets = resume_bullets(report)
    assert "synthetic" in bullets.lower()
    assert "advanced" not in bullets.lower()
    assert "expert" not in bullets.lower()
    assert f"{report['top1_correct']} of {report['top1_total']}" in bullets
    assert "production system" in bullets
    assert (ROOT / "RESUME_BULLETS.md").read_text() == bullets
    assert (ROOT / "docs" / "EVAL_REPORT.md").read_text() == eval_report_markdown(report)
