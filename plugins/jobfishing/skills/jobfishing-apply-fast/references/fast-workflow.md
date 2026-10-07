# Fast workflow

## Start the pulse

1. Confirm Basic Info, Experience, and resume files in jobfishing are current — once for this pulse, not per job.
2. Call `refresh_application_cache` exactly once and use that snapshot for the whole pulse.
3. Ask the user once which of the App's existing resumes (1-4) to use for this pulse. Use its cached `local_path`; its storage basename is not the employer-facing name. Do not re-ask per job unless a job is an obvious hard mismatch for that resume — then confirm the exception with the user before switching.
4. Read `list_tracking` and select the requested jobs from cached jobs, skipping anything already recorded.

If the user asked for tailored materials on a specific job, hand that job to `$jobfishing-tailor` first and only bring it back here once both tailored files are verified and uploaded; use `resume_choice="tailored"` for that job instead of the pulse resume.

## Per job

Process jobs sequentially unless the user explicitly asks for parallel work.

1. Call `get_job_detail` and skim the description and match details. Surface a missing or conflicting requirement before proceeding; the user may still choose to continue.
2. Open two tabs at once in the visible Chrome integration: the job's ATS/employer application page, and the job-search webmail inbox. Having both open avoids a second round trip when a verification email or an email-application channel turns out to be needed.
3. Identify the ATS pattern for this job:
   - **Resume-parse autofill ATS** (Greenhouse, Lever, Workday, and most others that offer an "upload your resume" step before the full form): read [outbound-filenames.md](../../jobfishing-apply/references/outbound-filenames.md), prepare the clean outbound resume copy, and upload it *first* — before typing anything — so the ATS parses and autofills the form. Then fill whatever it left blank from `get_experience_context()` (basic_info + experience + saved answers), not by re-deriving facts from the resume text yourself. After autofill runs, check every identity/contact field (name, email, phone, address) against `basic_info` and overwrite any that differ — the parsed resume is never the authority for those fields, autofill or not.
   - **LinkedIn Easy Apply**: do not start with the Easy Apply form. Follow the "LinkedIn Easy Apply routing" section of [application-workflow.md](../../jobfishing-apply/references/application-workflow.md) exactly as written — official posting first, verified email before or alongside Easy Apply when no official application interface exists, pause and report if no verified email can be found. Nothing in that section is shortened here.
   - **Direct email application**: read [email-workflow.md](../../jobfishing-apply/references/email-workflow.md)'s direct-email section and use the employer-provided address exactly as published.
4. Check whether this application needs a Cover Letter — an ATS upload slot, a text field, or the email body itself. If it does:
   - Draft it inline from the job detail and candidate context in this same turn.
   - Self-review that draft in the same pass against the [cover-letter-quality.md](../../jobfishing-apply/references/cover-letter-quality.md) checklist (factual accuracy against cited sources, JD coverage, honest gap language, no duplicated evidence, tone/length, consistency with the chosen resume). Do not dispatch a separate reviewer subagent for this, even when the host supports isolated subagents — that dispatch is the one thing this fast path skips.
   - Render it locally to a verified DOCX and upload with `upload_tailored_cover_letter`; never through the jobfishing frontend or its renderer.
5. Prepare clean outbound filenames for every file still to be attached (per [outbound-filenames.md](../../jobfishing-apply/references/outbound-filenames.md)) and verify the ATS/webmail UI displays the clean name before submitting — remove and re-upload if it shows an App storage prefix instead.
6. Fill any remaining required fields, consent checkboxes, and narrative answers from candidate context. Save reusable answer knowledge with `save_agent_answer`, and keep the exact final wording actually entered for the application note.
7. Stop here. Show the user the completed application (or, if this task already carries explicit direct-submit authorization, proceed without asking again) before clicking the final Submit/Send action. This is the one mandatory checkpoint in this Skill; everything above it can move fast, this step never does.
8. Submit or send once. Capture the visible confirmation page or the Sent-mail evidence — that is the only thing that counts as submission evidence.
9. Read current tracking; if this submission is not already recorded, call `mark_applied(job_id, resume_choice)` with the pulse resume slot (or `tailored` when `$jobfishing-tailor` produced this job's materials). If it is already recorded, treat that as a successful no-op.
10. Call `add_application_note` once with the essential facts: submitted time, channel, ATS or recipient, resume and Cover Letter filenames used, visible confirmation text, and — for a LinkedIn candidate — the same `official_job_url`/channel fields the LinkedIn Easy Apply routing section requires. Deduplicate against existing notes first; do not write the same submission twice.

## Failure handling

Same as `$jobfishing-apply`: pause for the user on authentication, CAPTCHA, MFA, or a missing fact; reopen the same tracked URL on a browser-tab failure instead of resubmitting blind; check the confirmation page or Sent mailbox before retrying an unclear result; explain a hard mismatch and let the user decide.

## Batch summary

Report each job as submitted, blocked, failed, or skipped, with company, role, resume choice, and the next required action for anything not submitted.
