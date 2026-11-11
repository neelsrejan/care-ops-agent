"""Approved answers for a synthetic payer RFP.

Questions are things a payer might ask a care-gap vendor. Entries are the only
sentences the drafter is allowed to use. Nothing here describes a real bid.
"""

from __future__ import annotations

ENTRIES: list[dict[str, str]] = [
    {
        "id": "LIB-01",
        "title": "HEDIS-style measure definitions",
        "body": (
            "HbA1c control, blood-pressure control, and breast cancer screening are HEDIS-style "
            "definitions in this simulation. They are simplified teaching measures, not certified HEDIS logic."
        ),
    },
    {
        "id": "LIB-02",
        "title": "Where the rates come from",
        "body": (
            "Every care-gap rate, interval, and p-value is computed in Python from the scenario tables. "
            "The language model may rewrite a sentence and may not introduce a number."
        ),
    },
    {
        "id": "LIB-03",
        "title": "No real patients",
        "body": (
            "The panel is synthetic. Synthea patients are not real people, partner groups are not contracted "
            "providers, and the project stores no PHI."
        ),
    },
    {
        "id": "LIB-04",
        "title": "Wilson intervals",
        "body": (
            "A met rate is reported with a Wilson score interval because a bare percentage on a small "
            "clinic panel overstates how precise the week was."
        ),
    },
    {
        "id": "LIB-05",
        "title": "Missing feed versus missed care",
        "body": (
            "When visits lose their recorded result, the cell is a data issue. The program holds patient "
            "outreach for that measure until the feed check closes."
        ),
    },
    {
        "id": "LIB-06",
        "title": "Weekly PDSA",
        "body": (
            "The operating rhythm is a weekly PDSA cycle: plan the focus, do the outreach or the feed check, "
            "study the rates, and act by adopt, adapt, or abandon."
        ),
    },
    {
        "id": "LIB-07",
        "title": "Partner-safe updates",
        "body": (
            "A partner-safe update names only that partner's own panel. Another partner's id, name, or "
            "patients are filtered out before the note is written."
        ),
    },
    {
        "id": "LIB-08",
        "title": "Pipeline stages",
        "body": (
            "The Salesforce-shaped pipeline uses Prospect, Qualified, Agreement (simulated), Data Onboarding, "
            "and Live. Agreement is a label in the simulation, not a contract the author negotiated."
        ),
    },
    {
        "id": "LIB-09",
        "title": "Stalled onboarding",
        "body": (
            "An account that is not Live and has spent more than 14 days in its current stage is stalled. "
            "Outreach waits while that onboarding stage is cleared."
        ),
    },
    {
        "id": "LIB-10",
        "title": "Outreach experiment",
        "body": (
            "The outreach experiment randomizes synthetic patients to script A or script B, sizes the arms "
            "with a two-proportion power calculation, and reads gaps closed with a two-sided test."
        ),
    },
    {
        "id": "LIB-11",
        "title": "Asana stand-in",
        "body": (
            "The plan is an Asana CSV import plus an offline client. A live Asana workspace is not connected "
            "until a token is supplied outside the repo."
        ),
    },
    {
        "id": "LIB-12",
        "title": "Tableau extracts",
        "body": (
            "Reporting ships Tableau-ready CSV extracts and a written dashboard spec. Publishing to Tableau "
            "Public is a manual step and needs the author's own account."
        ),
    },
    {
        "id": "LIB-13",
        "title": "Local FHIR",
        "body": (
            "FHIR R4 bundles stay in local files. The project does not upload them to a public HAPI server "
            "or any other shared FHIR endpoint."
        ),
    },
    {
        "id": "LIB-14",
        "title": "Program controls budget",
        "body": (
            "The charter, WBS, RAID log, change log, and budget burn are synthetic project-controls figures. "
            "They are not a vendor bid and not a health-plan P&L."
        ),
    },
    {
        "id": "LIB-15",
        "title": "Synthea roster",
        "body": (
            "Synthea supplies the patient roster and the measure denominators. Outcome probabilities are "
            "scenario parameters because the public sample shows complete diabetes control."
        ),
    },
    {
        "id": "LIB-16",
        "title": "Multiple comparisons",
        "body": (
            "Partner and clinic cells are tested together, so the flag rule uses a Bonferroni adjustment "
            "on the two-proportion test to keep quiet weeks quiet."
        ),
    },
    {
        "id": "LIB-17",
        "title": "Scale decision",
        "body": (
            "The scaling go/no-go reads the eval gates: fidelity, partner leaks, false alarms, top-1 recovery, "
            "the care-versus-data call, and the outreach experiment. A failed gate is a no-go."
        ),
    },
    {
        "id": "LIB-18",
        "title": "How answers are cited",
        "body": (
            "An RFP draft may quote one approved library entry and must cite that entry id. A question with "
            "no matching entry is flagged for a person instead of answered from scratch."
        ),
    },
]

