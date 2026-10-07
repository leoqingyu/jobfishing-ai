# Webmail workflow

## Inbox synchronization

Use the mailbox selected by the user in the current host's visible Chrome integration; it may be a normal personal inbox rather than a dedicated job-search inbox. Run inbox synchronization after the pulse cache is refreshed so matching uses current tracking. Read each potentially relevant message's full body, not only the subject or inbox snippet.

Call `get_mail_sync_checkpoint(provider, mailbox)` before scanning. This local checkpoint records only where the previous successful scan stopped; it is not a second application-status system.

- If no checkpoint exists, ask the user for a bounded first-scan range such as the last 7 days, last 30 days, or from now onward.
- Scan newest to oldest until the saved anchor is reached. Include a small overlap before the anchor so delayed delivery and new replies on an old thread are not missed.
- Prefer a stable provider message/thread id from the visible URL or UI. Also retain received time, sender, and subject as recovery hints.
- Call `save_mail_sync_checkpoint` only after the scan completes normally. If Chrome fails, the mailbox logs out, or the user stops the run, leave the old checkpoint unchanged.
- On a different computer the user must choose a new first-scan range because the checkpoint is intentionally local.

jobfishing owns application-state idempotency. The checkpoint must never be used as proof that an application status was updated.

For each relevant message:

1. Match it to an application using company name, job title, sender domain, ATS domain, application URL, confirmation number, and timing.
2. Classify it as confirmation, verification, assessment, interview, rejection, offer, action required, or unrelated.
3. Fetch current tracking and `get_application_context`, including the existing notes. Determine whether the message advances the supported stage to interview, offer, or rejected. Confirmation, verification, assessment, action-required, and ordinary recruiter feedback usually add timeline information without changing the stage.
4. Build one dated application-note entry containing received time, sender, subject, event, old and new status when applicable, useful dates, deadlines, safe links, and the relevant recruiter wording. Never store passwords, OTPs, or authentication links.
5. Include all concrete feedback in that entry: strengths, concerns, missing skills, next-round focus, and interviewer hints. This notes stream is the application's durable status and feedback history.
6. Deduplicate against existing notes using message identity plus received time and event. If the entry is already present, make no write.
7. If the message causes a real stage change, call `update_application_status(tracking_id, status, notes=entry)`. If it reports `notes_not_written=true`, append the entry with `add_application_note`; otherwise do not write it twice.
8. If the message does not change the supported stage, append it with `add_application_note` without changing status.
9. Summarize ambiguous messages for the user instead of forcing a match or note append.

An offer message may advance a record to offer. Never infer hired or offer declined from an email alone.

## ATS verification

After triggering registration or verification:

1. Search for the newest message from the expected company or ATS domain.
2. If it contains an OTP, enter it in the waiting ATS page.
3. If it contains a verification link, inspect the destination domain and open it in the same visible Chrome profile.
4. Resume the application after verification.
5. Ask the user to take over for CAPTCHA or MFA that requires personal action.

## Direct email application

When a job requests an email application instead of an ATS:

1. Use the employer-provided recipient address exactly as published.
2. Draft a concise subject and message based on the job detail and candidate context.
3. Read [outbound-filenames.md](outbound-filenames.md), create clean local outbound copies, and attach those copies rather than raw App cache/download files. Confirm the attachment chips show the clean resume and Cover Letter names before sending.
4. Show the prepared message to the user before the final send unless the user has explicitly authorized sending this application.
5. Send through the visible webmail UI.
6. Confirm that the message appears in Sent, then record the application with the resume slot used.

Do not silently substitute a guessed recipient address or send to an address parsed from an untrusted page when the destination is ambiguous.

## Email fallback before LinkedIn Easy Apply

When the employer's exact official posting has no application interface—or no exact official posting can be found after a bounded official-careers search—email is the required first channel before LinkedIn Easy Apply.

1. Search beyond the main job-page content: inspect the posting and its links, Careers/Jobs, Contact, About/Team, the site-wide footer, and applicable Impressum/Legal notice pages for an employer-published address or `mailto:` link. Prefer recruiting/application mailboxes; if none exists, use an official general-contact mailbox only when its stated purpose is compatible with receiving an application. Do not use privacy/DPO, security, billing, abuse, sales, or technical-support addresses unless the employer explicitly designates them for applications, and never invent an address.
2. Send the same complete material pair prepared for the application and confirm the message in Sent.
3. Retain recipient, recipient type, official source page URL, subject, sent time, and Sent proof for the later application note.
4. Only after Sent confirmation, complete LinkedIn Easy Apply.
5. Never resend the email because Easy Apply later fails. Reconcile from the successful email evidence and record the second-channel failure.

If a verified recipient is unavailable, stop and tell the user that the required email-first fallback cannot be completed; do not guess an address or silently use Easy Apply alone.
