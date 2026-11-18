# SIMULATION DISCLAIMER

The Harbor Health Plan program inside this repo is a **portfolio simulation**. "Harbor Health Plan", the 8 partner groups' program data, eligibility files, budgets, pipeline deals, contacts, contract stages, and outreach results are **synthetic** and labeled `SYNTHETIC` in those artifacts.

Separate from that program, the hosted demo (`published` schema and `streamlit_app.py`) reads public aggregate files from HRSA, CMS, and CDC. Those rows are not synthetic. They are also not a patient panel, not a contract this project holds, and not certified HEDIS. See [docs/HOSTING.md](docs/HOSTING.md) and [DATA_LICENSES.md](DATA_LICENSES.md).

- Partner names/locations are seeded from the public CMS *Hospital General Information* file. Using a real facility's name as a seed does **not** mean that facility has any relationship with this project, any payer, or the author.
- Patient-level clinical values are drawn from **Synthea** synthetic patients (no real people, no PHI).
- Quality measures are **HEDIS-style, simplified** definitions (see `docs/MEASURES.md`), not certified measure logic.
- The author has not owned real vendor, partner or contract relationships; all such work here is simulated.
- Not for clinical, contracting or coverage decisions. No government endorsement is implied (42 U.S.C. 1320b-10).
