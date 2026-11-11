"""Session metadata and practice tasks. Quizzes live in bank.py."""

SESSIONS = [
    {
        "id": 1,
        "week": 1,
        "title": "Frame the program and keep numbers out of the model",
        "minutes": "45–60",
        "ticket": "COA-101, COA-105",
        "artifact": "PRD, portable backlog, green tests, fidelity guard",
        "blurb": "The north star is a care-gap rate on a simulated network. The model, if you attach one, only rewrites sentences that already survived the guard.",
        "read": [
            "PRD.md — users, measures, and the non-goals.",
            "docs/backlog/backlog.csv — the build board, separate from the later program-control tasks.",
        ],
        "practice": """Work on a branch. Do not commit practice edits to main.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/test_fidelity.py tests/test_config.py
```

1. In a scratch script, call `check_narrative` with a sentence that adds a percentage the facts do not contain.
2. Confirm the result is not ok, and that the same sentence passes when that percentage is added to the facts.

**Extra.** Why does the template get checked before `ollama` is ever called?
""",
    },
    {
        "id": 2,
        "week": 1,
        "title": "Local FHIR into tested SQL views",
        "minutes": "50–70",
        "ticket": "COA-102",
        "artifact": "Flattened bundles, raw tables, measure views, SQL tests",
        "blurb": "Synthea bundles stay on disk. The parser keeps only the codes the three measures need. SQL tests fail the load when a row breaks a rule.",
        "read": [
            "docs/MEASURES.md — the simplified definitions, and what they are not.",
            "DATA_LICENSES.md — CMS and Synthea, and why the raw files are gitignored.",
        ],
        "practice": """The unit tests do not need the 1.5 GB download.

```bash
pytest tests/test_fhir_parse.py tests/test_measures.py
```

Read `sql/tests/patient_unique.sql` and say what a non-zero result would mean for every rate downstream.

**Extra.** Why is the HAPI upload function a hard block rather than a flag?
""",
    },
    {
        "id": 3,
        "week": 1,
        "title": "A synthetic network and a care-versus-data call",
        "minutes": "60–80",
        "ticket": "COA-103, COA-104",
        "artifact": "Triage memo that names the seeded cell",
        "blurb": "Eight partner groups, three clinics, three measures. The flag rule is a drop of at least 10 points plus a Bonferroni-adjusted test. A jump in missing results is a data issue, and outreach waits.",
        "read": [
            "scenarios/README.md — baseline rates are parameters, because the public Synthea sample shows complete diabetes control.",
            "scenarios/clinic_bp_drop.yaml and scenarios/missing_a1c_feed.yaml — one shock each.",
        ],
        "practice": """```bash
pytest tests/test_triage.py
```

These four files are the dev set. They are recovered on purpose and they are not the eval score.

**Extra.** Why can two clinic flags on the same partner and measure become a partner-level call?
""",
    },
    {
        "id": 4,
        "week": 2,
        "title": "A Salesforce-shaped pipeline next to the open gaps",
        "minutes": "45–60",
        "ticket": "COA-106, COA-107",
        "artifact": "Stage conversion, aging, readiness × gaps, import CSVs",
        "blurb": "Accounts, contacts, and opportunities mirror a CRM shape so the same files can be imported later. Stalled means more than 14 days and not Live.",
        "read": [
            "docs/adr/0004-salesforce-shaped-crm-stand-in.md",
            "src/care_ops_agent/metrics/pipeline.py — conversion, aging, open gaps.",
        ],
        "practice": """```bash
pytest tests/test_pipeline.py
```

**Extra.** Why can an account be in Data Onboarding and still be marked stalled?
""",
    },
    {
        "id": 5,
        "week": 2,
        "title": "Charter, WBS, RAID, change log, and an Asana file",
        "minutes": "50–70",
        "ticket": "COA-108",
        "artifact": "Controls workbook and Asana CSV",
        "blurb": "Hours and dollars are synthetic project-controls figures. A change request sits outside the baseline so the variance is visible. The Asana client writes a file unless a token is actually configured.",
        "read": [
            "docs/adr/0005-offline-asana-and-salesforce.md",
            "docs/samples/program_controls.xlsx — open the RAID and the change log.",
        ],
        "practice": """```bash
pytest tests/test_controls.py tests/test_clients.py
```

**Extra.** What happens to the forecast if CR-001 is folded into the baseline instead of kept beside it?
""",
    },
    {
        "id": 6,
        "week": 2,
        "title": "Weekly PDSA and three audiences",
        "minutes": "50–70",
        "ticket": "COA-109, COA-110",
        "artifact": "Cycle log and partner, internal, and steering notes",
        "blurb": "The same week is told three ways. The partner note is built from that partner's rows only, then scanned. A leaked id fails the run.",
        "read": [
            "docs/PERMISSIONS.md",
            "docs/samples/updates/ — compare P1.md with steering.md.",
        ],
        "practice": """```bash
pytest tests/test_pdsa_ab_rfp.py::test_pdsa_and_partner_filter_on_the_program_story
```

**Extra.** Why is abandon used when a flag clears, and not on a week that was quiet from the start?
""",
    },
    {
        "id": 7,
        "week": 2,
        "title": "Outreach A/B on gaps closed",
        "minutes": "40–55",
        "ticket": "COA-111",
        "artifact": "Sample size, randomization, two-proportion readout",
        "blurb": "Script rates are scenario parameters. The trial is a PDSA cycle: scale the winner, or abandon the change when the test does not clear alpha.",
        "read": [
            "src/care_ops_agent/experiment/ab.py — the size formula and the decision rule.",
        ],
        "practice": """```bash
pytest tests/test_pdsa_ab_rfp.py::test_ab_power_recovers_effect_and_reports_null
```

**Extra.** Why can't the null trial ask the sample-size formula for a number?
""",
    },
    {
        "id": 8,
        "week": 3,
        "title": "An RFP library that cites or flags",
        "minutes": "40–55",
        "ticket": "COA-112",
        "artifact": "40 synthetic questions, citations, a tracker",
        "blurb": "Overlap against approved entries. A weak or tied match is flagged. Finance and accreditation questions are in the set so the drafter is not tempted to invent them.",
        "read": [
            "docs/sessions/session-8/LOGIC_TRACE.md",
            "docs/samples/rfp_tracker.xlsx",
        ],
        "practice": """```bash
pytest tests/test_pdsa_ab_rfp.py::test_rfp_library_cites_or_flags
```

**Extra.** What would a closer-but-wrong entry do if the margin rule were removed?
""",
    },
    {
        "id": 9,
        "week": 3,
        "title": "Held-out score and an MS Project file",
        "minutes": "55–75",
        "ticket": "COA-113, COA-114",
        "artifact": "Eval report and MSPDI schedule",
        "blurb": "Twenty scenarios the dev set does not include. Each miss has a name. The Gantt is XML because the free Asana plan has no dependencies.",
        "read": [
            "evals/README.md",
            "docs/EVAL_REPORT.md",
        ],
        "practice": """```bash
pytest tests/test_eval.py::test_heldout_catalog_shape tests/test_controls.py::test_controls_workbook_and_project_xml
```

The full score test reruns every scenario. Use it when you want the gates, not for a quick edit.

**Extra.** Why is a mixed scenario kept out of the top-1 denominator?
""",
    },
    {
        "id": 10,
        "week": 3,
        "title": "Extracts, a no-go, and resume lines",
        "minutes": "40–55",
        "ticket": "COA-115, COA-116",
        "artifact": "Tableau-ready CSVs, scaling workbook, resume bullets",
        "blurb": "One failed gate is a no-go. The resume quotes the harness. Tableau Public is a manual publish, and the HTML file is only a preview.",
        "read": [
            "RESUME_BULLETS.md",
            "docs/tableau/DASHBOARD_SPEC.md",
        ],
        "practice": """```bash
python -m care_ops_agent.run_program
```

Open `out/tableau/preview.html` and `out/program_controls.xlsx`.

**Extra.** Why would editing a resume number by hand break the test that compares the file to the harness?
""",
    },
]
