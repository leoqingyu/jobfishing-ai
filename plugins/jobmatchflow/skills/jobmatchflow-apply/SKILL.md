---
name: jobmatchflow-apply
description: Run JobMatchFlow application sessions using its MCP data and the current host's visible Chrome integration. Use when the user asks to check setup, sync a selected webmail inbox, review Saved jobs, apply through an ATS or email, create application materials, or reconcile application outcomes. Do not use for unrelated career advice.
---

# JobMatchFlow Apply

Use JobMatchFlow as the source for jobs, candidate data, resumes, saved answers, and application tracking. Access JobMatchFlow data and files only through its MCP tools; never navigate, click, upload, download, or edit through the JobMatchFlow frontend. Use the user's visible Chrome profile only for Gmail or Outlook Web, employer sites, LinkedIn, and ATS interaction. Select the browser integration supplied by the current host:

- In Codex, use the external ChatGPT Chrome integration. Never substitute the temporary in-app browser.
- In Claude Code, use Claude in Chrome. If it is not connected, ask the user to run `/chrome` and complete its permission flow.

Do not install, configure, or invoke the other host's browser integration.

Use only the bundled `jobmatchflow` MCP for JobMatchFlow data. Do not search for, install, generate, or repair an alternative JobMatchFlow client during an application session. If the bundled MCP is unavailable, follow the setup check and report the exact missing dependency.

## Route the request

- For installation or connection checks, read [setup-check.md](references/setup-check.md).
- For inbox synchronization, email verification, or direct email applications, read [email-workflow.md](references/email-workflow.md).
- For an application batch, read [application-workflow.md](references/application-workflow.md).
- Before any ATS or email attachment upload, read [outbound-filenames.md](references/outbound-filenames.md).

Tailored materials, outcome analysis, and interview preparation are separate explicit skills. Do not enter those workflows merely because they could improve an ordinary application. If the user explicitly requests a tailored CV or tailored materials as part of an application, route that job through `$jobmatchflow-tailor` first and resume `$jobmatchflow-apply` only after both verified tailored files have been uploaded and handed off.

Load only the reference needed for the current request. A full application session may require the email and application references in that order.

## Core invariants

- If JobMatchFlow is not authorized, call `start_device_authorization`, show the exact verification link and code, and call `finish_device_authorization` only after the user approves it.
- The device-authorization page is the only JobMatchFlow webpage involved, and the user—not the Agent—opens and confirms it. The Agent must not control that page or any other JobMatchFlow frontend page.
- At the beginning of every new application pulse, ask the user to confirm that Basic Info, Experience, and resume files in JobMatchFlow are current. After confirmation, call `refresh_application_cache` exactly once and use that snapshot throughout the pulse.
- If the user says JobMatchFlow data changed during the pulse, call `refresh_application_cache` again before continuing. Do not otherwise refresh repeatedly.
- Read `list_tracking` before new submissions to avoid duplicates.
- Prefer jobs whose `is_preparing` value is true.
- Job data goes beyond the description. Use `contact` (name, email, phone the JD names; a field is absent when the JD does not give it) for the salutation and for email applications before searching the JD text. Check `visa_sponsorship_offered` and `work_permit_required` against `get_experience_context().work_authorization_status` and stop to ask the user when a job requires a permit they do not hold. `job_url_direct` is the employer's own posting when the App has it, `company_info` gives industry, size and website for the cover letter, and `salary` may be an estimate (`is_estimated`). Never present an estimate to an employer as a fact.
- Use `get_experience_context().basic_info` for form identity and contact fields. A downloaded resume is an upload asset, not the authority for those fields.
- If a resume conflicts with `basic_info`, warn the user to update the resume and state that the form uses `basic_info`.
- App storage and download basenames may be opaque. Before an ATS or email attachment upload, create a clean local outbound copy according to [outbound-filenames.md](references/outbound-filenames.md). Never expose an App prefix, numeric ID, hash, UUID, timestamp, or storage key to the employer. Record the original App slot with `mark_applied` after a successful submission.
- In the standard route, the selected existing resume is read-only: download/cache it through MCP for the application, but never call `upload_tailored_resume`, create another App resume, or upload that resume back to JobMatchFlow. `mark_applied` must retain its original App resume slot.
- Treat the Cover Letter as part of every normal application, not as an optional tailored-material feature. Read [cover-letter-quality.md](references/cover-letter-quality.md) whenever generating one. Standard DOCX and tailored LaTeX Cover Letters use the same drafter-reviewer content standard. A standard Cover Letter is rendered and verified locally as DOCX, uploaded through `upload_tailored_cover_letter`, and submitted from that same local file; never use the JobMatchFlow frontend or its renderer/download flow to obtain it.
- `mark_applied` is the only post-submission transition for a platform job and the App owns its idempotency and automatic application snapshot. Do not build or maintain a second Agent-side submission state.
- `mark_applied` keeps its existing resume choice: one of the App resume slots or `tailored`. The App automatically snapshots the current CV, latest MCP-uploaded Cover Letter, JD, score, and notes. Use `tailored` only after the separate tailored-material workflow has saved both verified PDFs to the job.
- Use only two durable Agent-written stores. Save reusable answer knowledge with `save_agent_answer` in the Experience answer library. Save job-specific facts—including the exact answers actually submitted, submission evidence, email timeline, status changes, recruiter feedback, and interview lessons—in that application's append-only notes.
- Use the current host's visible Chrome integration for Gmail, Outlook Web, ATS registration, verification links, form filling, and file upload.
- Treat a successful ATS confirmation page or sent email as submission evidence. Do not mark an application applied before that evidence exists.
- Before marking or advancing a status, read current tracking. Treat an existing application, the same status, or a clearly later stage as a successful no-op instead of reporting an error.
- After a confirmed submission and successful reconciliation, append one deduplicated submission record to the application's notes. Never write a submission record before visible ATS confirmation or Sent-mail evidence.
- For every LinkedIn Easy Apply candidate, prefer the employer's original careers posting. Save the exact official job URL in the application notes whenever it exists. An active official application interface replaces Easy Apply; when no official application interface exists, send a verified email application first and then complete Easy Apply. Read the detailed routing rules before acting.
- Ask for user help when Chrome requires sign-in, CAPTCHA, MFA, a legal attestation, or a fact that cannot be responsibly inferred from available data.
- Direct-submit authorization comes only from the user's instruction in the current task. Do not look for an App-side auto-confirm feature flag.
- Do not place ATS passwords in JobMatchFlow notes or other plaintext tracking fields.

## Session completion

Reconcile every completed application immediately. Finish with a compact summary of submitted, failed, blocked, and follow-up-required jobs. Include the exact next action for each blocked item.
