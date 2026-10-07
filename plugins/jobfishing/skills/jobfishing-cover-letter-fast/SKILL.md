---
name: jobfishing-cover-letter-fast
description: Generate one truthful, job-specific Cover Letter as a local Word file, fast — no resume selection, no ATS form filling, no browser involvement. Use when the user only wants a Cover Letter for a job, not a full application. Do not use this for submitting an application; hand off to `$jobfishing-apply` or `$jobfishing-apply-fast` for that.
---

# jobfishing Cover Letter (Fast)

Some requests are just "I need a cover letter for this job," not a full application pass. This Skill does exactly that and stops — it produces one verified local DOCX and, only on request, uploads it to jobfishing. It does not touch an ATS, does not pick or upload a resume, does not fill any form, and never opens a browser.

Access jobfishing data only through its MCP tools; never navigate, click, upload, or edit through the jobfishing frontend.

## Identify the job

The job does not need to already exist in jobfishing:

- If the user names a jobfishing job (by id, or company + title), call `get_job_detail` for the full description and match details.
- If the user instead pastes a JD directly in the conversation, use that text as the requirements source. Do not search jobfishing for a matching record unless the user asks you to.

Either way, call `get_experience_context()` for `basic_info`, experience, and saved answers — this is the only source of candidate facts. Never invent a skill, date, number, employer, or scope claim that is not in that context or an explicitly supplied resume.

## Draft once, review once

Follow the evidence plan and content contract in [cover-letter-quality.md](../jobfishing-apply/references/cover-letter-quality.md): extract the three to five requirements that matter most, cite verified evidence for each, and leave unsupported requirements visible as gaps rather than papering over them.

Draft the letter and self-review it against that same checklist (factual accuracy, JD coverage, honest gaps, no duplicated evidence, tone/length, consistency with whatever resume the user mentions) in one inline pass, in the same turn. Do not dispatch a separate reviewer subagent — that is what makes this fast. Apply at most one revision pass if the self-review finds a real problem; do not loop.

## Render and hand off

1. Render the final reviewed paragraphs locally to a clean DOCX and verify its visible and extracted text match. Write a small script and run it with `uv run --no-project --with python-docx script.py` (the user may have no Python or `python-docx` installed; `uv` fetches both). Do not use the jobfishing frontend or its renderer.
2. Name the file `<Candidate Name> - Cover Letter - <Company>.docx` (see [outbound-filenames.md](../jobfishing-apply/references/outbound-filenames.md) for the same clean-filename standard used elsewhere).
3. Tell the user where the local file is and show the letter content.
4. Only if the user asks to save it to jobfishing, and only when this is a real jobfishing job: call `upload_tailored_cover_letter` so it becomes that job's current Cover Letter. Do not call this for a job that only exists as a pasted JD.

## Explicitly out of scope

This Skill never selects or uploads a resume, never fills an ATS form, never opens a browser, and never calls `mark_applied`. If the user's next request is to actually submit this application, hand off to `$jobfishing-apply` (deliberate) or `$jobfishing-apply-fast` (quick pass) — either can reuse the Cover Letter this Skill just uploaded instead of generating a new one.
