#!/usr/bin/env python3
"""Write narration YAML from the clip list below."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "academy" / "narration"


def clip(session, stem, title, file, overview, segments):
    return {
        "session": session,
        "stem": stem,
        "title": title,
        "file": file,
        "overview": " ".join(overview.split()),
        "segments": [{"lines": lines, "say": " ".join(say.split())} for lines, say in segments],
    }


CLIPS = [
    clip(1, "01_config", "Session 1 · Where settings live",
         "../../../src/care_ops_agent/config.py",
         "config.py is the boundary between the process environment and the rest of the program. "
         "Measure targets, the model switch, and the output folder are read here so triage, the CRM, "
         "and the exporters do not each invent their own paths. Secrets are not stored. A missing "
         "variable falls back to the deterministic demo, which is what CI runs.",
         [
             ("1-27", "This file is the settings boundary. The constants at the top are simulation targets for a synthetic program, not a contract benchmark. Eight partners and three measure goals live here so every later module quotes the same numbers."),
             ("29-38", "find_repo_root walks upward until it sees the project file beside the package. That matters because a test, a notebook, and the installed package do not share a working directory. Scenario paths stay correct without a hard-coded laptop folder."),
             ("42-63", "Settings is frozen. rules_only is true when the backend is deterministic, which is the default. redacted and the custom repr exist so a future token added to this object is not printed just because someone logged the settings."),
             ("66-79", "load_settings reads the environment. Unknown or blank model backends collapse to deterministic. The output directory defaults under the repo. Nothing here opens a network connection."),
         ]),
    clip(1, "02_fidelity", "Session 1 · Numbers stay in the code",
         "../../../src/care_ops_agent/guards/numeric_fidelity.py",
         "The fidelity guard sits between any prose and the reader. Triage, PDSA notes, and steering "
         "updates all pass through it. It does not compute rates. It only checks that every number in "
         "a sentence already exists in the facts Python produced. That is why a model is allowed to "
         "rewrite wording and not allowed to invent a percentage.",
         [
             ("1-17", "The guard rejects narrative numbers that are not in the computed facts. Identifiers such as a partner id are masked first so a label is not mistaken for a rate."),
             ("27-44", "Walking the facts collects the raw value, a rounded form, and the percent form when the value is a proportion. That is why a sentence may say 62 percent when the fact was 0.62, and why a nearby invention still fails."),
             ("66-88", "check_narrative strips dates and known identifier strings, then every remaining number must sit near an allowed value. A miss returns ok false. Callers treat that as a failed draft, not as a warning to ignore."),
         ]),
    clip(2, "01_parse", "Session 2 · Flatten only what the measures need",
         "../../../src/care_ops_agent/fhir/parse.py",
         "parse.py is the edge between a FHIR bundle and the relational rows the SQL views expect. "
         "It keeps diabetes, hypertension, HbA1c, blood pressure, and mammography codes, and drops "
         "the rest of the bundle. Downstream views never see a raw JSON document. That keeps the "
         "measure logic in SQL and the file format in one module.",
         [
             ("1-21", "The module docstring states the contract: three measures, and blood pressure stored as components. The code constants are the clinical codes those measures look up. Changing a code here changes who lands in a denominator."),
             ("23-29", "Helpers pull the first coding and the id from a FHIR reference. They are small on purpose. The bundle shape stays in this file so the loader can stay a copy loop."),
             ("32-76", "flatten_bundle walks one Synthea bundle into patient, condition, observation, and procedure rows. iter_bundles and flatten_all are how the loader streams a directory of files without posting them anywhere."),
         ]),
    clip(2, "02_load", "Session 2 · Local files into checked tables",
         "../../../src/care_ops_agent/data/load.py",
         "load.py is the only place that writes the raw tables. It reads local FHIR files and the "
         "CMS csv, copies rows into PostgreSQL, then builds the views and runs the SQL tests. "
         "CI does not call it, because the raw download is large and gitignored. The unit tests "
         "prove the parser and the rate math on fixtures instead.",
         [
             ("1-23", "Column lists are the contract with the schema. The CMS rename map keeps only name and place fields. Quality stars are not loaded, because they are not the care-gap measures."),
             ("25-42", "load connects, applies the schema, copies each table, creates the mart schema, and applies the views. Counts come back from SQL. A failed copy stops the pipeline before any rate is quoted."),
             ("45-58", "The command-line entry is how a person with the raw files and a local database rebuilds the marts. It is optional for the demo, which uses the committed roster instead."),
         ]),
    clip(3, "01_network", "Session 3 · A network with a known shock",
         "../../../src/care_ops_agent/sim/network.py",
         "network.py builds the synthetic panel and the weekly results. Partners are name seeds, "
         "patients are resampled denominator ids, and whether a visit meets the measure is drawn "
         "from the scenario, not from Synthea. Triage, the pipeline, and the PDSA loop all consume "
         "this frame. A second code path exists for scenarios that inject more than one shock, so "
         "the original four dev scenarios keep their random draws.",
         [
             ("1-23", "The header says the panel is synthetic and the outcome probabilities are scenario parameters. Visit probability and panel size are design choices. They set how many observations a clinic week will have, which is what makes a ten-point drop detectable."),
             ("26-52", "load_scenario reads YAML. seeds_from_db is the path that uses PostgreSQL when the marts exist. build_network picks eight facilities and assigns each patient to a partner, a clinic, and a measure. The ids are new. The facility name is only a seed."),
             ("55-94", "When a scenario lists several injections, this branch applies each one. A clinic drop, a partner drop, and a missing feed can land on different partners in one story. Dev scenarios do not use this branch."),
             ("97-121", "The original single-injection loop is unchanged so the four scenarios the rule was tuned on still recover. Missing results are drawn only on the shocked rows. Every other visit uses the baseline probability."),
         ]),
    clip(4, "01_crm", "Session 4 · A CRM shape without a login",
         "../../../src/care_ops_agent/crm/mock.py",
         "mock.py is the Salesforce-shaped store. Accounts, contacts, opportunities, and stage "
         "history are ordinary rows so the same files can be imported later. Pipeline metrics "
         "read these rows. The live HTTP client lives in a different module and is not called. "
         "apply_pipeline_stall is how a held-out scenario forces one opportunity to age in stage "
         "without changing the random draws of the other accounts.",
         [
             ("1-19", "Stages run from Prospect to Live. Agreement is labeled simulated in the stage name because no contract was negotiated. Contacts are roles, not generated people."),
             ("22-48", "build_crm gives every partner and a few prospects an opportunity and a stage history. Time in the current stage is drawn so the book is not accidentally all stalled. The label SYNTHETIC is on the account."),
             ("51-83", "apply_pipeline_stall rewrites one opportunity when the scenario asks for it. The stage and the entered date are set so aging will mark it stalled. Dev scenarios omit the block, so their CRM is untouched."),
             ("86-99", "export_salesforce_csv writes one file per object. Those files are what a Data Import Wizard would load. Writing them does not contact Salesforce."),
         ]),
    clip(4, "02_pipeline", "Session 4 · Stage next to open gaps",
         "../../../src/care_ops_agent/metrics/pipeline.py",
         "pipeline.py answers a program question the CRM rows alone do not: who can take outreach "
         "now, and who is stuck. Conversion, aging, and open gaps are computed here in Python. "
         "The readiness view joins them. PDSA and the Tableau extract both read this view, so "
         "the definition of stalled lives in one place.",
         [
             ("1-14", "Stalled means more than fourteen days and not Live. The constant is the rule. Changing it changes the workbook, the eval, and the partner note together."),
             ("17-32", "Conversion counts who reached each stage and who moved on. Aging turns the entered date into days and sets the stalled flag. Live never stalls, even if the date is old."),
             ("35-53", "Open gaps use each patient's latest result. A missing result counts as open. readiness_view attaches those gaps to the stage and sorts partners who can start outreach ahead of the rest."),
         ]),
    clip(5, "01_plan", "Session 5 · One schedule, several sheets",
         "../../../src/care_ops_agent/controls/plan.py",
         "plan.py is the source of truth for the charter, the WBS, the RAID log, the change log, "
         "the burn, and the capacity check. Excel, MS Project XML, and the Asana file are views "
         "of this object. Hours times a synthetic rate produce the dollars. An approved change "
         "stays outside the baseline so the variance is a calculated difference, not an edited cell.",
         [
             ("1-31", "The module states that the dollars are project controls for a simulation, not a bid and not a P and L. Rates and funded full-time equivalents live next to that warning. The start date is a Monday so business-day math has a clean origin."),
             ("33-96", "The task table is the WBS. Summaries roll up. Leaves carry a role, a duration, and predecessors. CR-001 is marked out of the baseline. That single flag is what splits forecast from baseline later."),
             ("98-133", "Business days skip weekends. A successor starts the next weekday after the predecessor finishes. The program week index is how burn rows group cost. None of this is typed into the spreadsheet by hand."),
             ("136-189", "Leaves are scheduled in dependency order. Summaries then span their children. Hours are duration times eight. Cost is hours times the role rate. A summary does not add a second copy of the money."),
             ("321-349", "build_plan assembles the sheets and raises if any role is assigned more hours than the funded capacity. That check is the control. A pretty Gantt that overbooks the team does not leave this function."),
         ]),
    clip(5, "02_asana", "Session 5 · A tracker file, and a live client that waits",
         "../../../src/care_ops_agent/pm/asana.py",
         "asana.py is the boundary with the tracker. The offline client writes a CSV and SIM "
         "identifiers so a reviewer can see that no board was updated. The live client knows "
         "the REST shape and reads the token from the environment. The demo and the tests "
         "construct only the offline client. Switching later is an environment variable, not a rewrite.",
         [
             ("1-16", "The module docstring is the operating rule. Offline is the default. Live needs a token and a workspace id. Neither value is hard-coded."),
             ("27-67", "OfflineAsanaClient stores tasks with SIM gids and writes the importer columns Asana expects. Assignee is blank on purpose. There is no person to assign."),
             ("70-97", "LiveAsanaClient posts to the Asana API only when something calls create_task. Constructing it still requires both secrets. The demo never constructs it."),
             ("100-112", "asana_client_from_env is the switch. An unknown backend or a live backend with a blank token raises, instead of quietly writing a file and pretending the board moved."),
         ]),
    clip(6, "01_pdsa", "Session 6 · A week is a cycle",
         "../../../src/care_ops_agent/pdsa/cycle.py",
         "cycle.py turns the triage output into plan, do, study, and act for each program week. "
         "It does not invent a new statistic. It reuses analyze on the results up to that week, "
         "then chooses adopt, adapt, or abandon from the flags. The sentence it writes still "
         "goes through the fidelity guard, so the cycle log cannot drift from the counts.",
         [
             ("1-18", "The file owns the weekly rhythm. A data issue and a care gap are different acts. The guard is imported because the memo is prose about numbers."),
             ("31-55", "Each week slices the results, runs the same triage, and compares the flag set with last week. A data issue adapts the plan and holds outreach. A care gap adopts targeted outreach. A flag that disappeared is abandoned. A week that was always quiet just keeps monitoring."),
             ("56-89", "The memo is filled from a facts dict and passed to narrate. If the guard fails, the run raises. The returned rows are what the extract and the workbook show. The language model is not asked which act to pick."),
         ]),
    clip(6, "02_audience", "Session 6 · Three views, one analysis",
         "../../../src/care_ops_agent/pdsa/audience.py",
         "audience.py is the permissions boundary. Steering, internal, and partner notes are "
         "rendered from the same analysis, but the partner function only receives that partner's "
         "rows. A scan then looks for every other partner id. The matrix at the top is the spec "
         "the renderer is supposed to obey. A leak fails the eval even if the triage was right.",
         [
             ("1-22", "The dictionary is the spec. Partner notes may not see other partners or the budget. Steering may see flagged partners and the budget rollup, and may not see patient keys. Internal may see the working set."),
             ("25-66", "permissions_markdown is the same matrix written down for a reader. network_rates rolls the recent window up to the measure, which is the grain steering needs. leak_findings is the backstop: another partner id or name in the text is a finding."),
             ("73-160", "render_updates builds facts, writes steering and internal through the guard, then one note per partner from that partner's flags only. The leaks map is returned to the caller. The eval sums it and treats any hit as a failed gate."),
         ]),
    clip(7, "01_power", "Session 7 · Size the test before the draw",
         "../../../src/care_ops_agent/experiment/ab.py",
         "ab.py is the outreach experiment. It is a PDSA cycle, not a side spreadsheet. The "
         "sample size is a normal approximation from the two planned rates. The draw happens "
         "after. Eval repeats the trial so one lucky seed is not the resume line. A null "
         "trial reuses the size, because the formula cannot divide by a zero difference.",
         [
             ("1-22", "The seeded rates are parameters. Script A and script B are not estimated from Synthea. Alpha and the power target are design choices written down where the formula can see them."),
             ("25-37", "sample_size_per_arm is the usual two-proportion calculation. It refuses equal rates, because the difference in the denominator would be zero. That is why the null trial must be handed a size."),
             ("40-47", "The readout is a two-sided test on the closed counts. The p-value is computed here. It is not typed into the JSON after the fact."),
         ]),
    clip(7, "02_trial", "Session 7 · Randomize, then decide",
         "../../../src/care_ops_agent/experiment/ab.py",
         "The second half of the same module is the trial itself and the bridge back to PDSA. "
         "Arms are shuffled first, then each synthetic patient draws an outcome at that arm's "
         "rate. The decision is scale B, scale A, or no difference. pdsa_from_trial maps a "
         "winner to adopt and a null result to abandon, so the experiment does not become a "
         "permanent change just because it was run.",
         [
             ("50-91", "run_trial shuffles equal arms, draws a closure for each patient, and compares the arms. Equal assignment is checked later in the test. The decision rule is explicit: significance and a higher rate, or no difference."),
             ("99-125", "effect_recovered and null_quiet are how the eval counts repeats. pdsa_from_trial does not recompute the test. It only names the act that follows a decision the code already made."),
         ]),
    clip(8, "01_library", "Session 8 · Cite an entry or flag the question",
         "../../../src/care_ops_agent/rfp/library.py",
         "library.py is the retrieval boundary. Questions come from the bank. Scoring is token "
         "overlap against the approved title and body. There is no embedding call. A weak or "
         "tied score is flagged so the closest entry is not automatically an answer. A cited "
         "draft must contain the entry id, which is what a reviewer can check.",
         [
             ("1-28", "The threshold and the margin are the refusal rule. The tracker start date only creates due dates. Owners in the bank are a role, not a person."),
             ("35-54", "Tokens drop short and common words. retrieve ranks entries and flags the question when the best score is low or too close to the runner-up. That is the difference between a hit and a guess."),
             ("57-89", "draft_answer either cites the id inside the sentence or writes a flag that says not to invent an answer. tracker assigns due dates from the start date. Nothing is sent to a proposal tool."),
             ("92-106", "answer_all is the score the test locks. A question is correct when the cite matches the expected entry, or when an out-of-library question stays flagged."),
         ]),
    clip(8, "02_bank", "Session 8 · The only sentences a draft may use",
         "../../../src/care_ops_agent/rfp/bank.py",
         "bank.py is the content boundary. The retriever does not own the wording. Eighteen "
         "entries cover the measures, the guard, the feeds, the pipeline, the experiment, and "
         "the decision not to upload FHIR. Forty questions include four that the library should "
         "refuse: a loss ratio, malpractice, accreditation, and a dividend. Those exist so a "
         "confident draft cannot wander into claims this project does not make.",
         [
             ("1-12", "The docstring says the questions are what a payer might ask and the entries are the only sentences the drafter may use. Editing an entry is a content change. Editing the threshold is a mechanism change. They are separate on purpose."),
             ("14-160", "Each entry is a short approved answer with an id. The ids are what drafts cite. If two entries shared the same rare words, the margin rule would flag the question instead of guessing."),
             ("205-223", "questions builds the forty rows. The last four have an empty expected id. The test requires those to come back flagged. That is the restraint check."),
         ]),
    clip(9, "01_eval", "Session 9 · Score what the rule was not tuned on",
         "../../../src/care_ops_agent/eval/harness.py",
         "harness.py is the score. It refuses the four dev scenario ids, runs the held-out "
         "catalog, and names the failure when a case misses. Top-1 is only for single-cause "
         "cases. Mixed shocks, stalls, leaks, fidelity, and the outreach repeats have their "
         "own counts. The resume and the go or no-go sheet are functions of this report, so "
         "they cannot quote a number the harness did not produce.",
         [
             ("1-36", "Dev ids are listed so a scenario cannot quietly enter the score. The repeat seeds for the experiment are fixed, which is why the resume counts are stable."),
             ("39-83", "Matching helpers compare a verdict or a flagged set with the seeded truth. The taxonomy distinguishes a wrong partner from a wrong measure, a false alarm, a missed signal, and a mixed case that did not find both shocks."),
             ("86-135", "score_scenario builds the network, writes the memo, checks fidelity, applies a stall if the scenario has one, and renders partner notes to count leaks. A dev id raises instead of being scored as a win."),
             ("154-192", "run_eval aggregates the denominators separately. Quiet scenarios are the false-alarm gate. Single-cause rows are the top-1 gate. The experiment block is appended from the same process so the report is one dict."),
         ]),
    clip(9, "02_mspdi", "Session 9 · Dependencies the free tracker does not store",
         "../../../src/care_ops_agent/export/mspdi.py",
         "mspdi.py is a view of the same plan object Excel already shows. Asana's free plan "
         "has no dependencies, so the Gantt lives in MS Project XML. Finish-to-start links "
         "are type 1. The file does not introduce dates that the scheduler did not compute. "
         "If the WBS changes, this export changes with it.",
         [
             ("1-19", "The namespace is the Project XML namespace. Durations are hours from the business-day count. The stamp helper only formats dates the plan already decided."),
             ("22-43", "Each task writes outline level, start, finish, duration, and predecessor links. The link type is finish to start. Notes carry the synthetic label and the role."),
             ("46-80", "project_xml adds a project summary and then the WBS. write_project_xml is what the program command calls. Opening the file in Project is a manual step, like the Tableau publish."),
         ]),
    clip(10, "01_extracts", "Session 10 · Rows a dashboard can import",
         "../../../src/care_ops_agent/export/tableau.py",
         "tableau.py is the handoff to a dashboard tool this repo cannot log into. It flattens "
         "weekly rates, the pipeline, the PDSA log, and the burn into scalar columns. A hyper "
         "extract is created later inside Tableau from these CSVs. The local HTML preview is a "
         "different module and is not this file. Publishing remains a manual step.",
         [
             ("1-16", "The docstring draws the line. These files are extracts. They are not a published workbook and they do not call Tableau Public."),
             ("19-48", "care_gap_weekly groups to the cell and uses the same rate helper as triage. The label column is SYNTHETIC on every row. Nested objects are not written, so an extract does not need a JSON parse."),
             ("51-105", "The other frames are the pipeline, the cycle log, and the burn. write_extracts is a thin CSV writer. The dashboard spec, not this module, decides which sheet uses which file."),
         ]),
    clip(10, "02_closeout", "Session 10 · The decision and the resume are the same report",
         "../../../src/care_ops_agent/run_program.py",
         "run_program.py is the close-out command. It builds the plan, the tracker file, the "
         "PDSA packet, the experiment, the RFP workbook, and the extracts without PostgreSQL "
         "and without a live account. The eval flag reruns the harness and writes the go or "
         "no-go workbook from those gates. One failed gate stays a no-go. The resume text is "
         "rendered from the same report so a hand-edited number cannot drift.",
         [
             ("1-22", "The command is the demo path. It says the roster is the fixture, not the large download, and that outcome rates still come from the scenario. The eval flag is optional because the score is slower than the weekly pack."),
             ("52-99", "The body asks the plan, the offline Asana client, the network, the cycle, the CRM, and the audience renderer to write their files. A live Asana client is refused here. Partner leaks are counted in the summary."),
             ("101-152", "The experiment, the RFP answers, and the extracts follow. With the eval flag, decision and resume_bullets are called on one report. The scaling workbook is that decision, not a separate opinion."),
         ]),
    clip(3, "02_triage", "Session 3 · Care gap or data issue",
         "../../../src/care_ops_agent/nodes/triage.py",
         "triage.py decides where patients are falling behind and whether the cause is care or "
         "data. It is the consumer of the weekly frame and the producer of the memo. PDSA, "
         "the audience notes, and the eval all call it rather than reimplementing the test. "
         "The Bonferroni adjustment and the missing-result rule live here so a quiet week and "
         "a broken feed do not become the same outreach list.",
         [
             ("1-21", "Thresholds are the operating rules: a ten-point drop, a missing-result share, and a family-wise alpha. They are constants because the eval scores the rule as it is, not a tuned variant per scenario."),
             ("23-47", "A rate counts an unrecorded visit as not met. The Wilson interval uses that denominator. The two-proportion helper is the one-sided test that the recent rate is lower."),
             ("50-97", "analyze builds partner cells and clinic cells, adjusts alpha by how many cells share a level, and flags a large significant drop. A high missing share labels the flag as a data issue. Two clinic flags on the same partner and measure promote the call to the partner."),
             ("108-134", "memo turns the top flag into sentences whose numbers are copied into the facts dict, then narrate runs the guard. The verdict is the structured call the eval compares to the seed. The prose is not a second opinion."),
         ]),
]


def main() -> None:
    for item in CLIPS:
        folder = OUT / f"session-{item['session']}"
        folder.mkdir(parents=True, exist_ok=True)
        payload = {
            "title": item["title"],
            "file": item["file"],
            "overview": item["overview"],
            "voice": "en-US-AndrewNeural",
            "rate": "+0%",
            "pause": 0.35,
            "segments": item["segments"],
        }
        path = folder / f"{item['stem']}.yaml"
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
