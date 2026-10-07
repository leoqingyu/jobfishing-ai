# jobfishing × Codex — Full User Workflow

This document guides users through the first-time connection of jobfishing, Codex, and Chrome, and through the ongoing usage pattern of "open once, submit a batch, end the task."

jobfishing is the source of truth for candidate profile, resume, jobs, Q&A, and application status. Codex is responsible for reading this data, operating Gmail, Outlook Web, and job-board sites through the Chrome browser already logged in on the user's own machine, and writing the results back to jobfishing once applications are submitted.

## 1. What to Prepare Before Starting

The user needs to prepare:

- A jobfishing account;
- The Codex desktop app, already logged in;
- Google Chrome;
- The ChatGPT Chrome extension;
- A job-search email account already logged into Chrome;
- Python 3.10 or higher;
- The `jobfishing-distribution-0.5.1-complete-v7.zip` dual-compatibility distribution package.

It is recommended to set up a dedicated Gmail or Outlook mailbox for the job search. Other web-based mailboxes that work normally through Chrome will also work.

## 2. Complete jobfishing First

Before letting Codex start working, log in to jobfishing and complete the following:

1. Fill in Basic Info;
2. Fill in Experience;
3. Upload the resumes you plan to use;
4. Check the filename shown for each resume in the App;
5. Review your common application Q&A;
6. Put the jobs you plan to apply to into `Saved`;
7. Decide whether to explicitly authorize Codex to submit directly this round; the App has no separate auto-confirm toggle.

Basic Info is the final source of truth for the name, address, phone number, email, and other personal information in application forms. Users are responsible for the accuracy of the information they enter.

If the information in a resume is inconsistent with Basic Info, Codex should remind the user to update the resume, but the application form should still follow Basic Info.

### Optional: Have Codex Filter the Job List

Job filtering is a standalone feature and does not automatically start submitting applications. On first use, send:

> Use $jobfishing-rank. First read the existing filtering preferences in Experience; if the information is insufficient, ask me a series of questions to understand my target direction, hard constraints, work preferences, and trade-off rules. Save the confirmed preferences to Experience Agent Q&A, then review the Job List and add jobs that match the preferences to Saved. Do not start submitting applications.

Codex will save the confirmed long-term preferences as `job_ranking_preferences_v1` in Experience Agent Q&A. This entry can be edited in the App frontend.

Every subsequent call to this Skill, Codex will first show a summary of the existing preferences and ask whether they need updating. Only after the user confirms the preferences will Codex read the full JD, App score, match details, and hard thresholds to filter jobs. Jobs that are not selected are left unchanged by default and are not automatically deleted.

If you only want to view the ranking without modifying Saved, explicitly send:

> Use $jobfishing-rank, only review and show the recommended results, do not modify the Job List.

## 3. First-Time Plugin Installation for jobfishing

This section only needs to be done once.

### 1. Unzip the Distribution Package

Unzip the package to a fixed location, for example:

- Windows: `%USERPROFILE%\Documents\JobfishingAgent`
- macOS: `$HOME/Documents/JobfishingAgent`
- Linux: `$HOME/JobfishingAgent`

Do not delete or move this folder after installation is complete.

Do not use this plugin directory as your day-to-day Codex Project for submitting applications. The plugin directory is only for storing and installing the runtime program.

### 2. Install the Local Runtime Package

Open a terminal in the unzipped directory.

Windows PowerShell:

```powershell
python -m pip install ".\plugins\jobfishing"
```

macOS Terminal:

```bash
python3 -m pip install "./plugins/jobfishing"
```

On Windows you can confirm the installation with:

```powershell
Get-Command jobfishing-mcp
```

On macOS you can use:

```bash
command -v jobfishing-mcp
```

Linux Terminal uses the same `python3` and `command -v` commands as macOS.

As long as the install location of `jobfishing-mcp` is shown, the local runtime package is ready.

### 3. Install the Codex Plugin

You do not need to run `codex plugin ...` commands in PowerShell. The Codex desktop app and Codex CLI are two different entry points; if you have only installed the desktop version, it is normal for the `codex` command to be missing from PowerShell.

