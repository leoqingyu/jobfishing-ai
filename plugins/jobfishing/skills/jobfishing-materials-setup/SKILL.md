---
name: jobfishing-materials-setup
description: Check, install, or repair the system-wide local LaTeX environment used for jobfishing tailored CV and Cover Letter PDFs. Use when the user asks to configure tailored materials or when the jobfishing materials doctor reports an invalid environment. Do not invoke during standard DOCX applications when the environment is healthy or irrelevant.
---

# jobfishing Materials Setup

Configure the LaTeX toolchain once per OS user account, shared by Codex and Claude Code. Read [latex-environment.md](references/latex-environment.md) before installing or repairing anything. Both hosts must use the canonical state at `~/.jobfishing/materials/environment.json`; do not create host-specific state or reinstall because a new project has no prior conversation context.

## Start with doctor

Run:

```text
python scripts/materials_doctor.py
```

Resolve the script path from this skill directory. If it returns `ready=true`, stop; do not reinstall or run a full smoke test. Retain `engines.lualatex.path` and `engines.xelatex.path` from the JSON for later compilation; they may come from shared state even when the current host's `PATH` differs.

If both engines exist but the state is unverified or the template fingerprint changed, run:

```text
python scripts/materials_doctor.py --smoke --write-state
```

This is a verification/migration, not a system installation.

## Installation boundary

If `lualatex` or `xelatex` is missing, explain the detected state, OS default install root, proposed distribution, approximate system impact, and exact command before acting. Obtain user approval immediately before any package-manager, installer, administrator, or system-PATH change.

If the user already has a custom LaTeX installation, do not move or reinstall it. Run the smoke doctor once with `--lualatex <absolute-path>` and `--xelatex <absolute-path>` plus `--write-state`; later Codex and Claude Code sessions will reuse those persisted paths.

After installation, run the smoke doctor with `--write-state`. It installs the bundled default templates under `~/.jobfishing/materials/templates/`, compiles both without shell escape, and records their fingerprint. Setup is complete only when the JSON result says `ready=true`.

Do not create separate Codex or Claude Code configuration for LaTeX. A host switch only requires running the ordinary doctor; a healthy shared state is sufficient.

Do not install on every new project or task. Re-enter setup only after a failed doctor, a missing engine, a changed template/toolchain fingerprint, or an explicit repair request.
