# jobfishing × Claude Code — Full User Workflow

> **How to use this guide.** It is the companion to the [README](../README.md), not a second install. The README's one-line install and "How to use it" cover finding, scoring, saving and recommending jobs, and the tools are ready as soon as the install finishes. **If that already works for you, do not repeat any setup here.** Open this guide only for what the README does not cover: connecting Claude Code to your own Chrome, running application sessions and reading your inbox, tailored CVs with LaTeX, and troubleshooting. The README has a table of exactly which section to open and when.

> **Command names.** This guide writes Claude Code commands in the plugin form, `/jobfishing:jobfishing-apply`. If you used the one-line install, leave out the `jobfishing:` part: it is `/jobfishing-apply`, the same skill.


This document guides users through the first-time connection of jobfishing, Claude Code, and Claude in Chrome, and describes how to use them afterward following the pattern of "open once, submit a batch, end the task."

jobfishing is the source of truth for candidate profile, resume, jobs, Q&A, and application status. Claude Code is responsible for reading this data, operating Gmail, Outlook Web, and job-board sites through the Chrome already logged in on the user's own machine, and writing the results back to jobfishing once applications are complete.

## 1. What to Prepare Before Starting

The user needs to prepare:

- A jobfishing account;
- Claude Code, logged in with a direct Anthropic account via `/login`;
- A Pro, Max, Team, or Enterprise plan that supports the Claude Code Chrome integration;
- Google Chrome;
- The Claude in Chrome extension;
- A job-search email account already logged into the same Chrome Profile;
- jobfishing installed with the [README's one-line install](../README.md#install). Nothing else to install: no Python, no download. (Only if that cannot run on your computer: the `jobfishing-distribution-0.5.1-complete-v7.zip` distribution package and section 3.)

Claude in Chrome requires a direct Anthropic login. Claude Code sessions that only use an API Key, Amazon Bedrock, Google Cloud, or Microsoft Foundry cannot use this Chrome integration.

Windows users should run native Claude Code; the Claude Code Chrome integration does not support WSL.

Official Claude Code documentation: <https://code.claude.com/docs/en/chrome>

## 2. Complete jobfishing Setup First

Before letting Claude Code start working, log in to jobfishing and complete:

1. Fill in Basic Info;
2. Fill in Experience;
3. Upload the resumes you plan to use;
4. Check the file name shown for each resume in the App;
5. Review your commonly used application Q&A;
6. Move the jobs you plan to apply to into `Saved`;
7. Decide whether to explicitly authorize Claude Code to submit directly this round; the App has no separate auto-confirm toggle.

Basic Info is the final source of truth for the name, address, phone, email, and other personal information on application forms. Users are responsible for the accuracy of what they enter.

If information in a resume is inconsistent with Basic Info, Claude Code should remind the user to update the resume, but the application form will still follow Basic Info.

### Optional: Have Claude Code Filter the Job List

Job filtering is a separate feature and will not automatically start submitting applications. For first-time use, send:

> /jobfishing:jobfishing-rank First read my existing filtering preferences from Experience; if the information is insufficient, ask me multiple rounds of questions to understand my target direction, hard requirements, work preferences, and trade-off rules. Save the final confirmed preferences to Experience Agent Q&A, then review the Job List and add jobs that match my preferences to Saved. Do not start submitting applications.

Claude Code will save the confirmed long-term preferences as `job_ranking_preferences_v1` in Experience Agent Q&A. This entry can be edited from the App front end.

Every time this Skill is invoked afterward, Claude Code will first show a summary of the existing preferences and ask whether they need to be updated. Only after the user confirms the preferences will it read the full JD, App scores, match details, and hard thresholds to filter jobs. Jobs that are not selected are left as-is by default and are not automatically removed.

If you only want to view the ranking without modifying Saved, explicitly send:

> /jobfishing:jobfishing-rank Only review and show the recommended results; do not modify the Job List.

## 3. Manual Installation (Only If the One-Line Install Cannot Be Used)

**Skip this whole section if the README one-line install worked.** You can check in a few seconds: ask Claude Code to "list your jobfishing skills", or run `claude mcp list` and look for `jobfishing` showing as connected. Use the steps below only on a computer where the one-line install cannot run (a locked-down or corporate machine, no way to run PowerShell or shell scripts from the internet), or if you prefer to install it as a plugin.

This section only needs to be done once.

### 1. Unzip the Distribution Package

Unzip the package to a fixed location, for example:

- Windows: `%USERPROFILE%\Documents\JobfishingAgent`
- macOS: `$HOME/Documents/JobfishingAgent`
- Linux: `$HOME/JobfishingAgent`

Do not delete or move this folder after installation is complete.

Do not use the plugin directory as your day-to-day application-submission Project. The plugin directory is only for storing and installing the runtime program.

### 2. Install uv (the only thing to install)

The plugin starts itself with [uv](https://docs.astral.sh/uv/), which downloads the right Python and every dependency on first use. You do not install Python and you run no `pip`.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

macOS / Linux Terminal:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

Open a new terminal afterwards. As long as `uv --version` prints a version, you are ready. The first start of jobfishing takes about 10 seconds; after that it is instant. If you skip this step, the `jobfishing-setup` skill will offer to do it for you.

### 3. Install the Claude Code Plugin

Start Claude Code:

```bash
claude
```

In Claude Code, run:

```text
/plugin marketplace add <absolute path to the unzipped directory>
/plugin install jobfishing@jobfishing
```

If the installation result indicates a reload is needed, run:

```text
/reload-plugins
```

Use the following command to check:

```text
/plugin
```

Confirm:

- `jobfishing` appears under Installed;
- The plugin is in an enabled state;
- There are no jobfishing errors under Errors;
- The component list includes a Skill and an MCP server.

Official Claude Code plugin installation instructions: <https://code.claude.com/docs/en/discover-plugins>

## 4. Set Up Claude in Chrome

### 1. Install and Log In

Install the Claude in Chrome extension in Chrome, and make sure it uses the same Claude account as Claude Code's `/login`.

Your job-search email, LinkedIn, job boards, and ATS should all be logged in within this Chrome Profile.

Do not use the ChatGPT Chrome extension in place of Claude in Chrome.

### 2. Check the Connection

Start Claude Code with:

```bash
claude --chrome
```

Or run, in an already-open Claude Code session:

```text
/chrome
```

The correct status should display:

```text
Status: Enabled
Extension: Installed
```

You can select "Enabled by default" within `/chrome` so you don't need to add `--chrome` every time afterward.

### 3. Site Permissions

Claude may request authorization the first time it operates on a new site. It's recommended to authorize per-site for the current session or for trusted sites, rather than permanently opening access to all sites for convenience.

Claude in Chrome supports operating on sites you're already logged into, filling out forms, and uploading local files. When it encounters a login page or a CAPTCHA, Claude Code should pause and let the user handle it personally.

## 5. Create a Day-to-Day Application-Submission Project

Create a new, dedicated empty folder, for example:

```text
Documents\Job Applications
```

Do not choose the plugin's unzipped directory, and there's no need to manually copy resumes into it.

Open a terminal and navigate into that directory:

Windows:

```powershell
cd "$HOME\Documents\Job Applications"
claude --chrome
```

macOS:

```bash
cd "$HOME/Documents/Job Applications"
claude --chrome
```

Linux:

```bash
cd "$HOME/Job Applications"
claude --chrome
```

This directory is now Claude Code's current application-submission Project.

## 6. First Configuration Check

In the Project, send:

> /jobfishing:jobfishing-apply Run a full configuration check. Do not send any emails, upload files, or submit applications for now.

Claude Code should execute, in order:

1. Check whether the jobfishing MCP tools are available;
2. If not yet authorized, generate a jobfishing verification link and verification code;
3. Ask the user to open the link, log in to jobfishing, and approve the authorization;
4. Complete the long-term authorization;
5. Ask the user to confirm that Basic Info, Experience, and resumes have already been updated;
6. Once the user confirms, refresh the local cache once for this round;
7. Download all available resumes to a local temporary directory;
8. Check whether the downloaded resume file names exactly match the names shown in the App;
9. Check Chrome via the browser tool corresponding to `/chrome`;
10. Check whether the job-search inbox is already logged in;
11. Output the configuration check results without submitting any applications.

The expected result looks similar to:

```text
jobfishing connection: ready
jobfishing authorization: ready
Candidate profile: ready
Saved jobs: ready (N)
Resume library: ready (N)
Outbound material filenames: ready
Pulse cache: ready
Visible Chrome integration: ready (Claude Code)
Job-search inbox: ready
File download: ready
```

If Claude Code recognizes `/jobfishing:jobfishing-apply` and starts the process above, it means the plugin, Skill, and MCP have all loaded successfully.

## 7. Optional: One-Time Setup of a Shared LaTeX Environment

LaTeX is only needed when the user explicitly requests generation of a tailored CV or a tailored Cover Letter. Standard applications and the DOCX Cover Letter do not require LaTeX to be installed.

The LaTeX environment is a "system-user-level configuration for the current computer" — it does not belong to any single Claude Code Project or any single conversation. jobfishing always uses the following locations:

| System | Shared State File | Shared Template Directory | Default LaTeX Install Root |
| --- | --- | --- | --- |
| Windows | `%USERPROFILE%\.jobfishing\materials\environment.json` | `%USERPROFILE%\.jobfishing\materials\templates` | `%LOCALAPPDATA%\Programs\MiKTeX` |
| macOS | `$HOME/.jobfishing/materials/environment.json` | `$HOME/.jobfishing/materials/templates` | `$HOME/Library/TinyTeX` |
| Linux | `$HOME/.jobfishing/materials/environment.json` | `$HOME/.jobfishing/materials/templates` | `$HOME/.TinyTeX` |

The first time you need tailored materials, send this in Claude Code:

> /jobfishing:jobfishing-materials-setup Check and configure the shared LaTeX environment on this computer. Only check for now; if installation is needed, first tell me the install location, size, and command, and wait for my approval.

The Skill will first run an environment check. When the environment is already usable, it will simply reuse the existing one; only when the compiler is missing or the template validation fails will it propose an installation or repair plan. On success, it will write the absolute paths for `lualatex` and `xelatex` into the shared state file listed in the table above.

If the same system account has already been configured previously by Codex, Claude Code only needs to run the environment check once, and it will reuse the same state file, templates, and compiler — there's no need to read Codex's conversation history or reinstall anything.

If the user has already installed LaTeX on their own, the compiler paths can be registered explicitly. Windows PowerShell example:

```powershell
uv run --no-project "$env:USERPROFILE\.claude\skills\jobfishing-materials-setup\scripts\materials_doctor.py" --smoke --write-state --lualatex "D:\TeX\bin\lualatex.exe" --xelatex "D:\TeX\bin\xelatex.exe"
```

macOS example:

```bash
uv run --no-project "$HOME/.claude/skills/jobfishing-materials-setup/scripts/materials_doctor.py" --smoke --write-state --lualatex "/custom/tex/bin/lualatex" --xelatex "/custom/tex/bin/xelatex"
```

Linux example:

```bash
uv run --no-project "$HOME/.claude/skills/jobfishing-materials-setup/scripts/materials_doctor.py" --smoke --write-state --lualatex "/custom/tex/bin/lualatex" --xelatex "/custom/tex/bin/xelatex"
```

These paths are where the one-line install puts the skills. If you installed manually from the unzipped folder, the script is in `plugins/jobfishing/skills/jobfishing-materials-setup/scripts/` inside that folder instead. Run it with `uv run --no-project` either way, so no separate Python is needed.

Do not put `environment.json` inside a Project, the plugin directory, or the Claude Code cache directory. Each different computer and each different system account needs its own separate configuration; WSL and a native Windows environment are also treated as two separate environments. Windows users should continue to use native Claude Code to connect to Chrome.

### Choosing a Materials Path Before Each Job

jobfishing has two materials paths. The user needs to tell Claude Code explicitly whether this particular job requires a tailored resume.

#### Path A: No Tailored Resume Needed

Simply call `/jobfishing:jobfishing-apply`. Claude Code selects the most suitable resume from those already in the App, while also generating a standard DOCX Cover Letter locally through the full quality process, saving it via MCP, and then using that same local file to submit the application. Do not call `jobfishing-tailor`, and LaTeX is not required.

Prompt:

> /jobfishing:jobfishing-apply This job does not need a tailored resume — please choose the most suitable resume from the App's existing resumes; do not re-upload a resume. Generate a DOCX Cover Letter locally following the standard quality process, save it via MCP, and use that same file to fill out the application. Do not operate the jobfishing front end; stop before the final submit button.

#### Path B: Tailored Resume Needed

First call `/jobfishing:jobfishing-tailor`. This Skill generates and validates two LaTeX PDFs at the same time: a tailored CV and a tailored Cover Letter. It will not generate only the CV, nor will it submit the application directly.

First-step prompt:

> /jobfishing:jobfishing-tailor Generate a tailored CV and a tailored Cover Letter for "Company Name + Job Title" in jobfishing. Base it on the most suitable existing resume in the App, complete fact-checking, review, LaTeX rendering, and PDF validation, and upload the results back to jobfishing. Do not submit the application after the materials are done.

Once both materials have been uploaded successfully, call `/jobfishing:jobfishing-apply`:

> /jobfishing:jobfishing-apply Continue with "Company Name + Job Title" for which the tailored materials were just completed. Use the uploaded tailored CV and tailored Cover Letter to fill out the application, and stop before the final submit button.

If the user wants to complete both steps in one continuous task, they can also state it in a single message:

> First use /jobfishing:jobfishing-tailor to generate and upload two tailored materials for "Company Name + Job Title"; once validation is complete, use /jobfishing:jobfishing-apply to continue filling out the application, and stop before the final submit button.

`jobfishing-tailor` will first check the shared LaTeX environment. When the environment is already usable, it reuses it directly; only when the check fails does it move on to `/jobfishing:jobfishing-materials-setup` — there's no need to manually reconfigure it for every job.

### Optional: A Faster Path for a Quick Pass

`/jobfishing:jobfishing-apply-fast` is a leaner sibling of `jobfishing-apply` for when the user just wants to get through one job, or a handful, quickly — it is not a replacement for the standard entry point. It picks one resume for the whole pass instead of re-deliberating per job, uploads that resume first on any ATS that can parse and autofill from it, drafts and self-reviews the Cover Letter inline instead of dispatching a separate reviewer, and still stops before the final submit button unless direct submission is already on. LinkedIn Easy Apply routing (official posting first, verified email before or alongside Easy Apply) is not shortened in this path.

> /jobfishing:jobfishing-apply-fast Use my resume #2 for this pass. Process these three Saved jobs; stop before the final submit button on each.

## 8. First Trial Submission

For the first time, it's recommended to process only a single job and stop before the final submission.

First, place a test job into `Saved` in jobfishing, then send:

> /jobfishing:jobfishing-apply First sync the job-search inbox, then process one job from Saved. This test does not need a tailored resume: use the most suitable existing resume in the App and generate a standard DOCX Cover Letter; stop before the final submit button — do not submit.

Claude Code should:

1. Read the job-search inbox from where it left off last time;
2. Summarize new recruiting emails and update jobfishing;
3. Check whether the job has already been applied to;
4. Read Basic Info, Experience, and application Q&A from this round's cache;
5. Select the appropriate resume slot;
6. Fill out the ATS using the original-named resume from the local temporary directory;
7. Generate any application Q&A that's needed;
8. Generate and check a DOCX Cover Letter locally following the standard quality process, upload it to jobfishing via MCP, and keep that same local file;
9. Upload the local resume and this local DOCX directly to the ATS; the standard workflow must not re-upload the resume back to jobfishing, nor download the Cover Letter through the jobfishing front end;
10. Stop before the final submit button so the user can review it.

After confirming everything looks correct, send:

> Go ahead and submit, and update jobfishing once you've confirmed success.

Claude Code must see a success confirmation page or a sent email before it can mark the job as submitted.

## 9. Turning On Direct Submission

After the first trial submission succeeds, you can send:

> /jobfishing:jobfishing-apply First sync the job-search inbox for everything after the last cutoff point, then process all Saved jobs for this round. Direct submission is enabled; stop and ask me when you hit a CAPTCHA, MFA, a legal disclaimer, conflicting data, or a fact you can't determine.

Even with direct submission enabled, Claude Code should still pause in the following situations:

- CAPTCHA;
- Email or SMS verification codes;
- MFA;
- ATS registration confirmation links;
- Legal disclaimers or e-signatures;
- Facts that cannot be reliably determined from Basic Info and Experience;
- A job site requiring the user to log in again;
- Salary, visa, or relocation questions that need the user's confirmation.

## 10. Every Subsequent Submission Round

The user does not need to reinstall the plugin or re-copy resumes.

Each time, you only need to:

1. Update your profile, resumes, and Saved jobs in jobfishing;
2. Go into the same Job Applications directory;
3. Run `claude --chrome`;
4. Start a new task or clean up into a fresh round;
5. Confirm that profile and resume data are up to date;
6. Have Claude Code sync the inbox and submit a batch of applications;
7. Review the round's summary and end the session.

A commonly used prompt:

> /jobfishing:jobfishing-apply My jobfishing profile and resumes have been updated. First sync the job-search inbox, then process all Saved jobs for this round. Direct submission is enabled; stop and ask me whenever something needs my personal confirmation or action.

The batch prompt above uses, by default, the App's existing resumes and a standard DOCX Cover Letter. If a particular job needs a tailored resume, run `/jobfishing:jobfishing-tailor` separately for that job first, and only hand it to `/jobfishing:jobfishing-apply` once both tailored materials are complete.

## 11. This Round's Cache Rules

At the start of each round, Claude Code refreshes jobfishing exactly once, and caches:

- Basic Info;
- Experience;
- Application Q&A;
- The job list;
- Application records;
- Resume files.

The same round of submissions reuses this cache, without re-downloading resumes for every job.

If the user modifies jobfishing partway through, they must explicitly tell Claude Code:

> I just updated jobfishing — please refresh this round's cache and continue.

The temporary cache is cleared once the task ends. It gets reconfirmed and refreshed again next round.

## 12. Resume and Cover Letter Rules

- Personal information on the form always follows Basic Info;
- A resume is an uploaded file, not the final source of truth for personal information on the form;
- jobfishing's internal upload name, storage name, and download cache name may carry internal prefixes — the App is not required to be renamed for this;
- Before actually uploading to the ATS or attaching to an email, the Agent must create a clean submission copy in this round's local directory — numbers, hashes, UUIDs, timestamps, database keys, or storage prefixes must never be exposed to the employer;
- For a standard resume, restore the user-visible original name where possible; when no reliable name is available, use "Name - CV.extension". A tailored resume uses "Name - CV - Company.extension", and the Cover Letter uses "Name - Cover Letter - Company.extension";
- The Agent does not modify the App's internal files — it only copies them to a clean file name; after the ATS or email shows the attachment, double-check it again. If a dirty file name is still shown, delete the attachment and re-upload a clean copy before submitting;
- The current version supports explicitly invoked tailored CVs and Cover Letters; a standard application does not automatically enter the tailoring flow;
- When not tailoring a resume, only call `/jobfishing:jobfishing-apply`: the existing App resume stays read-only, the standard Cover Letter is generated locally as a DOCX, uploaded via MCP, and that same local file is used directly for the application;
- When tailoring a resume, first call `/jobfishing:jobfishing-tailor`: a tailored CV PDF plus a tailored Cover Letter PDF; only call `/jobfishing:jobfishing-apply` after the upload and validation are complete;
- `/jobfishing:jobfishing-tailor` is not responsible for submitting the application; `/jobfishing:jobfishing-materials-setup` is used only when the LaTeX environment check fails;
- The standard workflow never re-uploads a resume; only the tailoring workflow may upload the tailored resume and use `resume_choice="tailored"`;
- Any Cover Letter generated by the Agent must be rendered and validated locally before being uploaded back to jobfishing via MCP; it must not be re-downloaded while the local file still exists;
- The Agent must not operate the jobfishing front end through the browser, including reading data, modifying fields, or uploading/downloading files; all App business operations go strictly through MCP. The device authorization page is opened and confirmed by the user personally;
- `resume_choice` only records which resume slot was used; it does not re-upload the resume file;
- Reusable Q&A can be saved back to jobfishing, and the user can edit it from the front end.

## 13. Email Workflow

Claude Code uses the web-based email accounts already logged into the current Chrome Profile:

- Gmail or Google Workspace: <https://mail.google.com/>
- Outlook, Hotmail, Live, or Microsoft 365: <https://outlook.live.com/mail/>

Email is used to read company replies, verification codes, ATS confirmation links, and interview invitations, and also for direct email applications and for updating jobfishing based on replies.

Each round continues from where it left off last time, without reprocessing the entire email history.

### Fixed Order for LinkedIn Easy Apply

When encountering an Easy Apply job, Claude Code must first look for the original job posting on the company's own website for the same company, role, and location.

1. If the original posting exists on the company website and has a valid application interface: apply directly through the company site or the ATS linked from it, without also doing an email application or Easy Apply.
2. If the company job page exists but has no application interface: first look for the company's officially published recruiting email address, and only after the email application succeeds, also complete the Easy Apply.
3. If no original job posting can be found on the company website: after a reasonably thorough search of the search results, first submit via the company's officially published recruiting email address, then complete the Easy Apply.
4. If no trustworthy recruiting email address can be found: pause and report — never guess an email address, and never skip the email step and go straight to Easy Apply.

When searching for an email address, don't rely only on the main content of the job page or the company homepage. Claude Code must also check Careers/Jobs, Contact, About/Team, the site-wide footer, the Impressum/Legal notice, and any `mailto:` links on the page. Prefer a recruiting email address; when no HR/recruiting email exists, a general contact address officially published by the company and compatible in purpose — such as `info@`, `hello@`, or `office@` — may be used. Applications must not be sent to privacy/DPO, security, billing, abuse, sales, or dedicated technical-support email addresses, unless the company explicitly states that address accepts applications.

Once the application is submitted, the App's Interview Notes/Application Notes must be appended with:

- The original job posting link on the company website; if it truly cannot be found, record "original company job posting link not found" along with the search date;
- The LinkedIn job link;
- Whether the company website has an application interface;
- The channel(s) actually used and the order in which they were used;
- The email recipient, the type of email address (recruiting or general contact), the official source page where the address was found, the send time, and evidence that it was sent;
- The success confirmation or failure reason for Easy Apply.

If the email application succeeds but Easy Apply fails, do not resend the email. The email already constitutes evidence of application and should be recorded as a normal Application, with the Easy Apply failure and next steps appended to the Notes.

## 14. End-of-Round Summary

At the end of each round, Claude Code should output:

```text
Submitted: jobs successfully submitted
Failed: jobs that failed this round and why
Blocked: jobs waiting on the user
Follow-up required: jobs needing a reply, interview, or additional materials
```

Every Blocked job should include a clear next step.

## 15. Frequently Asked Questions

### `/jobfishing-apply` (or `/jobfishing:jobfishing-apply`) Isn't Recognized

**If you used the one-line install:** the skills are copied to `~/.claude/skills` (Windows: `%USERPROFILE%\.claude\skills`). Check that `jobfishing-apply` is there, fully quit and reopen Claude Code (twice if it still does not show; the skills refresh themselves when the tools start), and type `/jobfishing-apply`, without the `jobfishing:` prefix. If the folder is empty, run the README install line again; it is safe to repeat.

**If you installed as a plugin:** run:

```text
/plugin
```

Check whether the plugin is Installed, Enabled, and whether there are any errors under Errors. After installing or updating, run `/reload-plugins`, and if necessary, quit and restart Claude Code.

### The jobfishing MCP Fails to Start

**If you used the one-line install:** run `claude mcp list`. `jobfishing` should show as connected; the first start after an update takes about ten seconds. If it does not, run the README install line again (it is safe to repeat), and if it still fails, run this and read the error:

```text
uvx --from "https://github.com/leoqingyu/jobfishing-ai/archive/refs/heads/main.zip#subdirectory=plugins/jobfishing" jobfishing-mcp
```

**If you installed manually:** check that `uv` works (`uv --version`) and re-install the plugin as in section 3.

You can also use `claude --debug` to view MCP initialization errors.

### Claude Code Can't Connect to Chrome

Run:

```text
/chrome
```

Confirm that the extension is installed, its status is Enabled, it's using the correct Chrome Profile, and that Claude Code is logged in via `/login` rather than using only an API Key.

### Chrome Can't Be Found in Windows WSL

Exit WSL and use native Windows Claude Code. The Chrome integration does not support WSL.

### The ATS or Email Attachment Shows Numbers, Hashes, UUIDs, or Other Internal Prefixes

It's not inherently a bug that the App's download cache name carries an internal prefix. Claude Code should keep the original file, create a clean submission copy in this round's local directory, and re-upload it. Only the final file name shown in the ATS or email attachment interface needs to be clean; do not submit or send until both attachment names have been double-checked as correct.

### The User Changes Their Address, Phone Number, or Resume Partway Through

Send:

> I just updated jobfishing — please refresh this round's cache, remove the outdated content from the current form, and refill it using the latest Basic Info before continuing.

### A Page Requires a Verification Code, CAPTCHA, or Legal Confirmation

The user handles it personally in the visible Chrome page, then tells Claude Code to continue once it's done.

### Codex Already Set Up LaTeX, but Claude Code Still Says It Can't Find It

Confirm both Agents are using the same system account, and check whether the shared state file exists. Have Claude Code run the `jobfishing-materials-setup` environment check once; the checker reads the saved absolute compiler paths and does not depend on Claude Code's current `PATH`. If it's running on a different computer, a different system account, or in WSL, it needs to be configured separately in that environment.

### The User Wants to Install LaTeX Somewhere Else

That's fine. Use the `--lualatex` and `--xelatex` parameters from this section to register the two absolute paths and complete the smoke test. Once validated, both Codex and Claude Code will reuse these paths.

## 16. The Daily Routine the User Just Needs to Remember

```text
Update the App
→ Go into the Job Applications directory
→ Start claude --chrome
→ Confirm profile and resumes are up to date
→ Sync the inbox and submit a batch
→ Handle a few CAPTCHAs or manual confirmations
→ Review this round's summary
```

This is not a 24-hour monitoring task. Claude Code only works when the user actively opens the Project and kicks off a round of applications.

## 17. Quick Reference for All Skills

| Skill | When to Use | Main Actions | What Gets Saved |
| --- | --- | --- | --- |
| `/jobfishing:jobfishing-rank` | To filter the Job List or add suitable jobs to Saved | First time: multi-round questions about job-search preferences; afterward: confirm preferences first, then filter using App scores, the full JD, and match details | Confirmed preferences are saved to Experience Agent Q&A; Saved is modified when the user requests it |
| `/jobfishing:jobfishing-apply` | Configuration checks, syncing the inbox, filling out the ATS, applying via company site/email/Easy Apply | Selects existing or tailored materials, operates Chrome, updates the Application after submission | Cover Letter, application status, complete submission records, original company link, and email/recruiting feedback are written to the App |
| `/jobfishing:jobfishing-apply-fast` | A quick one-job or small-batch pass once setup is already done | Same as `apply`, but with one resume for the whole pass, ATS resume-parse autofill first, and an inline self-reviewed Cover Letter instead of a dispatched reviewer | Same write-back as `apply`; still stops before the final submit button |
| `/jobfishing:jobfishing-cover-letter-fast` | Just want a Cover Letter, not a full application | Drafts and self-reviews one job-specific Cover Letter inline, renders a verified local DOCX, uploads to jobfishing only on request | Nothing until the user asks to save it; no resume choice, no ATS, no browser |
| `/jobfishing:jobfishing-tailor` | The user explicitly requests a tailored resume or tailored materials | Generates, reviews, renders, and uploads a tailored CV and a tailored Cover Letter for one job at the same time | Both final PDFs are uploaded to that Job; not responsible for submitting the application |
| `/jobfishing:jobfishing-materials-setup` | First-time setup of the tailored-materials environment, or when the LaTeX doctor check fails | Installs/repairs and validates the shared LaTeX environment | Only saves local machine/user-level LaTeX state and templates; does not modify jobfishing data |
| `/jobfishing:jobfishing-insights` | To analyze the application funnel, conversion rate, job strategy, or outcome feedback | Reads existing Jobs, Applications, scores, stages, and Notes to perform analysis | Read-only by default; does not modify the App |
| `/jobfishing:jobfishing-interview` | An Application has reached the interview stage and needs targeted preparation | Reads the frozen JD, the actual CV/CL, submitted answers, email timeline, and feedback, and generates interview prep | Full prep is saved locally; after the user reviews it, a brief summary of experience and feedback can be appended to the Application Notes |

Common combinations:

```text
Filter jobs: rank
→ Standard application: apply
→ Quick pass through a few jobs: apply-fast
→ Just need a Cover Letter: cover-letter-fast
→ Tailored application: tailor → apply (or tailor → apply-fast)
→ LaTeX issue: materials-setup → tailor
→ Got an interview: interview
→ Reviewing progress later: insights
```

`rank`, `tailor`, `insights`, and `interview` are all additional features invoked separately whenever the user needs them. The main entry point for standard applications is `/jobfishing:jobfishing-apply`; reach for `/jobfishing:jobfishing-apply-fast` only when the user explicitly wants a quicker pass through one or a few jobs.