1. Fully quit the Codex desktop app.
2. Reopen Codex and open the unzipped directory of this package as the project. Do not select its parent directory.
3. Open Codex's **Plugins** page, go to **Personal**, and find `jobfishing`.
4. Open the plugin details and click the plus sign to install; if it is already installed, confirm that it is enabled.
5. After installation, create a new task so that the new Skill and MCP tools are loaded.

On the Plugins page, confirm:

- `jobfishing` appears in the Installed section;
- The plugin is enabled;
- The Chrome plugin is enabled.

If `jobfishing` does not appear, first confirm that `.agents/plugins/marketplace.json` exists directly under the current project's root directory, then fully quit and reopen Codex.

After installing the plugin, you need to open a new task before the new Skill and MCP tools will load. OpenAI's official documentation: <https://learn.chatgpt.com/docs/build-plugins>

## 4. Set Up Chrome

### 1. Check the Extension Connection

Open Chrome, open the ChatGPT extension from the toolbar or the extensions menu, and confirm that the sidebar loads normally.

Codex will use this Chrome Profile's existing login state to access email, LinkedIn, job boards, and ATS systems.

### 2. Allow Local File Uploads

Open:

```text
Chrome → Extensions → Manage Extensions → ChatGPT → Details
```

Enable:

```text
Allow access to file URLs
```

This permission is used to upload resumes — which Codex has downloaded to a local temporary directory — to job-board sites.

OpenAI's official setup instructions: <https://learn.chatgpt.com/docs/chrome-extension>

### 3. Site Permissions

When Codex visits a site for the first time, Chrome may ask for authorization. It is recommended to choose based on the situation:

- Allow once; or
- Always allow on this site.

It is not recommended to permanently allow all sites just for convenience.

## 5. Create a Day-to-Day Application Project

Create a new, separate empty folder, for example:

```text
Documents\Job Applications
```

Recommended fixed locations:

- Windows: `%USERPROFILE%\Documents\Job Applications`
- macOS: `$HOME/Documents/Job Applications`
- Linux: `$HOME/Job Applications`

Use this folder to create a new local Project in Codex.

This Project is used to store the user's application tasks and conversations; do not select the plugin's unzipped directory, and there is no need to manually copy resumes into it.

A Codex local Project uses the selected local folder as the task's working directory. OpenAI's official documentation: <https://learn.chatgpt.com/docs/projects>

## 6. First-Time Configuration Check

Create the first task in the new Project and send:

> Use $jobfishing-apply to run a full configuration check. Do not send any emails, upload any files, or submit any applications for now.

Codex should proceed in the following order:

1. Check whether the jobfishing MCP tool is available;
2. If not yet authorized, generate a jobfishing verification link and verification code;
3. Ask the user to open the link, log in to jobfishing, and approve the authorization;
4. Complete the long-term authorization;
5. Ask the user to confirm whether Basic Info, Experience, and resumes have been updated;
6. Once the user confirms, refresh the local cache once for this round;
7. Download all available resumes to a local temporary directory;
8. Check whether the filename of each downloaded resume exactly matches the name shown in the App;
9. Check whether external Chrome is connected;
10. Check whether the job-search inbox is logged in;
11. Output the configuration check results without performing any submissions.

The expected result looks like:

```text
jobfishing connection: ready
jobfishing authorization: ready
Candidate profile: ready
Saved jobs: ready (N)
Resume library: ready (N)
Outbound material filenames: ready
Pulse cache: ready
External Chrome: ready
Job-search inbox: ready
File download: ready
```

If Codex can recognize `$jobfishing-apply` and starts this process, it means the plugin and workflow have loaded successfully.

## 7. Optional: Configure the Shared LaTeX Environment Once

LaTeX is only needed if the user explicitly requests a tailored CV or a tailored Cover Letter. Standard applications and DOCX Cover Letters do not require LaTeX to be installed.

The LaTeX environment is a "system-user-level configuration for the current computer" — it does not belong to any particular Codex Project or any particular conversation. jobfishing always uses the following locations:

