# jobfishing AI Skills

Open-source [Claude Code](https://code.claude.com) and [Codex](https://openai.com/index/introducing-codex/) tools that let an AI agent run your job search: **find** jobs, **score** them against your CV and profile, **recommend** the best, and, with a [jobfishing](https://app.jobfish.ing) account, **apply** through your own visible Chrome, tailor resumes and cover letters, track outcomes, and prep you for interviews.

Two ways in, and they work together:

- **No account, fully local.** Crawl jobs for any market (Hong Kong, UK, US...) into a SQLite database on your machine, have your agent score many at once, and get ranked recommendations on a small local dashboard. Nothing leaves your computer except the job searches.
- **With a jobfishing account.** jobfishing already crawls Switzerland, Luxembourg, Frankfurt, Munich, Stuttgart, Amsterdam and Rotterdam, scores them for you, and keeps your profile, resumes, saved answers and application status. Your agent reads and writes that data only through the bundled MCP server, and only touches Gmail, Outlook Web and job boards through your own already-logged-in Chrome, never a hidden or headless browser. Your local jobs and the jobfishing list are ranked together on one scale.

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

Then restart your agent and say: **find me jobs**. Finding and ranking jobs needs no jobfishing account.

What the script does, and nothing else: installs [uv](https://docs.astral.sh/uv/) if it is missing (uv brings its own Python), downloads this repo's `plugins/jobfishing`, and then runs `jobfishing install`, which

- registers the MCP server with **Claude Code** (`claude mcp add --scope user`), and copies the skills to `~/.claude/skills`;
- registers the MCP server with **Codex** (a `[mcp_servers.jobfishing]` table in `~/.codex/config.toml`), and copies the skills to `~/.agents/skills`.

It only configures the agents it finds on the machine; if you install an agent later, run the line again (it is safe to repeat). Read the scripts first if you like: [install.sh](https://jobfish.ing/install.sh), [install.ps1](https://jobfish.ing/install.ps1).

**Update / uninstall**

```bash
uvx --refresh --from "https://github.com/leoqingyu/jobfishing-ai/archive/refs/heads/main.zip#subdirectory=plugins/jobfishing" jobfishing install     # update
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

## Contributing

This plugin is young and the skills are opinionated first drafts. Issues and pull requests are welcome — better prompts, edge cases the skills miss, additional guides, or support for other hosts.

## License

MIT — see [LICENSE](LICENSE).