# Two questions per entry, written in payer language that still shares the entry's nouns.
# Four further questions are outside the library on purpose.
_PAIRS: list[tuple[str, str, str]] = [
    ("LIB-01", "Clinical quality", "Are HbA1c control, blood-pressure control, and breast cancer screening certified HEDIS or simplified HEDIS-style definitions?"),
    ("LIB-01", "Clinical quality", "Which HEDIS-style definitions does the care-gap program actually track?"),
    ("LIB-02", "Data", "Are care-gap rates, intervals, and p-values computed in Python, or does the language model calculate them?"),
    ("LIB-02", "Data", "Can the language model introduce a number that was not computed in Python?"),
    ("LIB-03", "Privacy", "Does the panel contain PHI or any real patients?"),
    ("LIB-03", "Privacy", "Are the partner groups contracted providers or synthetic groups with no PHI?"),
    ("LIB-04", "Measurement", "Why is a met rate shown with a Wilson score interval instead of a bare percentage?"),
    ("LIB-04", "Measurement", "How do you keep a small clinic panel from looking more precise than the week was?"),
    ("LIB-05", "Operations", "If recorded results disappear, is that missed care or a data issue, and do you hold patient outreach?"),
    ("LIB-05", "Operations", "When do you hold patient outreach until a feed check closes?"),
    ("LIB-06", "Operations", "Is the weekly operating rhythm a PDSA cycle, and what do adopt, adapt, and abandon mean?"),
    ("LIB-06", "Operations", "Walk through one weekly PDSA cycle from the plan step to the act step."),
    ("LIB-07", "Privacy", "What does a partner-safe update contain, and can it name another partner?"),
    ("LIB-07", "Privacy", "How do you keep another partner's patients out of a partner-safe update?"),
    ("LIB-08", "Implementation", "What Salesforce-shaped stages run from Prospect through Data Onboarding to Live?"),
    ("LIB-08", "Implementation", "Is the Agreement stage a simulated label or a contract someone negotiated?"),
    ("LIB-09", "Implementation", "When is an account stalled, and does outreach wait past 14 days in stage?"),
    ("LIB-09", "Implementation", "What happens to outreach while a stalled onboarding stage is still open?"),
    ("LIB-10", "Experimentation", "How is the outreach experiment sized, and what does the two-proportion test read?"),
    ("LIB-10", "Experimentation", "Do you randomize synthetic patients to script A or script B before reading gaps closed?"),
    ("LIB-11", "Project management", "Is the work plan a live Asana workspace or an Asana CSV import with an offline client?"),
    ("LIB-11", "Project management", "What has to be supplied before a live Asana workspace is connected?"),
    ("LIB-12", "Reporting", "Do you ship Tableau-ready CSV extracts, and is Tableau Public publishing manual?"),
    ("LIB-12", "Reporting", "What account is required before the dashboard spec is published to Tableau Public?"),
    ("LIB-13", "Data", "Do FHIR R4 bundles stay in local files, or are they uploaded to a public HAPI server?"),
    ("LIB-13", "Data", "Will implementation post bundles to a shared FHIR endpoint?"),
    ("LIB-14", "Project management", "Are the charter, WBS, RAID log, and budget burn a vendor bid or synthetic project-controls figures?"),
    ("LIB-14", "Project management", "Is the budget burn a health-plan P&L?"),
    ("LIB-15", "Data", "Does Synthea supply outcome probabilities or only the roster and the denominators?"),
    ("LIB-15", "Data", "Why are outcome probabilities scenario parameters if the public sample shows complete diabetes control?"),
    ("LIB-16", "Measurement", "How does the Bonferroni adjustment keep a quiet week from lighting up every clinic cell?"),
    ("LIB-16", "Measurement", "Why is the two-proportion flag rule adjusted when many partner and clinic cells are tested together?"),
    ("LIB-17", "Governance", "Which eval gates does the scaling go/no-go read before a failed gate becomes a no-go?"),
    ("LIB-17", "Governance", "Does a partner-leak failure block the scaling decision?"),
    ("LIB-18", "Proposal process", "Must an RFP draft cite a library entry id, and what happens with no matching entry?"),
    ("LIB-18", "Proposal process", "Can a question with no matching entry be answered from scratch?"),
]

_OUTSIDE: list[tuple[str, str]] = [
    ("Finance", "What medical-loss ratio do you guarantee for the next fiscal year?"),
    ("Legal", "What malpractice limit will you carry on the production clinical workflow?"),
    ("Accreditation", "Are you currently surveyed by The Joint Commission for this product?"),
    ("Finance", "What dividend did the parent company declare last quarter?"),
]


def questions() -> list[dict[str, str]]:
    rows = []
    for index, (entry_id, section, text) in enumerate(_PAIRS, 1):
        rows.append({
            "id": f"RFP-{index:03d}",
            "section": section,
            "owner": "RFP coordinator (SYNTHETIC)",
            "question": text,
            "expect": entry_id,
        })
    for offset, (section, text) in enumerate(_OUTSIDE, 1):
        rows.append({
            "id": f"RFP-{900 + offset}",
            "section": section,
            "owner": "RFP coordinator (SYNTHETIC)",
            "question": text,
            "expect": "",
        })
    return rows