| System | Shared state file | Shared template directory | Default LaTeX install root |
| --- | --- | --- | --- |
| Windows | `%USERPROFILE%\.jobfishing\materials\environment.json` | `%USERPROFILE%\.jobfishing\materials\templates` | `%LOCALAPPDATA%\Programs\MiKTeX` |
| macOS | `$HOME/.jobfishing/materials/environment.json` | `$HOME/.jobfishing/materials/templates` | `$HOME/Library/TinyTeX` |
| Linux | `$HOME/.jobfishing/materials/environment.json` | `$HOME/.jobfishing/materials/templates` | `$HOME/.TinyTeX` |

The first time you need tailored materials, send in Codex:

> Use $jobfishing-materials-setup to check and configure the shared LaTeX environment on this computer. Check only for now; if installation is needed, tell me the install location, size, and command first, and wait for my approval.

The Skill will first run an environment check. When the environment is already usable, it will simply reuse it; only when the compiler is missing or template validation fails will it propose an installation or repair plan. On success, it writes the absolute paths for `lualatex` and `xelatex` into the shared state file listed in the table above.

If the same system account later switches to using Claude Code, Claude Code only needs to run the environment check again to reuse the same state file, templates, and compiler — it does not depend on any previous conversation, and there is no need to reinstall.

If the user has already installed LaTeX independently, the compiler paths can be registered explicitly. Windows PowerShell example:

```powershell
python "$env:USERPROFILE\Documents\JobfishingAgent\plugins\jobfishing\skills\jobfishing-materials-setup\scripts\materials_doctor.py" --smoke --write-state --lualatex "D:\TeX\bin\lualatex.exe" --xelatex "D:\TeX\bin\xelatex.exe"
```

macOS example:

```bash
python3 "$HOME/Documents/JobfishingAgent/plugins/jobfishing/skills/jobfishing-materials-setup/scripts/materials_doctor.py" --smoke --write-state --lualatex "/custom/tex/bin/lualatex" --xelatex "/custom/tex/bin/xelatex"
```

Linux example:

```bash
python3 "$HOME/JobfishingAgent/plugins/jobfishing/skills/jobfishing-materials-setup/scripts/materials_doctor.py" --smoke --write-state --lualatex "/custom/tex/bin/lualatex" --xelatex "/custom/tex/bin/xelatex"
```

Do not put `environment.json` inside a Project, the plugin directory, or the Codex cache directory. Each computer and each system account needs to be configured separately; WSL and native Windows are also treated as two separate environments.

### Choosing a Materials Path Before Starting Each Job

jobfishing has two materials paths. The user needs to explicitly tell Codex whether this job requires a tailored resume.

#### Path A: No Tailored Resume Needed

Call `$jobfishing-apply` directly. Codex selects the most suitable resume from the App's existing resumes, and, following the full quality process, generates a standard DOCX Cover Letter locally, saves it via MCP, and uses that same local file to submit the application. Do not call `$jobfishing-tailor`, and LaTeX is not needed.

Prompt:

> Use $jobfishing-apply. This job does not need a tailored resume — please select the most suitable resume from the App's existing resumes; do not re-upload a resume. Generate a DOCX Cover Letter locally following the standard quality process, save it via MCP, and use that same local file to fill out the application. Do not operate the jobfishing frontend, and stop before the final submit button.

#### Path B: Tailored Resume Needed

First call `$jobfishing-tailor`. This Skill generates and validates two LaTeX PDFs at the same time: a tailored CV and a tailored Cover Letter. It will not generate only a CV, and it will not submit the application directly.

First-step prompt:

> Use $jobfishing-tailor to generate a tailored CV and a tailored Cover Letter for "Company Name + Job Title" in jobfishing. Base it on the most suitable existing resume in the App, complete fact-checking, review, LaTeX rendering, and PDF validation, and upload the results back to jobfishing. Do not submit the application after the materials are done.

After both materials have been uploaded successfully, call `$jobfishing-apply`:

