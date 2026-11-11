import pandas as pd

from care_ops_agent.export.preview import write_preview
from care_ops_agent.export.tableau import care_gap_weekly, write_extracts


def test_tableau_extract_is_flat_scalars(tmp_path):
    frame = pd.DataFrame([
        {"week": 1, "partner_id": "P1", "clinic": "C1", "measure": "bp_control",
         "result_recorded": True, "met": True, "patient_key": "k"},
        {"week": 1, "partner_id": "P1", "clinic": "C1", "measure": "bp_control",
         "result_recorded": False, "met": None, "patient_key": "k2"},
    ])
    rows = care_gap_weekly(frame)
    assert rows[0]["label"] == "SYNTHETIC"
    assert rows[0]["visits"] == 2
    assert all(not isinstance(value, (dict, list)) for row in rows for value in row.values())
    paths = write_extracts(tmp_path, {"care_gap_weekly": rows})
    text = paths[0].read_text()
    assert "partner_id" in text and "{" not in text
    preview = write_preview(tmp_path / "preview.html", [("Weekly", rows)])
    html = preview.read_text()
    assert "Not a Tableau Public dashboard" in html
    assert "SYNTHETIC" in html
