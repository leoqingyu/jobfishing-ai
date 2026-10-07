#!/usr/bin/env python3
"""Check and smoke-test the shared jobfishing LaTeX environment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES = SKILL_ROOT / "assets" / "templates"
DEFAULT_STATE_DIR = Path.home() / ".jobfishing" / "materials"
_LEGACY_STATE_DIR = Path.home() / ".jobmatchflow" / "materials"  # installs from before the rename
if not DEFAULT_STATE_DIR.exists() and _LEGACY_STATE_DIR.exists():
    DEFAULT_STATE_DIR = _LEGACY_STATE_DIR
TEMPLATE_TARGETS = (
    ("default-cv", "resume.tex", "lualatex"),
    ("default-cover-letter", "cover-letter.tex", "xelatex"),
)


def _template_hash(templates_dir: Path) -> str:
    digest = hashlib.sha256()
    for folder, _, _ in TEMPLATE_TARGETS:
        template_dir = templates_dir / folder
        for path in sorted(template_dir.rglob("*")):
            if not path.is_file():
                continue
            digest.update(path.relative_to(templates_dir).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _install_bundled_templates(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for folder, _, _ in TEMPLATE_TARGETS:
        bundled = source / folder
        if not bundled.is_dir():
            raise RuntimeError(f"Missing bundled template: {bundled}")
        shutil.copytree(bundled, target / folder, dirs_exist_ok=True)


def _default_engine_candidates(name: str) -> list[Path]:
    executable = f"{name}.exe" if os.name == "nt" else name
    home = Path.home()
    candidates: list[Path] = []
    system = platform.system()
    if system == "Windows":
        local_app_data = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        roaming_app_data = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        candidates.extend(
            [
                local_app_data / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64" / executable,
                local_app_data / "Programs" / "MiKTeX" / "miktex" / "bin" / executable,
                program_files / "MiKTeX" / "miktex" / "bin" / "x64" / executable,
                roaming_app_data / "TinyTeX" / "bin" / "windows" / executable,
            ]
        )
    elif system == "Darwin":
        tinytex_bin = home / "Library" / "TinyTeX" / "bin"
        if tinytex_bin.is_dir():
            candidates.extend(sorted(tinytex_bin.glob(f"*/{executable}")))
        candidates.extend(
            [
                home / "Library" / "TinyTeX" / "bin" / "universal-darwin" / executable,
                Path("/Library/TeX/texbin") / executable,
            ]
        )
    else:
        tinytex_bin = home / ".TinyTeX" / "bin"
        if tinytex_bin.is_dir():
            candidates.extend(sorted(tinytex_bin.glob(f"*/{executable}")))
        candidates.append(Path("/usr/bin") / executable)
    return candidates


def _engine_record(
    name: str,
    explicit_path: Path | None,
    previous: dict[str, object] | None,
) -> dict[str, object]:
    if explicit_path is not None:
        candidates = [explicit_path.expanduser()]
    else:
        previous_engines = previous.get("engines") if isinstance(previous, dict) else None
        previous_record = previous_engines.get(name) if isinstance(previous_engines, dict) else None
        previous_path = previous_record.get("path") if isinstance(previous_record, dict) else None
        candidates = []
        if previous_path:
            candidates.append(Path(str(previous_path)).expanduser())
        path_value = shutil.which(name)
        if path_value:
            candidates.append(Path(path_value))
        candidates.extend(_default_engine_candidates(name))

    path: Path | None = None
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        if resolved.is_file():
            path = resolved
            break
    if path is None:
        result: dict[str, object] = {
            "name": name,
            "found": False,
            "path": str(explicit_path.expanduser().resolve()) if explicit_path else None,
            "version": None,
        }
        if explicit_path is not None:
            result["error"] = "Configured engine path does not exist"
        return result
    try:
        completed = subprocess.run(
            [str(path), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        version = (completed.stdout or completed.stderr).splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "name": name,
            "found": False,
            "path": str(path),
            "version": None,
            "error": str(exc),
        }
    return {"name": name, "found": True, "path": str(path), "version": version}


def _read_state(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _smoke_template(
    templates_dir: Path,
    folder: str,
    source_name: str,
    engine: str,
    engine_path: str | None,
) -> dict[str, object]:
    source = templates_dir / folder / source_name
    if not source.is_file():
        return {"template": folder, "engine": engine, "passed": False, "error": f"Missing {source}"}
    if not engine_path:
        return {"template": folder, "engine": engine, "passed": False, "error": f"Missing {engine}"}
    with tempfile.TemporaryDirectory(prefix="jobfishing-latex-smoke-") as temporary:
        output_dir = Path(temporary)
        completed = subprocess.run(
            [
                engine_path,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-no-shell-escape",
                f"-output-directory={output_dir}",
                str(source),
            ],
            cwd=source.parent,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        pdf = output_dir / f"{source.stem}.pdf"
        passed = completed.returncode == 0 and pdf.is_file() and pdf.read_bytes().startswith(b"%PDF-")
        result: dict[str, object] = {
            "template": folder,
            "engine": engine,
            "passed": passed,
            "returncode": completed.returncode,
        }
        if not passed:
            log = (completed.stdout or "") + "\n" + (completed.stderr or "")
            result["error"] = "\n".join(log.splitlines()[-30:])
        return result


def _write_state(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="Compile both bundled templates")
    parser.add_argument("--write-state", action="store_true", help="Persist verified state after smoke tests")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--templates-dir", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--lualatex", type=Path, help="Use this LuaLaTeX executable and persist it after verification")
    parser.add_argument("--xelatex", type=Path, help="Use this XeLaTeX executable and persist it after verification")
    args = parser.parse_args()
    if args.write_state and not args.smoke:
        parser.error("--write-state requires --smoke")

    bundled_templates = args.templates_dir.resolve()
    state_dir = args.state_dir.expanduser().resolve()
    installed_templates = state_dir / "templates"
    state_path = state_dir / "environment.json"
    previous = _read_state(state_path)
    if args.smoke and args.write_state:
        _install_bundled_templates(bundled_templates, installed_templates)
    templates_dir = installed_templates if installed_templates.is_dir() else bundled_templates
    explicit_paths = {"lualatex": args.lualatex, "xelatex": args.xelatex}
    engines = {
        name: _engine_record(name, explicit_paths[name], previous)
        for name in ("lualatex", "xelatex")
    }
    bundled_template_hash = _template_hash(bundled_templates) if bundled_templates.is_dir() else None
    template_hash = _template_hash(templates_dir) if templates_dir.is_dir() else None
    fingerprint_matches = bool(
        previous
        and previous.get("bundled_template_hash") == bundled_template_hash
        and previous.get("template_hash") == template_hash
        and previous.get("engines") == engines
    )
    smoke_results: list[dict[str, object]] = []
    if args.smoke:
        smoke_results = [
            _smoke_template(
                templates_dir,
                folder,
                source,
                engine,
                str(engines[engine].get("path") or "") or None,
            )
            for folder, source, engine in TEMPLATE_TARGETS
        ]
    engines_ready = all(record.get("found") for record in engines.values())
    smoke_ready = bool(smoke_results) and all(result.get("passed") for result in smoke_results)
    ready = engines_ready and (smoke_ready if args.smoke else fingerprint_matches)
    checked_at = datetime.now(timezone.utc).isoformat()
    state = {
        "schema_version": 1,
        "checked_at": checked_at,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "bundled_template_hash": bundled_template_hash,
        "template_hash": template_hash,
        "templates_dir": str(templates_dir),
        "engines": engines,
        "smoke_tests": smoke_results,
    }
    if args.write_state and ready:
        _write_state(state_path, state)

    result = {
        "ready": ready,
        "reason": (
            "verified"
            if ready
            else "missing_engine"
            if not engines_ready
            else "smoke_failed"
            if args.smoke
            else "verification_required"
        ),
        "state_path": str(state_path),
        "state_written": bool(args.write_state and ready),
        **state,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