> Use $jobfishing-apply to continue with "Company Name + Job Title," which just had tailored materials completed. Use the uploaded tailored CV and tailored Cover Letter to fill out the application, and stop before the final submit button.

If the user wants to complete this continuously within the same task, it can also be stated in one go:

> First use $jobfishing-tailor to generate and upload two tailored materials for "Company Name + Job Title"; once validation is complete, use $jobfishing-apply to continue filling out the application, and stop before the final submit button.

`$jobfishing-tailor` first checks the shared LaTeX environment. When the environment is already usable, it reuses it directly; only when the check fails does it move into `$jobfishing-materials-setup` — there is no need to manually reconfigure it for every job.

### Optional: A Faster Path for a Quick Pass

`$jobfishing-apply-fast` is a leaner sibling of `$jobfishing-apply` for when the user just wants to get through one job, or a handful, quickly — it is not a replacement for the standard entry point. It picks one resume for the whole pass instead of re-deliberating per job, uploads that resume first on any ATS that can parse and autofill from it, drafts and self-reviews the Cover Letter inline instead of dispatching a separate reviewer, and still stops before the final submit button unless direct submission is already on. LinkedIn Easy Apply routing (official posting first, verified email before or alongside Easy Apply) is not shortened in this path.

> Use $jobfishing-apply-fast with my resume #2 for this pass. Process these three Saved jobs; stop before the final submit button on each.

## 8. First Test Submission

For the first test, it is recommended to process only one job and stop before submission.

First put a test job into `Saved` in jobfishing, then send:

> Use $jobfishing-apply. First sync the job-search inbox, then process one Saved job. This test does not need a tailored resume: use the most suitable existing resume in the App and generate a standard DOCX Cover Letter; stop before the final submit button and do not submit.

Codex should perform:

1. Read the job-search inbox starting from where it last left off;
2. Summarize new recruiting emails;
3. Update jobfishing based on the email content;
4. Check whether this job has already been applied to, to avoid duplicate submissions;
5. Read Basic Info, Experience, and application Q&A from this round's cache;
6. Select the appropriate resume slot;
7. Fill out the ATS using the resume with its original filename from the temporary directory;
8. Generate any required application Q&A answers;
9. Generate and check a DOCX Cover Letter locally following the standard quality process, upload it to jobfishing via MCP, and keep the same local file;
10. Upload the local resume and this local DOCX directly to the ATS; the standard process must not re-upload the resume back to jobfishing, nor download the Cover Letter through the jobfishing frontend;
11. Stop before the final submit button and let the user check.

After confirming that the form entries and resume upload are correct, the user sends:

> Continue to submit, and update jobfishing once you have confirmed success.

Codex must see a success confirmation page on the job-board site or a sent email before it can mark the job as submitted.

## 9. Turning On Direct Submission

Once the first test submission succeeds, you can explicitly authorize direct submission within the current task and send:

> Use $jobfishing-apply. First sync the job-search inbox starting from where it last left off, then process all Saved jobs for this round. Direct submission is enabled; stop and ask me if you encounter a CAPTCHA, MFA, a legal disclaimer, conflicting data, or a fact you cannot determine.

Codex can complete this round's jobs continuously, but should still pause and hand off to the user in the following situations:

- CAPTCHA;
- Email or SMS verification codes;
- MFA;
- ATS registration confirmation links;
- Legal disclaimers or electronic signatures;
- Facts that cannot be reliably determined from Basic Info and Experience;
- The job-board site requiring the user to log in again;
- Salary, visa, or relocation questions that require user confirmation.

## 10. Every Subsequent Submission Round

You do not need to reinstall the plugin or re-copy resumes for each submission round.

The standard process is as follows:

1. The user first updates their profile, Experience, resumes, and Saved jobs in jobfishing;
2. Open the same Codex Project;
3. Create a new task;
4. Tell Codex which jobs to process this round and whether direct submission is allowed;
5. Codex asks whether the profile and resumes have been updated;
6. The user confirms;
7. Codex refreshes the cache once for this round;
8. Codex syncs the inbox first, then processes jobs in a batch;
9. Once done, Codex outputs a summary of this round's submissions.

