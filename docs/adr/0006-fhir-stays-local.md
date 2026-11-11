# ADR 0006 — FHIR bundles stay on disk
Status: accepted (S5)

`fhir/hapi.py` can still read a public server's metadata document. `upload_bundle` does not POST, even if a caller passes `allow_write=True`. A public test server is world-readable. Synthea files are synthetic, and this project still does not upload them. The measure pipeline reads local files through `data/load.py`.
