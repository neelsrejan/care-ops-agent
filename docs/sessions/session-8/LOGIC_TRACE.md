# Session 8 logic trace — RFP response library

1. **Goal.** Answer a synthetic payer questionnaire only from approved entries, and flag everything else.
2. **Needed next.** A score for the rest of the agent (S9).
3. **Libraries.** The standard library for tokens. No embedding API.
4. **Code.** `rfp/bank.py` holds 18 approved entries and 40 questions (36 in library, 4 deliberately outside: medical-loss ratio, malpractice, Joint Commission, a dividend). `rfp/library.py` scores token overlap. A hit must clear a threshold and a margin over the runner-up, or the question is flagged. A cited draft must contain the entry id. The tracker assigns a synthetic owner role and a due date. It does not invent a person's name.
5. **Docs.** The workbook `out/rfp_tracker.xlsx`.
6. **Buy-in.** A real RFP library would be reviewed by counsel. This one is a simulation of the workflow.
7. **Capability added.** Retrieval that refuses to answer when the library does not cover the question.
8. **What it proves.** Proposal hygiene: cite or flag. The four out-of-scope questions are the test that the drafter does not improvise finance or accreditation claims.