Common prompt:

> Use $jobfishing-apply. My jobfishing profile and resumes have been updated. First sync the job-search inbox, then process all Saved jobs for this round. Direct submission is enabled; stop and ask me if anything requires my personal confirmation or action.

The batch prompt above defaults to using the App's existing resumes and a standard DOCX Cover Letter. If a particular job needs a tailored resume, run `$jobfishing-tailor` for that job separately first, and hand it to `$jobfishing-apply` only after both tailored materials are complete.

## 11. Rules for This Round's Cache

At the start of each submission task, Codex refreshes jobfishing data only once, and saves the following in a local temporary directory:

- Basic Info;
- Experience;
- Application Q&A;
- Job list;
- Application records;
- Resume files.

The same submission round reuses this cache, and does not re-download resumes or re-read all the data for each job.

If the user modifies jobfishing while submissions are in progress, they must explicitly tell Codex:

> I just updated jobfishing — please refresh this round's cache and continue.

Only upon receiving this kind of notice should Codex refresh again within the same round.

Once the task ends, this round's temporary cache is cleared. Re-confirm and refresh again the next time you open a new task.

## 12. Resume and Cover Letter Rules

- Personal information in forms always follows Basic Info;
- A resume is just an uploaded file, not the final source of truth for a form's personal information;
- jobfishing's internal upload name, storage name, and download-cache name may carry internal prefixes; the App is not required to be renamed because of this;
- Before actually uploading to an ATS or attaching to an email, the Agent must create a clean submission copy in this round's local directory — numbers, hashes, UUIDs, timestamps, database keys, or storage prefixes must never be exposed to the employer;
- For a standard (non-tailored) resume, restore the user-visible original name whenever possible; when no reliable name is available, use "Name - CV.extension." A tailored resume uses "Name - CV - Company.extension," and a Cover Letter uses "Name - Cover Letter - Company.extension";
- The Agent does not modify the App's internal files — it only copies them to a clean filename; after the ATS or email shows the attachment, check it once more. If it still shows a dirty filename, remove the attachment and re-upload a clean copy before submitting;
- The current version supports explicitly invoked tailored CVs and Cover Letters; standard applications do not automatically enter the tailoring flow;
- When not tailoring a resume, only call `$jobfishing-apply`: the existing App resume remains read-only, the standard Cover Letter is generated locally as a DOCX, uploaded via MCP, and that same local file is used directly for the application;
- When tailoring a resume, first call `$jobfishing-tailor`: tailored CV PDF + tailored Cover Letter PDF; only after upload and validation are complete should you call `$jobfishing-apply`;
- `$jobfishing-tailor` is not responsible for submitting the application, and `$jobfishing-materials-setup` is only used when the LaTeX environment check fails;
- The standard process must never re-upload a resume; only the tailoring process may upload a tailored resume and use `resume_choice="tailored"`;
- Cover Letters generated by the Agent must be rendered and validated locally, then uploaded back to jobfishing via MCP; they must not be re-downloaded while the local file still exists;
- The Agent must not operate the jobfishing frontend through the browser, including reading data, modifying fields, or uploading/downloading files; all App business operations go through MCP only. The device authorization page is opened and confirmed by the user personally;
- After a successful submission, `resume_choice` only records which resume slot was used — it does not re-upload the resume file back to jobfishing;
- Reusable application Q&A can be saved back to jobfishing, and the user can edit it later in the frontend.

## 13. Email Workflow

Codex uses the web-based mailbox already logged into Chrome on the user's own machine.

Typical supported entry points:

- Gmail or Google Workspace: <https://mail.google.com/>
- Outlook, Hotmail, Live, or Microsoft 365: <https://outlook.live.com/mail/>

Email is used to:

- Find replies from companies;
- Read ATS verification codes;
- Click ATS registration or confirmation links;
- Send applications directly to a company's email address;
- Identify interviews, rejections, requests for supplementary materials, and follow-up actions;
- Update jobfishing based on email results.

At the start of each round, Codex should continue from where it last left off, without needing to reprocess the entire email history.

