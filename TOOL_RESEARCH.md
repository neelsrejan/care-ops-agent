# care-ops-agent: tool research (2026-11-03)

Goal: give care-ops-agent (healthcare delivery, patient outcomes) a different stack from invalid-agent (biotech product improvement: Jira, Streamlit, python-pptx, dbt + DuckDB, LangGraph, Ollama/Qwen, Python), using tools Neel's target roles actually ask for.

## 1. JD corpus counts (deterministic, `scripts/tool_counts.py`)
Corpus: **150 distinct JDs** (jds/ plus jd/JD.txt files under to-apply/, with .md/.txt/_2 copies de-duplicated) and **59 screener runs** (runs/*screener*.md, counted separately because they mostly hold gap notes). Count = number of distinct docs that mention the tool, not raw hits. Regex matching, so there's some noise ("R" and "Linear" are loose). Raw output: docs/tool_counts_2026-11-03.txt.

| Tool | JDs (of 150) | Screeners (of 59) |
|---|---|---|
| Tableau | 32 | 26 |
| Jira | 27 | 24 |
| Power BI | 26 | 17 |
| Excel | 24 | 14 |
| Python | 22 | 26 |
| Agile/Scrum | 19 | 19 |
| Lean/Six Sigma | 17 | 15 |
| SQL | 16 | 29 |
| Airtable | 15 | 9 |
| Confluence | 11 | 5 |
| Looker | 8 | 11 |
| Smartsheet | 6 | 16 |
| MS Project | 5 | 16 |
| Asana | 5 | 9 |
| Notion | 5 | 9 |
| Salesforce | 5 | 28 |
| Snowflake | 4 | 10 |
| dbt | 4 | 6 |
| Epic | 2 | 7 |
| Databricks | 2 | 6 |
| Monday.com | 2 | 1 |
| FHIR/HL7 | 1 | 4 |
| HubSpot | 0 | 6 |
| HEDIS | 0 | 1 |
| Zapier / Power Automate / n8n / Wrike / Mode / BigQuery / Cerner | 0 | 0–4 |

What stands out: BI tools (Tableau, Power BI) beat every PM tool except Jira. Smartsheet, MS Project and Salesforce show up much more in screener gap notes than in raw JD text.

## 2. Market signals (web)
- Breaknorm job-posting catalogue (as of 2026-11-03): companies naming each tool in postings were MS Project 9,855, Asana 3,824, Smartsheet 3,004, monday.com 2,152, ClickUp 934, Wrike 391. https://breaknorm.co/tools/category/project-work-management
- TechnologyChecker (DNS-based, Oct 2026): Hospitals & Health Care is Smartsheet's #1 industry at 6.95% of matched customers, including Kaiser Permanente and Optum. https://technologychecker.io/technology/smartsheet
- Smartsheet healthcare case study: Ballad Health's EPMO runs 150+ projects across 20 hospitals on Smartsheet. https://www.smartsheet.com/customers/ballad-health
- LinkedIn posts (self-reported, not rigorous): Jira at 28.4% of PM postings (https://www.linkedin.com/posts/ndavaul_projectmanagement-pmtools-careerdevelopment-activity-7373339842006437888-jCjb); "healthcare: compliance first, Epic/Cerner for IT projects" (https://www.linkedin.com/posts/irilamarr_i-analyzed-2500-pm-jobs-for-2025-us-activity-7366815573957177345-KWy1). Treat both as directional only.

## 3. Free-tier feasibility
| Tool | Solo/free option | Works for a portfolio? | Source |
|---|---|---|---|
| Smartsheet | No free plan for new signups since 2024-08-28. 30-day Business trial: no API tokens, no publishing; sheets are read-only for 30 days after the trial, then deleted | Weak. Manual only, screenshot or export before it expires | https://help.smartsheet.com/articles/2482687-free-plan , https://help.smartsheet.com/articles/529590-smartsheet-free-trial-faqs |
| Asana | Personal plan free (up to 2 users). API via personal access token, 150 req/min. No Timeline/Gantt or dependencies on free | Good, so the agent can create tasks over the API | https://asana.com/pricing , https://developers.asana.com/docs/rate-limits |
| monday.com | Free: 2 seats, 3 boards, 200 items, no automations or integrations | Too limited | https://support.monday.com/hc/en-us/articles/360010487220-Understanding-the-Free-Plan |
| Airtable | Free: 1,000 API calls per workspace per month | OK at small scale | https://support.airtable.com/articles/7735693959-managing-api-call-limits-in-airtable |
| Tableau | Tableau Public / Desktop Public Edition free. Published dashboards are public (good, since the data is synthetic) | Strong, and you get a shareable link | https://help.tableau.com/current/public/desktop/en-us/public_faq.htm |
| Power BI | Desktop free, but a free license can't publish or share | OK (.pbix in repo plus screenshots) | (search synthesis; check Microsoft licensing docs before claiming more) |
| Salesforce | Developer Edition free and ongoing (non-production, log in regularly) | Strong for the partner pipeline CRM | https://developer.salesforce.com/free-trials , https://developer.salesforce.com/blogs/2026/04/new-developer-edition-agentforce-vibes-claude-mcp |
| FHIR R4 | HAPI public test server https://hapi.fhir.org/baseR4, no credentials, purged regularly, never store PHI. Or run HAPI locally (Apache 2.0) | Strong, synthetic Synthea bundles only | https://hapi.fhir.org/ , https://confluence.hl7.org/spaces/FHIR/pages/35718859/Public+Test+Servers |

## 4. Recommended swap table
| invalid-agent tool | care-ops-agent replacement | Why |
|---|---|---|
| Jira | **Asana** (API-driven program plan, milestones, partner onboarding tasks). Optional: a one-off **Smartsheet** trial Gantt/dashboard built manually and exported | Asana: 5 JDs / 9 screeners, #2 in Breaknorm (3,824 cos), free API. Smartsheet: 6 / 16 and #1 industry is healthcare, but there's no free plan or trial API, so it can't be the agent's system of record |
| Streamlit | **Tableau Public** (quality-measure dashboard, control charts by partner). Power BI Desktop as an alt | Tableau is the #1 tool in the corpus (32 JDs / 26 screeners) and free to publish. Power BI is 26 / 17 but can't publish free |
| python-pptx deck | **Excel workbook via openpyxl** (weekly partner scorecard, risk/RAID log, go/no-go gate tracker) | Excel 24 JDs. Fits program-ops reporting and doesn't repeat the deck output |
| dbt + DuckDB | **PostgreSQL + plain SQL views** (or a Snowflake 30-day trial if he wants the brand name) | SQL 16 JDs / 29 screeners (the most-cited gap). dbt is only 4 JDs and already on invalid-agent. **PLAN.md session 2 currently says dbt/DuckDB and needs updating** |
| local mock CRM | **Salesforce Developer Edition** (partner/account pipeline objects) | Salesforce: 28 screener gap notes (top gap), free and non-expiring. Health Cloud availability in Dev Edition not verified |
| (none) | **FHIR R4 (HAPI) + Synthea**: ingest Patient/Observation/Condition bundles | The healthcare-only differentiator. Epic/FHIR show up in screener gaps (7 / 4). Synthetic data only, no PHI |
| (none) | **HEDIS-style / CMS eCQM measures** (HbA1c control, BP control, breast cancer screening, i.e. CMS122/CMS165/CMS125-style logic) computed deterministically in Python/SQL | Patient-outcomes framing. Say "HEDIS-style" because HEDIS is an NCQA trademark and we don't run certified measures |
| (none) | **Lean / PDSA improvement cycles** on control charts | 17 JDs. Matches the outcomes-improvement story |
| LangGraph | Plain Python tool-calling orchestration (or the OpenAI Agents SDK / PydanticAI) | No JD signal either way. Swapping only adds variety. Low priority |
| Ollama/Qwen | Keep local LLM (no-PHI story), or any hosted model on synthetic data | No JD signal. Not worth resume space |
| Python | Keep | 22 JDs. All metrics computed deterministically in Python/SQL. The LLM only drafts narrative, and resume numbers stay blank until evals produce them |

Resume framing: invalid-agent = biotech, product improvement (Jira, dbt, Streamlit). care-ops-agent = healthcare delivery, patient outcomes (Asana, Tableau, Salesforce, PostgreSQL/SQL, FHIR, HEDIS-style measures, Excel). The only overlap is Python.
