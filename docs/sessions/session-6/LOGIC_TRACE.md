# Session 6 logic trace — PDSA and three audiences

1. **Goal.** Turn each program week into plan / do / study / act, and write three updates from the same facts without leaking another partner into a partner note.
2. **Needed next.** An outreach experiment that is itself a PDSA cycle (S7).
3. **Libraries.** The existing triage functions and the numeric-fidelity guard. No new service.
4. **Code.** `pdsa/cycle.py` reruns triage on results up to that week. A data-issue flag adapts the plan (hold outreach, check the feed). A care-gap flag adopts targeted outreach. A cleared flag abandons the extra work. `pdsa/audience.py` holds the permissions matrix. Partner text is built only from that partner's rows, then scanned for every other partner id and name.
5. **Docs.** `docs/PERMISSIONS.md` matches the matrix in code.
6. **Buy-in.** None for the offline path. A real Salesforce sharing rule would replace the matrix later, not the leak check.
7. **Capability added.** Partner, internal, and steering notes under `out/updates/`.
8. **What it proves.** Per-audience reporting where the filter is the control, and a leaked partner id fails the run.