### The Fixed Order for LinkedIn Easy Apply

When encountering an Easy Apply job, Codex must first look for the original job posting on the company's own website for the same company, role, and location.

1. If the original posting exists on the company website and has a valid application interface: apply directly through the company site or the ATS linked from it, and do not also submit via email or Easy Apply.
2. If the company job page exists but has no application interface: first look for the company's officially published recruiting email address, and only complete Easy Apply after the email submission succeeds.
3. If no original posting can be found on the company website: after confirming the search results within a reasonable scope, first submit via the company's officially published recruiting email address, then complete Easy Apply.
4. If no trustworthy recruiting email address can be found: pause and report — do not guess an email address, and do not skip the email step and go straight to Easy Apply.

When searching for an email address, do not look only at the main content of the job page or the company homepage. Codex must also check Careers/Jobs, Contact, About/Team, the site-wide footer, the Impressum/Legal notice, and any `mailto:` links on the page. Prefer a recruiting email address; when there is no HR/recruiting email address, an officially published general contact address such as `info@`, `hello@`, or `office@` may be used if its purpose is compatible. Applications must not be sent to a privacy/DPO, security, billing, abuse, sales, or dedicated technical-support email address unless the company explicitly states that address accepts applications.

Once the submission is complete, the App's Interview Notes/Application Notes must have the following appended:

- The original job posting link from the company website; if it truly cannot be found, record "original company website job link not found" along with the search date;
- The LinkedIn job link;
- Whether the company website has an application interface;
- The channel(s) actually used and their order;
- The email recipient, email type (recruiting or general contact), the official source page where the email address was found, the send time, and evidence that it was sent;
- The success confirmation or failure reason for Easy Apply.

If the email submission succeeds but Easy Apply fails, do not resend the email. The email already constitutes evidence of application, so the Application should be recorded normally, with the Easy Apply failure and next steps appended to Notes.

## 14. Summary at the End of a Task

At the end of each round, Codex should output a concise results summary:

```text
Submitted: jobs successfully submitted
Failed: jobs that failed this round, and the reasons
Blocked: jobs waiting on the user to handle
Follow-up required: jobs needing a reply, an interview, or supplementary materials
```

Every Blocked job should include a clear next action.

## 15. Frequently Asked Questions

### Codex Doesn't Recognize `$jobfishing-apply`

Check:

1. Whether jobfishing appears in the Installed section of Plugins;
2. Whether the plugin is enabled;
3. Whether a new task was created after installing the plugin;
4. Fully close and reopen Codex and try again.

### The jobfishing MCP Fails to Start

Windows PowerShell:

```powershell
Get-Command jobfishing-mcp
```

macOS:

```bash
command -v jobfishing-mcp
```

If the command cannot be found, go back to the unzipped directory and reinstall the local runtime package.

### Codex Cannot Connect to Chrome

Check:

1. Whether Chrome is running;
2. Whether the ChatGPT extension is installed and enabled;
3. Whether the extension sidebar can be opened;
4. Whether Codex's Chrome plugin is enabled;
5. Whether you are currently using the same Chrome Profile that has the extension installed and the mailbox logged in;
6. Restart Chrome and Codex and create a new task.

### Unable to Upload a Resume

Check whether "Allow access to file URLs" is enabled in the Chrome extension's details.

### The ATS or Email Attachment Shows Numbers, Hashes, UUIDs, or Other Internal Prefixes

A download-cache name with an internal prefix from the App is not itself an error. Codex should keep the original file, create a clean submission copy in this round's local directory, and re-upload it. Only the final filename shown in the ATS or email attachment interface must be clean; do not submit or send until both attachment names have been checked and are correct.

### The User Changed Their Address, Phone Number, or Resume Midway Through

Tell Codex:

> I just updated jobfishing — please refresh this round's cache, remove the old content currently in the form, and re-fill it with the latest Basic Info before continuing.

### A Page Asks for a Verification Code, CAPTCHA, or Legal Confirmation

This is completed by the user personally on the visible Chrome page; once done, tell Codex to continue.

