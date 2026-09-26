# Application workflow

## Prepare the batch

1. Ask the user to confirm that Basic Info, Experience, and all resume files in JobMatchFlow are current. This confirmation is required once per new application pulse, not once per job.
2. After confirmation, call `refresh_application_cache` exactly once. Use its cached profile, jobs, tracking, and resume files for the whole pulse.
3. Build the duplicate check from cached tracking and select requested jobs from cached jobs, prioritizing `is_preparing=true`. Job List ranking and Saved curation belong to the separate `$jobmatchflow-rank` workflow; do not re-rank the full Job List inside an application pulse.
4. Determine the material route for each selected job. An explicit request for a tailored CV/material pair requires `$jobmatchflow-tailor` to finish first. Otherwise use the standard route: one existing read-only App resume plus a locally generated DOCX Cover Letter. Never enter CV tailoring merely because it might improve the application; the Cover Letter remains job-specific in both routes.
5. For each selected job, call `get_job_detail` and inspect the full description and match details.
6. Choose a resume deliberately. Use the cached `local_path` belonging to the selected slot; its storage basename is not the employer-facing name.
7. Read [cover-letter-quality.md](cover-letter-quality.md) and run its complete evidence-plan, drafter, reviewer, and revision workflow. For the standard route, render those final paragraphs locally into a clean DOCX and verify its visible and extracted text. Do not call `save_cover_letter_content` or rely on the App DOCX renderer.
8. Establish a complete material pair before opening the ATS:
   - standard: the selected cached existing App resume plus the locally rendered and verified DOCX Cover Letter;
   - tailored: the verified `materials-manifest.json` produced by `$jobmatchflow-tailor`, containing both local PDF paths and confirming the job's current tailored CV and Cover Letter records.
9. For the standard route, upload only the local DOCX Cover Letter with `upload_tailored_cover_letter` so it is the job's current Cover Letter before submission and later snapshot creation. Never call `upload_tailored_resume` or upload the selected existing resume back to the App.
10. Read [outbound-filenames.md](outbound-filenames.md). Create clean local outbound copies of both files and verify their content before entering the browser workflow. Prefer the same verified local Cover Letter file that was just uploaded; do not download it again. App filenames may remain unchanged.

If the user updates JobMatchFlow during the pulse, refresh the application cache once more before continuing. Otherwise do not repeatedly fetch profile or resume files.

If a match detail shows a missing or conflicting requirement, surface it before submission. The user may still choose to continue.

## Apply in visible Chrome

Process jobs sequentially unless the user explicitly requests parallel work.

### LinkedIn Easy Apply routing

When the selected source offers LinkedIn Easy Apply, do not start with the Easy Apply form.

1. Locate the original employer-hosted posting by exact company, title, and location on the employer's official careers domain. Verify that it is the same role; a company landing page or search-results page is not the original job URL.
2. Preserve the exact official posting URL. If an exact page cannot be found after a bounded official-careers search, retain the explicit marker `official job URL not found` and the search date; never substitute the LinkedIn URL as if it were the official URL.
3. If the official posting has an active application form or links to the employer's ATS for this exact job, apply through that official interface. Do not also submit Easy Apply or email a duplicate application.
4. If the official posting exists but has no application interface, or the exact official posting cannot be found, locate a verified employer-published email. Do not stop after searching only the main page content: inspect the exact posting and its links, Careers/Jobs, Contact, About/Team, the site-wide footer, and applicable Impressum/Legal notice pages, including visible `mailto:` links. Prefer a recruiting/application address; if none is published, an official general-contact address such as `info@`, `hello@`, or `office@` may be used when its published purpose is compatible with receiving an application. Never guess an address, and never use a purpose-restricted privacy/DPO, security, billing, abuse, sales, or technical-support mailbox unless the employer explicitly says it accepts applications. Send the complete email application first, confirm it in Sent, and then complete LinkedIn Easy Apply.
5. If no verified recipient can be found, pause before Easy Apply and report the missing email channel. The required fallback order is email first, Easy Apply second; do not silently perform Easy Apply alone.
6. If the email succeeds but Easy Apply is blocked or fails, the email is still valid submission evidence. Reconcile the application once, record the Easy Apply failure and next action, and do not resend the email.

After the successful channel sequence, the application note must include:

- `official_job_url`: the exact employer/ATS URL, or `not found after official-careers search` with date;
- whether an official application interface existed;
- the LinkedIn listing URL;
- every channel attempted in order, including the email recipient, recipient type (recruiting or general contact), official source page URL, and Sent proof when used, plus Easy Apply confirmation or failure;
- the ordinary material, answer, declaration, timestamp, and confirmation details required below.

The App may label this field Interview Notes; it is the same append-only application notes stream used for submission evidence and later interview preparation.

1. Open only the employer, LinkedIn, or ATS application URL in the current host's visible Chrome integration. Never open or operate the JobMatchFlow frontend; all App reads, writes, uploads, and downloads use MCP.
2. Reuse an existing ATS account in the dedicated Chrome profile when available.
3. Register when required and complete email verification through the webmail workflow.
4. Fill identity and contact fields from `basic_info`.
5. Generate narrative answers from candidate context. Save reusable answer knowledge with `save_agent_answer`, and separately retain the exact final wording actually entered for the later application note. The reusable library can change over time and is not proof of what this employer received.
6. Upload the clean outbound resume and Cover Letter copies when the ATS requests attachments; use the same final reviewed Cover Letter paragraphs when it provides a text field. Do not decode Base64 in Chrome. Verify the attachment names displayed by the ATS; if either exposes an App storage prefix, remove it and upload the clean copy again before submission.
7. Review required fields, consent checkboxes, attachments, and recipient/job identity.
8. Keep optional marketing, talent pool, notification, and extended-storage choices off unless the user has stated another preference.
9. Obtain the user's final review or use direct-submit authorization explicitly given in the current task. There is no App-side auto-confirm flag.
10. Submit once. Capture the visible confirmation result.
11. Read current tracking, then call the existing `mark_applied(job_id, resume_choice)` immediately after success only if the application is not already recorded. For a standard application, use its original App resume slot and never upload the resume. For tailored materials, use `tailored`. The App snapshots the current MCP-uploaded Cover Letter automatically. If the App already contains the application, accept the no-op result and continue reconciliation.
12. Resolve the resulting `tracking_id`, read `get_application_context`, and inspect its current notes. If this submission event is not already present, call `add_application_note` once with a dated record containing:
    - submitted time, channel, ATS or recipient, application URL, original official job URL when applicable, and visible confirmation text/number;
    - resume choice and exact employer-facing filename, plus the exact employer-facing Cover Letter filename or text-field use;
    - the full final wording of every narrative answer actually submitted, not only a summary;
    - required declarations or consent choices actually selected, plus any follow-up action or deadline.

Do not put passwords, OTPs, session links, or authentication tokens in the note. If reconciliation finds an older existing application and no new browser submission occurred in this task, do not create a new submission note.

For jobs found outside JobMatchFlow, use `create_manual_tracking` after success, then append the same submission record to its returned tracking id.

## Failure handling

- Authentication, CAPTCHA, or MFA: pause and ask the user to take over the visible page.
- Missing fact or legal attestation: ask one concise question and preserve the page.
- Browser tab failure: reopen the URL in the same visible Chrome profile and use the tracking record to avoid duplicate submission.
- Unclear success: do not retry Submit immediately. Check the confirmation page, Sent mailbox, or confirmation email first.
- Hard mismatch: explain the mismatch and let the user decide whether to continue.

## Batch summary

Report each job as submitted, blocked, failed, or skipped. Include company, role, resume choice, and the next required action.
