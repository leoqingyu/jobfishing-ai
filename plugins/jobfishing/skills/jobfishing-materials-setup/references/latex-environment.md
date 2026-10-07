# LaTeX environment setup

## Persistent scope

The LaTeX distribution and engines are OS-user installations, not project dependencies. Codex and Claude Code share one canonical state:

```text
~/.jobfishing/materials/environment.json
```

The state records OS, architecture, engine paths and versions, bundled-template fingerprint, and verification time. Never store jobfishing tokens or candidate data there.

| OS | Shared state | Installed jobfishing templates |
|---|---|---|
| Windows | `%USERPROFILE%\.jobfishing\materials\environment.json` | `%USERPROFILE%\.jobfishing\materials\templates` |
| macOS | `$HOME/.jobfishing/materials/environment.json` | `$HOME/.jobfishing/materials/templates` |
| Linux | `$HOME/.jobfishing/materials/environment.json` | `$HOME/.jobfishing/materials/templates` |

Do not put this state inside a Codex Project, Claude working directory, plugin cache, or extracted distribution folder. It survives plugin upgrades and is discovered without conversation context.

## Preferred distributions

- Windows default: per-user MiKTeX under `%LOCALAPPDATA%\Programs\MiKTeX`. Typical engine directory: `%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64`. Configure missing-package installation so non-interactive compilation does not block on GUI prompts.
- macOS default: TinyTeX under `$HOME/Library/TinyTeX`. BasicTeX or MacTeX exposed through `/Library/TeX/texbin` is accepted when already installed.
- Linux default: user-level TinyTeX under `$HOME/.TinyTeX`. A trusted system TeX Live installation under `/usr/bin` is accepted when already installed.

Use the user's available trusted package manager or the distribution's official installer. Do not download an installer from an unverified mirror. Installation may be large and may require administrator approval; state this before asking permission.

The doctor resolves each engine in this order:

1. an explicit `--lualatex` or `--xelatex` path supplied by the user;
2. the last verified absolute path in the canonical state;
3. the current process `PATH`;
4. the OS defaults above.

After a successful `--smoke --write-state`, the absolute paths in `engines.*.path` are the source of truth for both hosts. Tailoring must invoke those exact paths instead of assuming that Codex and Claude Code inherited the same shell `PATH`.

For a custom existing installation, keep the canonical state location and register the engines once:

```text
python materials_doctor.py --smoke --write-state --lualatex <absolute-lualatex> --xelatex <absolute-xelatex>
```

Changing `--state-dir` is reserved for testing or an explicitly managed deployment. It is not the normal user customization path because another host would no longer find the state automatically.

## Security and isolation

- Compile with `-no-shell-escape`, `-interaction=nonstopmode`, and `-halt-on-error`.
- Run smoke tests and application compiles in a dedicated temporary/material directory containing only the selected template and required assets.
- Do not let a custom template install packages, execute lifecycle scripts, or substitute an arbitrary compile command.
- Never copy authorization tokens, mailbox state, browser profiles, or unrelated workspace files into the compile directory.

## Repair decisions

- Missing state, engines present: run smoke verification and write state.
- Host `PATH` differs but state engine paths are valid: reuse the state paths; do not reinstall.
- Template fingerprint changed: rerun smoke verification; do not reinstall engines unless compilation identifies a missing package.
- Engine path/version changed: rerun smoke verification.
- Missing package: install only the package reported by the trusted compiler/package manager, then rerun smoke.
- Missing engine/distribution: request approval for the OS-appropriate installation.
- Smoke failure after one targeted repair: report the compiler log and stop instead of repeatedly reinstalling.

The bundled default CV uses `lualatex`; the bundled default Cover Letter uses `xelatex`.