### Codex Has LaTeX Configured, but Claude Code Still Says It Can't Find It

Confirm that both Agents are using the same system account, and check whether the shared state file exists. Have Claude Code run the `jobfishing-materials-setup` environment check once; the checker reads the saved absolute compiler paths and does not depend on Claude Code's current `PATH`. If this is happening on a different computer, a different system account, or in WSL, it needs to be configured separately in that environment.

### The User Wants to Install LaTeX Somewhere Else

That's fine. Use the `--lualatex` and `--xelatex` parameters described in this section to register the two absolute paths and complete the smoke test. Once validated successfully, both Codex and Claude Code will reuse these paths.

## 16. The Daily Actions the User Just Needs to Remember

After the first-time installation is complete, the user's day-to-day routine is just:

```text
Update the App
→ Open the Codex Project
→ Create a new task
→ Confirm the profile and resumes are updated
→ Have Codex sync the inbox and submit a batch
→ Handle a small number of CAPTCHAs or manual confirmations
→ Review this round's summary
```

This is not a 24-hour monitoring task. Codex only works when the user actively opens the Project and starts a submission round.

## 17. Quick Reference for All Skills

| Skill | When to use it | Main actions | What it saves |
| --- | --- | --- | --- |
| `$jobfishing-rank` | Want to filter the Job List or add suitable jobs to Saved | First asks a series of questions about job-search preferences; afterward confirms preferences first; filters using App score, full JD, and match details | Confirmed preferences saved to Experience Agent Q&A; Saved modified when the user asks |
| `$jobfishing-apply` | Configuration check, syncing email, filling out an ATS, submitting via company site/email/Easy Apply | Chooses existing or tailored materials, operates Chrome, updates the Application after submission | Cover Letter, submission status, complete submission record, original company-site link, email and recruiting feedback written to the App |
| `$jobfishing-apply-fast` | A quick one-job or small-batch pass once setup is already done | Same as `apply`, but with one resume for the whole pass, ATS resume-parse autofill first, and an inline self-reviewed Cover Letter instead of a dispatched reviewer | Same write-back as `apply`; still stops before the final submit button |
| `$jobfishing-cover-letter-fast` | Just want a Cover Letter, not a full application | Drafts and self-reviews one job-specific Cover Letter inline, renders a verified local DOCX, uploads to jobfishing only on request | Nothing until the user asks to save it; no resume choice, no ATS, no browser |
| `$jobfishing-tailor` | The user explicitly requests a tailored resume or tailored materials | Generates, reviews, renders, and uploads a tailored CV and tailored Cover Letter for one job at the same time | Both final PDFs uploaded to that Job; not responsible for submitting the application |
| `$jobfishing-materials-setup` | First-time setup of the tailored materials environment, or when the LaTeX doctor check fails | Installs/repairs and validates the shared LaTeX environment | Only saves the local machine's user-level LaTeX state and templates; does not modify jobfishing data |
| `$jobfishing-insights` | Want to analyze the application funnel, conversion rate, job strategy, or outcome feedback | Reads existing Jobs, Applications, scores, stages, and Notes to perform analysis | Read-only by default; does not modify the App |
| `$jobfishing-interview` | An Application has reached the interview stage and needs targeted preparation | Reads the frozen JD, the actual CV/CL, submitted answers, email timeline, and feedback to generate interview prep | Full prep saved locally; after user review, a brief summary of experience and feedback can be appended to Application Notes |

Common combinations:

```text
Filter jobs: rank
→ Standard submission: apply
→ Quick pass through a few jobs: apply-fast
→ Just need a Cover Letter: cover-letter-fast
→ Tailored submission: tailor → apply (or tailor → apply-fast)
→ LaTeX issue: materials-setup → tailor
→ Got an interview: interview
→ Review after a while: insights
```

`rank`, `tailor`, `insights`, and `interview` are all extra functions called individually as needed. The main entry point for standard submissions is `$jobfishing-apply`; reach for `$jobfishing-apply-fast` only when the user explicitly wants a quicker pass through one or a few jobs.
