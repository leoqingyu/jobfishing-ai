---
name: jobfishing-setup
description: Get the jobfishing tools running. Use when the user has just installed the jobfishing plugin, or when the jobfishing MCP tools (crawl_jobs, recommend, list_jobs) are missing, fail to start, or the user says jobfishing is not working or asks how to install it.
---

# jobfishing Setup

The plugin starts its tools with `uvx`, which needs [uv](https://docs.astral.sh/uv/). uv downloads the right Python and all dependencies by itself, so the user installs no Python and runs no `pip`. The first start takes about 10 seconds; after that it is instant.

## Steps

1. Check whether the tools are there: call a jobfishing tool such as `get_local_preferences`. If it works, say jobfishing is ready and stop.
2. Otherwise check `uv --version`.
3. If uv is missing, tell the user in one sentence that jobfishing needs uv, that installing it is one command, and ask for permission. On approval run the official installer:
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
4. Ask the user to restart the agent session (or reload plugins) so the tools start with uv on the PATH, then re-check with `get_local_preferences`.
5. If the tools still fail, run `uvx --from "https://github.com/leoqingyu/jobfishing-ai/archive/refs/heads/main.zip#subdirectory=plugins/jobfishing" jobfishing-mcp` once in a shell, read the error and report it; do not install packages by hand or create another client.

To update jobfishing later: `uvx --refresh --from "https://github.com/leoqingyu/jobfishing-ai/archive/refs/heads/main.zip#subdirectory=plugins/jobfishing" jobfishing-mcp --help`, then restart the session.

## Rules

- Never run an installer without the user's yes.
- jobfishing needs no account for finding and ranking jobs. Mention signing in only if the user wants tracking, applying or the app's own scores.
