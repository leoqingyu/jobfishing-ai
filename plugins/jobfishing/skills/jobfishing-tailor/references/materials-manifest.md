# Tailored materials manifest

Write this manifest only after both final PDF uploads succeed. It is a local handoff artifact, not a second App database.

```json
{
  "schema_version": 1,
  "mode": "tailored_latex",
  "job_id": 123,
  "generated_at": "2026-08-26T10:00:00Z",
  "environment_fingerprint": "...",
  "resume": {
    "local_path": "absolute/path/Candidate_Acme_CV.pdf",
    "filename": "Candidate_Acme_CV.pdf",
    "sha256": "...",
    "resume_choice": "tailored"
  },
  "cover_letter": {
    "local_path": "absolute/path/Candidate_Acme_Cover_Letter.pdf",
    "filename": "Candidate_Acme_Cover_Letter.pdf",
    "sha256": "...",
    "app_material_saved": true
  },
  "verification": {
    "facts_checked": true,
    "visual_checked": true,
    "text_layer_checked": true
  }
}
```

Use absolute local paths. Each `filename` is the clean employer-facing basename, not an App storage/download name. The application Agent must still confirm both files exist before browser upload and follow the outbound-filename rules in `$jobfishing-apply`. If it has to download either material again, it recreates a local copy with the manifest filename before attaching it. The App's current job materials are authoritative for snapshot creation; local hashes only protect the handoff within the current computer.
