# PRD — care-ops-agent (v0, Session 1) · SIMULATION

## Positioning
invalid-agent is about **product quality** in biotech/IVD: lowering an assay's invalid rate. care-ops-agent is about **patient outcomes** in **healthcare delivery**: closing care gaps across a provider network so more patients reach diabetes control and blood-pressure control and more women get breast cancer screening.

## Problem
A value-based care organization ("Harbor Health Plan", synthetic) has 8 partner provider groups. Too many patients have open care gaps: HbA1c not controlled, BP not controlled, mammograms overdue. The network team spends its week stitching together gap lists, partner readiness, outreach progress and partner updates by hand. The gaps that matter most get lost in the noise, and patients wait.

## Outcome goal (north star)
**Raise the share of attributed patients meeting each care-gap measure, network-wide and per partner**, with the biggest movement where gaps are widest. Every rate is computed in code from tested tables.

## Users
- **Network care-gap program lead (Neel in the sim):** decides where outreach and partner support go each week.
- **Quality / population-health lead:** needs to tell a real gap signal from noise or a data artifact.
- **Partner practice manager (simulated):** needs a short, partner-safe list of patients and gaps to act on.
- **Clinical + steering leads:** want progress on outcomes and a go/no-go on scaling.

## Measures (HEDIS-style, simplified; see docs/MEASURES.md)
HbA1c control (<8.0%) · BP control (<140/90) · Breast cancer screening (mammogram within 27 months, women 52–74 at year end).

## Success metrics
Outcome metrics (the program's, computed in the sim; never quoted on a résumé unless produced by the eval report):
- Met rate per measure, network and per partner, with 95% Wilson intervals; change vs baseline.
- Open gaps closed per week; share of the widest-gap partners improving.
Agent-quality metrics (measured in the eval harness later):
- Does the agent point outreach to the partner/clinic where the gap truly is (top-1/top-3 vs seeded truth)?
- Does it flag gaps caused by missing data instead of missing care?
- Numeric fidelity of every written number (target 100%); partner-safe views leak no other partner's patients (target 0).

## User stories (Sprint 1 excerpt; full list in docs/backlog/backlog.csv)
- **COA-101** As the program lead, I want one command that installs and tests the repo, so reviewers trust it.
  *Given* a fresh clone *When* I run `pip install -e ".[dev]" && pytest` *Then* all tests pass with no secrets.
- **COA-102** As the quality lead, I want CMS and Synthea data in tested tables, so every care-gap rate traces to SQL that passed its checks.
  *Given* raw files *When* I build the marts *Then* every model builds and every SQL test passes.
- **COA-103** As the program lead, I want each partner's care-gap rates with intervals and a weekly control chart, so outreach goes where patients are actually falling behind.
  *Given* a scenario with one clinic whose patients lose BP control *When* triage runs *Then* the memo names that partner and clinic first.
- **COA-104** As the quality lead, I want gaps caused by missing lab feeds flagged as data issues, so we don't send outreach for care that already happened.
- **COA-105** As the program lead, I want any LLM-written number that doesn't match the code rejected.
- **COA-106** As the program lead, I want the partner pipeline (readiness stage, aging) next to each partner's open gaps, so I know which partners can start outreach now.

## Non-goals
Real PHI or real partners, certified measure logic, clinical recommendations for individual patients, contracting decisions, real CRM data, multi-agent crews, fine-tuning.

## Risks
Simplified measures could read as clinical claims → disclaimer + MEASURES.md. Synthea sample is 1,171 patients → used as the source of clinical value distributions; synthetic partner panels sample from it and say so.
