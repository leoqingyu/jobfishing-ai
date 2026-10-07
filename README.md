# jobfishing AI Skills

Open-source [Claude Code](https://code.claude.com) and [Codex](https://openai.com/index/introducing-codex/) plugin that lets an AI agent drive the [jobfishing](https://app.jobfish.ing) job-search workflow end to end: ranking jobs against your preferences, applying through your own visible Chrome session, tailoring resumes and cover letters, analyzing outcomes, and prepping you for interviews — all from data jobfishing already has, batched instead of one job at a time.

jobfishing stays the single source of truth for your profile, resumes, jobs, saved answers, and application status. The agent reads and writes that data only through the bundled MCP server, and only touches Gmail, Outlook Web, and job boards through your own already-logged-in Chrome — never a hidden or headless browser.

## Skills

| Skill | What it does |
| --- | --- |
| `jobfishing-rank` | Interviews you about job-search preferences, saves the confirmed profile, ranks untracked jobs, and shortlists qualified matches into Saved. |
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

This repo is both a [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugins) and a Codex plugin source, rooted at `plugins/jobfishing`.

**Claude Code**

```
/plugin marketplace add <this-repo-url>
/plugin install jobfishing
```

**Codex**

Point Codex at `plugins/jobfishing` per its plugin-source instructions; the manifest lives at `plugins/jobfishing/.codex-plugin/plugin.json`.

Both hosts share one local MCP bridge (`plugins/jobfishing/scripts/jobfishing_mcp_server.py`, Python 3.10+) and one LaTeX environment for tailored materials, so `jobfishing-materials-setup` only needs to run once per machine.

## Contributing

This plugin is young and the skills are opinionated first drafts. Issues and pull requests are welcome — better prompts, edge cases the skills miss, additional guides, or support for other hosts.

## License

MIT — see [LICENSE](LICENSE).
