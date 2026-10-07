# jobfishing AI Skills

**jobfishing** ([jobfish.ing](https://jobfish.ing), formerly JobMatchFlow) is a free AI job search and CV matching service for Switzerland, Luxembourg, Germany and the Netherlands. This repository is its open-source part: tools that let your own AI agent run the search for any country. (The name is a pun on fishing for jobs; it has nothing to do with jobs in the fishing industry. More: [jobfish.ing/about](https://jobfish.ing/about).)

Open-source [Claude Code](https://code.claude.com) and [Codex](https://openai.com/index/introducing-codex/) tools that let an AI agent run your job search: **find** jobs, **score** them against your CV and profile, **recommend** the best, and, with a [jobfishing](https://app.jobfish.ing) account, **apply** through your own visible Chrome, tailor resumes and cover letters, track outcomes, and prep you for interviews.

Two ways in, and they work together:

- **No account, fully local.** Crawl jobs for any market (Hong Kong, UK, US...) into a SQLite database on your machine (listing first, then the text of the jobs worth it, gently, since there is no proxy), have your agent score many at once, and get ranked recommendations on a small local dashboard. Nothing leaves your computer except the job searches.
- **With a jobfishing account.** jobfishing already crawls Switzerland, Luxembourg, Frankfurt, Munich, Stuttgart, Amsterdam and Rotterdam, scores them for you, and keeps your profile, resumes, saved answers and application status. Your agent reads and writes that data only through the bundled MCP server, and only touches Gmail, Outlook Web and job boards through your own already-logged-in Chrome, never a hidden or headless browser. Your local jobs and the jobfishing list are ranked together on one scale.

## How to use it

Everything below is a sentence you paste into Codex or Claude Code. You never run jobfishing yourself.

### What it can do

| You want to... | Say something like | Needs a jobfishing account? | One-time setup |
| --- | --- | --- | --- |
| Find jobs in any market and rank them | "Use $jobfishing-rank to find data engineer jobs in Hong Kong from the last 3 days" | No | None |
| See and manage them on a page | "Open the jobfishing dashboard" | No | None |
| Score against your full profile | (asked for automatically when you are signed in) | Yes | Fill in your profile in the app |
| Keep the best ones in the app | "Save the top 10 to my jobfishing account" | Yes | Sign in once |
| Tailor a CV and cover letter | "Use $jobfishing-tailor for the Acme data engineer job" | Yes | Install LaTeX once (`$jobfishing-materials-setup` does it with you) |
| A quick cover letter only | "Use $jobfishing-cover-letter-fast for the Acme job" | Yes | None |
| Apply, and read your inbox | "Use $jobfishing-apply to go through my Saved jobs" | Yes | Your agent's Chrome connection (below) |
| See what is working | "Use $jobfishing-insights on my applications" | Yes | None |
| Prepare for an interview | "Use $jobfishing-interview for my Acme interview" | Yes | None |

### A first run, step by step

Paste these in order, one message each.

1. **Crawl.** "Use $jobfishing-rank. Crawl data engineer, data platform engineer and analytics engineer jobs in Hong Kong, posted in the last 3 days." It fetches the listings in seconds. LinkedIn jobs arrive as titles only; Indeed jobs arrive complete.
2. **Fetch the job texts.** "From the titles, pick the LinkedIn jobs worth scoring (skip irrelevant ones and duplicates) and fetch their text." It fetches a few at a time on purpose. If LinkedIn starts limiting your connection, it stops and tells you to wait a few minutes. jobfishing's own job list (Switzerland, Luxembourg, Frankfurt, Munich, Stuttgart, Amsterdam, Rotterdam) is not limited that way.
3. **Score.** "Score the jobs that have their text. Use my jobfishing profile if I'm signed in, otherwise my CV at `C:\path\to\cv.pdf`." Many jobs are scored at once. The profile jobfishing keeps is more complete than a single CV; a CV works too.
4. **Look at the results.** "Open the jobfishing dashboard." The Recommended tab ranks your local jobs and, when you are signed in, your jobfishing jobs, on one scale. Click a job for the score breakdown and the posting.
5. **Keep the good ones.** In the dashboard click **Save to jobfishing...**, tick the jobs, and paste the prompt it gives you into your agent. They appear in your jobfishing Saved list with their scores, private to you.
6. **Start the next batch clean.** When you have finished with this batch, click **Clear all jobs** in the dashboard. It asks first. The jobs disappear from the page; the rows stay in the database file but stay hidden. Then go back to step 1.
7. **Go from found to applied** (needs a jobfishing account): "Use $jobfishing-tailor for the top job in my Saved list", then "Use $jobfishing-apply to apply to my Saved jobs" and "Use $jobfishing-apply to check my inbox and update my application statuses".

The dashboard also shows ready-made prompts at the right moments: one when jobs are waiting to be scored, one after a crawl when some jobs have only a title, and one for saving.

### What you need to set up, and what you do not

You do **not** follow an install guide, unzip anything, or install Python. The one-line install does everything, and `uv` fetches whatever the tools need.

- **LaTeX, only for tailored CVs.** Say "Use $jobfishing-materials-setup". It checks your machine, and if there is no LaTeX it walks you through installing one (TinyTeX or MiKTeX) and tests it with the bundled templates. Do it once per computer. Cover letters from `$jobfishing-cover-letter-fast` are Word files and need nothing.
- **A Chrome connection, only for applying and reading your inbox.** In Codex use the ChatGPT Chrome integration; in Claude Code run `/chrome` and approve Claude in Chrome. jobfishing drives your own, visible, already-logged-in Chrome and never a hidden browser.
- **Your profile in the app, only to improve scores.** Without one, scoring uses your CV.
- Your local jobs live in `~/.jobfishing/` (on Windows `%USERPROFILE%\.jobfishing\`).

## Which guide do I need?

For most people the answer is **none**. If the one-line install finished and `$jobfishing-rank` answers, you have everything in this README and nothing to set up twice.

The two long guides are a companion for the parts that need more hand-holding. Open the one for your agent: [Claude Code](docs/claude-code-guide.md) or [Codex](docs/codex-guide.md).

| Your situation | Open | Section |
| --- | --- | --- |
| The one-line install worked and you only find, score, save and recommend jobs | Nothing | |
| You want to apply through your own Chrome or have it read your inbox, for the first time | The guide | Connecting to Chrome, the day-to-day project, the first configuration check and the first trial submission (sections 4 to 8) |
| You want to turn on direct submission and run application rounds every day | The guide | Sections 9 to 14, then the daily routine in section 16 |
| You want tailored CVs and already have LaTeX, or want it somewhere specific | The guide | Section 7 (Optional: shared LaTeX environment). For a normal install just say `$jobfishing-materials-setup` |
| The one-line install cannot run on your computer (locked-down machine, no way to run a script from the internet), or you prefer to install it as a plugin | The guide | Section 3 (Manual installation) |
| Something is not working: a skill is not recognized, the tools will not start, Chrome will not connect, an upload fails | The guide | Section 15 (Frequently asked questions) |
| You want to see every rule the apply skill follows (filenames, cache rules, email order, end-of-round summary) | The guide | Sections 10 to 14 and the quick reference in section 17 |

Tip: you do not have to read a guide front to back. Find your row, open that section only.

## Skills

| Skill | What it does |
| --- | --- |
| `jobfishing-setup` | Gets the tools running: checks for `uv` (which brings its own Python), installs it with your permission, and verifies the connection. |
| `jobfishing-rank` | Interviews you about job-search preferences, then finds and ranks jobs: from your jobfishing list, from a local crawl of any market (no account needed, many jobs scored at once), or both on one scale. Shortlists qualified jobfishing matches into Saved when you ask. |
| `jobfishing-apply` | Runs application sessions: setup checks, inbox sync, ATS/email submission, and reconciling outcomes — using jobfishing's MCP data and your visible Chrome. |
| `jobfishing-apply-fast` | Leaner sibling of `jobfishing-apply` for a quick one-job or small-batch pass: picks one resume for the whole pulse, leans on ATS resume-parse autofill, drafts and self-reviews the cover letter inline instead of dispatching a reviewer, and still stops before the final submit. |
| `jobfishing-tailor` | Produces a truthful, tailored CV and cover letter for one job, with multi-stage review, local LaTeX rendering, verification, and upload back to jobfishing. |
| `jobfishing-cover-letter-fast` | Just need a Cover Letter, not a full application? Generates one truthful, job-specific Cover Letter as a local Word file in one fast pass, and uploads it to jobfishing only on request. |
| `jobfishing-materials-setup` | Checks, installs, or repairs the shared local LaTeX toolchain that tailored-materials rendering depends on. |
| `jobfishing-insights` | Read-only analysis of your application funnel, stage timing, targeting patterns, and outcomes from existing jobfishing data. |
| `jobfishing-interview` | Prepares you for an interview from the exact snapshot jobfishing submitted — the real resume, cover letter, and notes the employer received. |

Each skill is scoped narrowly on purpose: the agent should reach for exactly one of these when asked, not improvise a workflow of its own.

## Guides

Full first-connection and day-to-day usage walkthroughs:

- [`docs/claude-code-guide.md`](docs/claude-code-guide.md) — jobfishing + Claude Code + Claude in Chrome
- [`docs/codex-guide.md`](docs/codex-guide.md) — jobfishing + Codex

## Install

One line, in a terminal. It sets jobfishing up for Claude Code and Codex, whichever you have, and needs no Python, no pip and no git.

**macOS / Linux**

```bash
curl -fsSL https://jobfish.ing/install | sh
```

**Windows (PowerShell)**

```powershell
irm https://jobfish.ing/install.ps1 | iex
```

Then restart your agent and say: **find me jobs**. Finding and ranking jobs needs no jobfishing account. Please read the [Disclaimer and data](#disclaimer-and-data) section first: it is short, and it says what runs on your computer and what leaves it.

What the script does, and nothing else: installs [uv](https://docs.astral.sh/uv/) if it is missing (uv brings its own Python), downloads this repo's `plugins/jobfishing`, and then runs `jobfishing install`, which

- registers the MCP server with **Claude Code** (`claude mcp add --scope user`), and copies the skills to `~/.claude/skills`;
- registers the MCP server with **Codex** (a `[mcp_servers.jobfishing]` table in `~/.codex/config.toml`), and copies the skills to `~/.agents/skills`.

It only configures the agents it finds on the machine; if you install an agent later, run the line again (it is safe to repeat). Read the scripts first if you like: [install.sh](https://jobfish.ing/install.sh), [install.ps1](https://jobfish.ing/install.ps1).

**Updates are automatic.** Each time your agent starts jobfishing, `uv` checks GitHub for a newer version and fetches it, and the skills copied by the installer are refreshed to match. A new version is therefore live the next time you restart your agent (once or twice at most). Nothing to run.

To force an update now, or to uninstall:

```bash
uvx --refresh --from "https://github.com/leoqingyu/jobfishing-ai/archive/refs/heads/main.zip#subdirectory=plugins/jobfishing" jobfishing install     # update now
uvx --from "https://github.com/leoqingyu/jobfishing-ai/archive/refs/heads/main.zip#subdirectory=plugins/jobfishing" jobfishing uninstall            # remove
```

Your local jobs and scores live in `~/.jobfishing/`; delete that folder to clear them.

### Alternative: install as a plugin

This repo is also a [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugins) and a Codex plugin source, rooted at `plugins/jobfishing`. You need [uv](https://docs.astral.sh/uv/) installed first.

**Claude Code**

```
/plugin marketplace add leoqingyu/jobfishing-ai
/plugin install jobfishing
```

**Codex**

Point Codex at `plugins/jobfishing` per its plugin-source instructions; the manifest lives at `plugins/jobfishing/.codex-plugin/plugin.json`.

Use one method or the other, not both, or you will see two copies of the skills. Both share one local MCP server and one LaTeX environment for tailored materials, so `jobfishing-materials-setup` only needs to run once per machine.

## Disclaimer and data

jobfishing is open source (MIT) and comes **as is, without warranty of any kind**. This section says plainly what it does on your computer and what leaves it. It is not legal advice.

**Crawling is done from your own computer and is your responsibility.**
- `crawl_jobs` and `fetch_descriptions` send ordinary web requests to LinkedIn and Indeed from your connection, with no proxy. Those sites' terms restrict automated access, and they may limit or block your connection. You are responsible for how you use this and for following the terms of any site you access. Keep searches modest: a few titles and places per run, not hundreds. If LinkedIn starts limiting you, stop and wait; the tools stop on their own and say so.
- jobfishing's own job list is crawled by jobfishing with its own infrastructure; using it does not run anything from your connection.

**Scores and recommendations are a rough guide, not advice.**
- Local scores come from judgments your own AI agent makes, combined by a fixed formula. Different models judge differently, and a posting may be misread. Use them to sort, then read the posting yourself. Nothing here predicts whether you will be hired.
- Everything the agent writes for you (tailored CVs, cover letters, form answers) is generated. Read it before it is sent. You are responsible for what you submit and for its being true.

**Applying and reading your inbox are your decisions.**
- The application skills drive your own, visible Chrome, with your logins. Review what they do, especially before a final submit, and for any site or mailbox you would not want automated.

**What stays on your computer, and what leaves it**
- Crawled jobs and scores are stored locally in `~/.jobfishing/` (on Windows `%USERPROFILE%\.jobfishing\`). The dashboard runs only on your machine (`127.0.0.1`). There is no telemetry or usage tracking in the local tools.
- The job texts and CV or profile your agent reads go to **whichever AI provider your agent uses** (OpenAI, Anthropic, ...), under that provider's terms. jobfishing does not control that.
- Without a jobfishing account, the only other network traffic is your searches to LinkedIn and Indeed, and fetching updates (below).
- **Signed in to jobfishing:** the tools talk to `app.jobfish.ing`. They read your profile, jobs, resumes and application tracking, and write what you ask them to: saved jobs with their scores, cover letters and resumes, application status. A job you save from a local crawl is private to your account. The sign-in token is kept in `~/.jobfishing/agent_token`, readable only by you on macOS and Linux. You can revoke it from the app.
- Imported jobs are scored from the extraction and judgments your agent supplies; jobfishing does not run a model on them.

**The tools update themselves.** When your agent starts them, `uv` checks this repository for a newer version and fetches it, so the code that runs on your computer is whatever is on the `main` branch at that moment. Read the code if you want to know what it does; it is all here. To stop using it, run the uninstall command above and delete `~/.jobfishing/`.

Questions or concerns: hello@jobfish.ing.

## Contributing

This plugin is young and the skills are opinionated first drafts. Issues and pull requests are welcome — better prompts, edge cases the skills miss, additional guides, or support for other hosts.

## License

MIT — see [LICENSE](LICENSE).
