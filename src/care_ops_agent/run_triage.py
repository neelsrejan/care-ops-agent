"""CLI: python -m care_ops_agent.run_triage scenarios/clinic_bp_drop.yaml"""

from __future__ import annotations

import json
import sys

from care_ops_agent import db
from care_ops_agent.config import load_settings
from care_ops_agent.nodes.triage import memo
from care_ops_agent.sim.network import build_network, load_scenario, seeds_from_db, simulate_results


def run(path: str) -> dict:
    sc = load_scenario(path)
    with db.connect() as con:
        net = build_network(sc, seeds_from_db(con))
    df = simulate_results(sc, net)
    out = memo(df, sc, net["partners"])
    s = load_settings()
    s.out_dir.mkdir(parents=True, exist_ok=True)
    (s.out_dir / f"{sc['id']}_triage.md").write_text(out["memo"])
    df.to_csv(s.out_dir / f"{sc['id']}_results_SYNTHETIC.csv", index=False)
    return {"scenario": sc["id"], "verdict": out["verdict"], "truth": sc["truth"], "fidelity_ok": out["fidelity"]["ok"]}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(run(p)))
