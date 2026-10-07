---
name: jobfishing-interview
description: Prepare for an interview from the exact jobfishing snapshot and application notes containing submitted answers, status timeline, email events, and feedback. Use only when the user explicitly asks for interview preparation for a tracked application. Do not invoke for general career advice or ordinary application batches.
---

# jobfishing Interview

Use the facts the employer actually received. Do not silently substitute the user's current resume or a later-edited cover letter for the application snapshot. Read and append jobfishing information only through its MCP tools; never operate the App frontend in a browser.

## Required App capabilities

Identify one tracking record, then require jobfishing to expose:

- tracking/application identity, company, role, applied time, and current status;
- the application snapshot with the submitted full JD, score, exact resume, and exact Cover Letter;
- the current user-editable application notes. Treat these notes as the per-application authority for exact submitted answers, submission evidence, chronological status/email events, recruiter feedback, and earlier interview notes;
- current Experience and the reusable answer library as supporting context. When a reusable answer differs from the application's recorded submitted answer, the application note is authoritative for what that employer received.

If an essential frozen material or JD is unavailable through the bundled MCP, name the missing App capability and stop before inventing endpoint paths or installing another client. Older applications may have incomplete notes; state the missing history and continue with the available snapshot instead of requiring another App schema.

## Build the preparation

1. Reconstruct the employer's view from the frozen materials and the exact submitted answers recorded in application notes.
2. Map likely interview themes to specific, truthful evidence in Experience and the submitted resume.
3. Draft STAR outlines as evidence prompts, not memorized fictional scripts.
4. Create honest gap bridges for requirements without direct evidence.
5. Reconstruct the stage timeline from application notes and use its email events and recruiter feedback to prioritize concerns, missing skills, next-round focus, and interviewer hints.
6. Prepare questions for the interviewer that are specific to the role, company, and interview stage.
7. Include a short schedule for final research, rehearsal, logistics, and follow-up.

## Save safely

Save the complete preparation as a local Markdown file in the user's current project, grouped by company, role, and tracking id. Do not upload the full preparation to jobfishing by default.

After the user reviews it, produce a concise dated summary of durable facts, open concerns, recruiter feedback, and post-interview lessons. Append it with `add_application_note`. If a real stage update also applies, use `update_application_status(tracking_id, status, notes=summary)` instead. Never remove or rewrite existing notes; only the user can edit or delete them in the frontend.
