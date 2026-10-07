# Setup check

Run this check without submitting applications or sending email.

1. Confirm that the `jobfishing` MCP tools are available.
2. If authorization is missing, call `start_device_authorization`, show the verification link and code to the user, and finish only after the user approves it.
3. Ask the user to confirm that Basic Info, Experience, and resume files in jobfishing are current.
4. After confirmation, call `refresh_application_cache` once. Confirm that it returns local snapshot paths and one local file per available resume.
5. Confirm each cached resume is readable and has enough logical metadata to prepare a clean employer-facing copy. The internal cache basename may contain a storage prefix; that alone is not a failure.
6. Select the current host's visible Chrome integration:
   - Codex: external ChatGPT Chrome integration; do not use the temporary in-app browser.
   - Claude Code: Claude in Chrome; check `/chrome` when connection status is unclear.
7. Open the configured webmail site based on the candidate email domain:
   - Gmail or Google Workspace: `https://mail.google.com/`
   - Outlook/Hotmail/Live/Microsoft 365: `https://outlook.live.com/mail/` or the user's organization URL.
8. Confirm that the inbox is visibly signed in. Do not inspect unrelated browser history or profiles.
9. Do not upload a file, send email, or submit an application during the setup check.
10. Report a checklist with one status per dependency and an exact fix for every failure.

Expected report:

```text
jobfishing connection: ready
jobfishing authorization: ready
Candidate profile: ready
Saved jobs: ready (N)
Resume library: ready (N)
Outbound filename preparation: ready
Pulse cache: ready
Visible Chrome integration: ready (Codex or Claude Code)
Job-search inbox: ready (Gmail or Outlook)
File download: ready
```

If Chrome is not connected, give the fix for the current host only. In Codex, direct the user to install or enable the ChatGPT Chrome plugin and finish its browser permission flow. In Claude Code, direct the user to install Claude in Chrome, launch with `claude --chrome` or run `/chrome`, and finish its browser permission flow. If the mailbox is signed out, ask the user to sign in in the visible job-search Chrome profile, then continue the same check. Do not open the jobfishing frontend during setup; App authorization and data checks use the device flow and MCP.
