---
name: jobmatchflow-apply-fast
description: Run a fast, one-job-at-a-time or small-batch JobMatchFlow application pass that leans on ATS resume-parse autofill instead of deliberate per-job material selection. Use when the user explicitly asks for a quick/fast apply session through one or a few jobs. Do not use for a full deliberate batch run, first-time setup, or inbox sync — those stay with `$jobmatchflow-apply`.
---

# JobMatchFlow Apply Fast

A leaner sibling of `$jobmatchflow-apply` for speed. It shares the same MCP, the same host Chrome integration selection, the same outbound-filename rule, and the same Cover Letter content-quality bar — this Skill does not redefine those, it reuses them by reference. The only thing this Skill relaxes is ceremony that slows down submitting; it does not relax correctness or safety invariants.

Access JobMatchFlow data and files only through its MCP tools; never navigate, click, upload, download, or edit through the JobMatchFlow frontend. Use the user's visible Chrome profile only for ATS pages, employer sites, LinkedIn, and the job-search webmail inbox:

- In Codex, use the external ChatGPT Chrome integration. Never substitute the temporary in-app browser.
- In Claude Code, use Claude in Chrome. If it is not connected, ask the user to run `/chrome` and complete its permission flow.

If JobMatchFlow is not yet authorized or the shared setup has never been checked, run [setup-check.md](../jobmatchflow-apply/references/setup-check.md) from `$jobmatchflow-apply` first — do not duplicate that check here.

## Route the request

- For the full fast sequence, read [fast-workflow.md](references/fast-workflow.md).
- Before any ATS or email attachment upload, read [outbound-filenames.md](../jobmatchflow-apply/references/outbound-filenames.md).
- Whenever a Cover Letter is needed, read [cover-letter-quality.md](../jobmatchflow-apply/references/cover-letter-quality.md) for the content standard — [fast-workflow.md](references/fast-workflow.md) describes how the review pass is run without a dispatched subagent.
- For any LinkedIn Easy Apply candidate, read the "LinkedIn Easy Apply routing" section of [application-workflow.md](../jobmatchflow-apply/references/application-workflow.md) and follow it exactly as written. Nothing about that routing is simplified in fast mode.

Tailored materials remain a separate explicit request. If the user explicitly wants a tailored CV/Cover Letter pair for a job, route that job through `$jobmatchflow-tailor` first and resume this Skill only after both verified tailored files have been uploaded and handed off, exactly as `$jobmatchflow-apply` does.

## What stays exactly the same as `$jobmatchflow-apply`

- MCP-only access to JobMatchFlow; the frontend is never opened or operated.
- `get_experience_context().basic_info` is the authority for identity and contact fields, even when an ATS auto-fills different values from a parsed resume.
- Job data beyond the description: `contact` (name, email, phone from the JD, when present) for the greeting or recipient; `visa_sponsorship_offered` / `work_permit_required` checked against the user's work authorization (stop and ask when a job needs a permit they lack); `company_info` and `job_url_direct`. `salary` can be an estimate (`is_estimated`), never state it to an employer as fact.
- `list_tracking` is read before new submissions to avoid duplicates; `mark_applied` is the only post-submission transition and stays idempotent.
- Clean outbound filenames on every attachment, verified in the ATS/webmail UI before submit.
- No passwords, OTPs, or auth links in application notes.
- LinkedIn Easy Apply's official-posting-first, email-before-or-with-Easy-Apply fallback order.
- Submission requires either the user's final review or explicit direct-submit authorization already given in the current task — there is no App-side auto-confirm flag.
- Treat only a visible ATS confirmation or a confirmed Sent email as submission evidence.

## What is relaxed for speed

- One resume slot is chosen once, up front, for the whole pulse (1 of the user's App resumes) instead of being deliberated per job. Only override it mid-pulse if a job is an obvious hard mismatch for that resume.
- When an ATS can parse an uploaded resume to autofill the form, upload first and let it autofill instead of typing every field by hand; only the remaining blanks are filled manually from Experience/basic_info.
- A needed Cover Letter is drafted and self-reviewed by the orchestrating Agent in one inline pass against the [cover-letter-quality.md](../jobmatchflow-apply/references/cover-letter-quality.md) checklist. A separate reviewer subagent is not dispatched, even when the host supports isolated subagents.
- Application notes stay to the essential facts (submitted time, channel, resume/Cover Letter filenames, confirmation evidence, and — for LinkedIn — the same official-URL/channel fields application-workflow.md requires); they do not need the full elaboration `$jobmatchflow-apply` uses for a deliberate batch.

The one checkpoint that is never relaxed: stop before the final Submit/Send action and get the user's review, unless direct-submit authorization for this task was already given. Everything upstream of that click can move fast; that click itself always waits for permission.

## Session completion

Reconcile every completed application immediately, same as `$jobmatchflow-apply`. Finish with a compact summary of submitted, blocked, failed, and skipped jobs, with the exact next action for anything blocked.
