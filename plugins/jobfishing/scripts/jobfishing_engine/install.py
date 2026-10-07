"""`jobfishing install`: register the MCP server and copy the skills into the agents found on this machine.

Claude Code: `claude mcp add --scope user` plus ~/.claude/skills. Codex: a [mcp_servers.jobfishing] table in
~/.codex/config.toml plus ~/.codex/skills. Idempotent, and `jobfishing uninstall` reverses it.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path

SPEC = os.environ.get("JOBFISHING_SPEC") or "git+https://github.com/leoqingyu/jobfishing-ai#subdirectory=plugins/jobfishing"
MCP_ARGS = ["--from", SPEC, "jobfishing-mcp"]
SKILL_PREFIX = "jobfishing-"
TABLE = "[mcp_servers.jobfishing]"


def _uvx() -> str:
    return shutil.which("uvx") or "uvx"


def _skills_src() -> Path:
    return Path(str(resources.files("jobfishing_skills")))


def _copy_skills(dest_root: Path) -> list[str]:
    dest_root.mkdir(parents=True, exist_ok=True)
    names = []
    for d in sorted(_skills_src().iterdir()):
        if d.is_dir() and d.name.startswith(SKILL_PREFIX):
            target = dest_root / d.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(d, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            names.append(d.name)
    return names


def _remove_skills(dest_root: Path) -> int:
    n = 0
    if dest_root.is_dir():
        for d in dest_root.iterdir():
            if d.is_dir() and d.name.startswith(SKILL_PREFIX):
                shutil.rmtree(d)
                n += 1
    return n


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


# ---- Claude Code -----------------------------------------------------------------------------------------------------

def install_claude() -> str:
    claude = shutil.which("claude")
    if not claude:
        return ""
    _run([claude, "mcp", "remove", "--scope", "user", "jobfishing"])  # idempotent: replace any earlier registration
    r = _run([claude, "mcp", "add", "--scope", "user", "jobfishing", "--", _uvx(), *MCP_ARGS])
    if r.returncode != 0:
        return f"Claude Code: could not register the MCP server ({(r.stderr or r.stdout).strip()[:200]})"
    skills = _copy_skills(Path.home() / ".claude" / "skills")
    return f"Claude Code: MCP server registered, {len(skills)} skills copied to ~/.claude/skills"


def uninstall_claude() -> str:
    claude = shutil.which("claude")
    if not claude:
        return ""
    _run([claude, "mcp", "remove", "--scope", "user", "jobfishing"])
    return f"Claude Code: MCP server removed, {_remove_skills(Path.home() / '.claude' / 'skills')} skills removed"


# ---- Codex -----------------------------------------------------------------------------------------------------------

def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _codex_block() -> str:
    args = ", ".join(_toml_str(a) for a in MCP_ARGS)
    return f"{TABLE}\ncommand = {_toml_str(_uvx())}\nargs = [{args}]\n"


def _strip_table(text: str) -> str:
    """Drop an existing [mcp_servers.jobfishing] table (up to the next [table] header) so a re-install replaces it."""
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        st = line.strip()
        if st == TABLE:
            skipping = True
            continue
        if skipping and st.startswith("[") and not st.startswith("[mcp_servers.jobfishing."):
            skipping = False
        if not skipping:
            out.append(line)
    return "".join(out)


def install_codex() -> str:
    home = _codex_home()
    if not (shutil.which("codex") or home.is_dir()):
        return ""
    home.mkdir(parents=True, exist_ok=True)
    cfg = home / "config.toml"
    text = _strip_table(cfg.read_text(encoding="utf-8")).rstrip() if cfg.exists() else ""
    cfg.write_text((text + "\n\n" if text else "") + _codex_block(), encoding="utf-8")
    skills = _copy_skills(home / "skills")
    return f"Codex: MCP server written to {cfg}, {len(skills)} skills copied to {home / 'skills'}"


def uninstall_codex() -> str:
    home = _codex_home()
    cfg = home / "config.toml"
    if not (shutil.which("codex") or home.is_dir()):
        return ""
    if cfg.exists():
        cfg.write_text(_strip_table(cfg.read_text(encoding="utf-8")).rstrip() + "\n", encoding="utf-8")
    return f"Codex: MCP server removed, {_remove_skills(home / 'skills')} skills removed"


# ---- CLI -------------------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="jobfishing", description="jobfishing for your AI agent")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("install", help="register jobfishing with Claude Code and/or Codex")
    sub.add_parser("uninstall", help="remove what install added")
    sub.add_parser("ui", help="open the local dashboard without an agent")
    args = ap.parse_args(argv)
    if args.cmd == "ui":
        from .web import main as ui
        ui()
        return 0
    if args.cmd not in ("install", "uninstall"):
        ap.print_help()
        return 0
    fns = (install_claude, install_codex) if args.cmd == "install" else (uninstall_claude, uninstall_codex)
    lines = [m for m in (f() for f in fns) if m]
    if not lines:
        print("No Claude Code or Codex found on this machine. Install one of them, then run this again.")
        return 1
    print("\n".join(lines))
    if args.cmd == "install":
        print("\nDone. Restart your agent, then say: find me jobs  (jobfishing needs no account to search and rank).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
