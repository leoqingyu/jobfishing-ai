#!/usr/bin/env python3
"""Local JobMatchFlow MCP bridge with self-service authorization and pulse caching."""

from __future__ import annotations

import atexit
import base64
import binascii
import io
import json
import os
import platform
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from mcp.server.mcpserver import MCPServer


API_BASE = "https://app.jobmatchflow.com"
AUTHORIZATION_PAGE = f"{API_BASE}/app/agent-authorize"
TOKEN_CACHE_PATH = Path.home() / ".jobmatchflow" / "agent_token"
MAIL_CHECKPOINT_PATH = Path.home() / ".jobmatchflow" / "mail_sync_checkpoints.json"


def _read_cached_token() -> str | None:
    try:
        return TOKEN_CACHE_PATH.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _write_cached_token(token: str) -> None:
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(token, encoding="utf-8")
    try:
        TOKEN_CACHE_PATH.chmod(0o600)
    except OSError:
        pass


def _read_mail_checkpoints() -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(MAIL_CHECKPOINT_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Cannot read the local mail checkpoint file: {MAIL_CHECKPOINT_PATH}"
        ) from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Invalid local mail checkpoint file: {MAIL_CHECKPOINT_PATH}")
    return value


def _write_mail_checkpoints(value: dict[str, dict[str, Any]]) -> None:
    MAIL_CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = MAIL_CHECKPOINT_PATH.with_name(
        f"{MAIL_CHECKPOINT_PATH.name}.{os.getpid()}.tmp"
    )
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(MAIL_CHECKPOINT_PATH)
        try:
            MAIL_CHECKPOINT_PATH.chmod(0o600)
        except OSError:
            pass
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _clear_cached_token() -> None:
    try:
        TOKEN_CACHE_PATH.unlink()
    except OSError:
        pass


TOKEN: str | None = _read_cached_token()
session = requests.Session()
if TOKEN:
    session.headers["Authorization"] = f"Bearer {TOKEN}"

pending_device_code: str | None = None


def _forget_token() -> None:
    global TOKEN
    TOKEN = None
    session.headers.pop("Authorization", None)


def _accept_token(token: str) -> None:
    global TOKEN
    TOKEN = token
    session.headers["Authorization"] = f"Bearer {token}"
    _write_cached_token(token)


def _call(method: str, path: str, **kwargs: Any) -> Any:
    if not TOKEN:
        raise RuntimeError(
            "JobMatchFlow is not authorized. Call start_device_authorization, show the "
            "verification link and code to the user, then call finish_device_authorization."
        )
    response = session.request(method, f"{API_BASE}{path}", timeout=30, **kwargs)
    if response.status_code == 401:
        _clear_cached_token()
        _forget_token()
        raise RuntimeError(
            "The JobMatchFlow authorization is invalid or revoked. Start device authorization again."
        )
    response.raise_for_status()
    return response.json()


# One MCP process owns one disposable cache root. A new application pulse explicitly
# creates a new snapshot; previous snapshots survive until process exit so open ATS tabs
# never lose a file path midway through an upload.
CACHE_ROOT = Path(tempfile.mkdtemp(prefix="jobmatchflow-session-"))
atexit.register(shutil.rmtree, CACHE_ROOT, ignore_errors=True)

cache_created_at: str | None = None
cache_dir: Path | None = None
cached_context: dict[str, Any] | None = None
cached_jobs: list[dict[str, Any]] | None = None
cached_tracking: list[dict[str, Any]] | None = None
cached_resumes: list[dict[str, Any]] | None = None
cached_resume_files: dict[str, dict[str, Any]] = {}

MAX_APPLICATION_MATERIAL_BYTES = 15 * 1024 * 1024
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _safe_exact_filename(value: object) -> str:
    """Return an App filename unchanged, or fail instead of silently renaming it."""
    name = str(value or "").strip()
    invalid = '<>:"/\\|?*'
    if (
        not name
        or name in {".", ".."}
        or Path(name).name != name
        or any(char in invalid or ord(char) < 32 for char in name)
        or name.endswith((" ", "."))
    ):
        raise RuntimeError(
            f"File name {name!r} cannot be used unchanged on Windows and macOS. "
            "Rename it in JobMatchFlow, then try again."
        )
    return name


def _resume_name(resume: dict[str, Any], payload: dict[str, Any], slot: str) -> str:
    # cv_name is the user-visible App name and is authoritative. The payload filename
    # can contain a storage hash and must never leak into an ATS upload.
    app_name = resume.get("cv_name") or payload.get("cv_name")
    if not app_name:
        raise RuntimeError(f"Resume {slot} has no cv_name in JobMatchFlow")
    return _safe_exact_filename(app_name)


def _store_resume(
    resume: dict[str, Any], payload: dict[str, Any], snapshot_dir: Path
) -> dict[str, Any]:
    slot = str(resume.get("slot") or "").strip()
    if not slot:
        raise RuntimeError("JobMatchFlow returned a resume without a slot")
    encoded = payload.get("content_base64")
    if not encoded:
        raise RuntimeError(f"JobMatchFlow returned no file content for {slot}")
    filename = _resume_name(resume, payload, slot)
    slot_dir = snapshot_dir / "resumes" / slot
    slot_dir.mkdir(parents=True, exist_ok=True)
    path = slot_dir / filename
    path.write_bytes(base64.b64decode(encoded))
    return {
        "slot": slot,
        "cv_name": filename,
        "filename": filename,
        "local_path": str(path.resolve()),
        "mime_type": str(payload.get("mime_type") or "application/octet-stream"),
        "size": path.stat().st_size,
        "has_source_file": bool(resume.get("has_source_file")),
    }


def _application_material_mime(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise RuntimeError("The application material is not a valid PDF")
        return "application/pdf"
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
                if archive.testzip() is not None:
                    raise RuntimeError("The application material DOCX contains a damaged ZIP entry")
        except (OSError, zipfile.BadZipFile) as exc:
            raise RuntimeError("The application material is not a valid DOCX") from exc
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise RuntimeError("The application material is not a valid DOCX")
        return DOCX_MIME_TYPE
    raise RuntimeError("An application material upload must use a .pdf or .docx filename")


def _store_application_material(
    tracking_id: int, material_type: str, payload: dict[str, Any]
) -> dict[str, Any]:
    filename = _safe_exact_filename(payload.get("filename"))
    encoded = payload.get("content_base64")
    if not isinstance(encoded, str) or not encoded:
        raise RuntimeError(
            f"JobMatchFlow returned no {material_type} file content for tracking {tracking_id}"
        )
    try:
        content = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(
            f"JobMatchFlow returned invalid Base64 for tracking {tracking_id} {material_type}"
        ) from exc
    if not content:
        raise RuntimeError(
            f"JobMatchFlow returned an empty {material_type} for tracking {tracking_id}"
        )
    material_dir = CACHE_ROOT / "application-materials" / str(tracking_id) / material_type
    material_dir.mkdir(parents=True, exist_ok=True)
    path = material_dir / filename
    path.write_bytes(content)
    return {
        "tracking_id": tracking_id,
        "material_type": material_type,
        "asset_id": payload.get("asset_id"),
        "filename": filename,
        "local_path": str(path.resolve()),
        "mime_type": str(payload.get("mime_type") or "application/octet-stream"),
        "size": path.stat().st_size,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _invalidate(*names: str) -> None:
    global cached_context, cached_jobs, cached_tracking, cached_resumes
    for name in names:
        if name == "context":
            cached_context = None
        elif name == "jobs":
            cached_jobs = None
        elif name == "tracking":
            cached_tracking = None
        elif name == "resumes":
            cached_resumes = None


def _mailbox_key(provider: str, mailbox: str) -> tuple[str, str, str]:
    normalized_provider = str(provider or "").strip().lower()
    normalized_mailbox = str(mailbox or "").strip().lower()
    if not normalized_provider or not normalized_mailbox:
        raise RuntimeError("provider and mailbox are required for mail synchronization")
    return normalized_provider, normalized_mailbox, f"{normalized_provider}:{normalized_mailbox}"


def _tracking_id(row: dict[str, Any]) -> int | None:
    value = row.get("tracking_id", row.get("id"))
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _tracking_job_id(row: dict[str, Any]) -> int | None:
    value = row.get("job_id", row.get("platform_job_id"))
    if value is None and isinstance(row.get("job"), dict):
        value = row["job"].get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _tracking_status(row: dict[str, Any]) -> str:
    value = row.get("status", row.get("current_status", row.get("application_status")))
    return str(value or "").strip().lower()


def _fresh_tracking() -> list[dict[str, Any]]:
    return _call("GET", "/api/v1/agent/tracking")["rows"]


def _find_tracking_by_id(rows: list[dict[str, Any]], tracking_id: int) -> dict[str, Any] | None:
    return next((row for row in rows if _tracking_id(row) == tracking_id), None)


def _find_tracking_by_job(rows: list[dict[str, Any]], job_id: int) -> dict[str, Any] | None:
    return next((row for row in rows if _tracking_job_id(row) == job_id), None)


# Application stages, matching the App's state machine (core.constants.ApplicationStatus):
#   applied -> assessment | interview | rejected
#   assessment -> interview | rejected
#   interview -> offer | no_offer        (after an interview the negative outcome is no_offer, NOT rejected)
#   offer <-> no_offer                   (the only pair that may be flipped back and forth)
#   rejected                             (terminal; only reachable before an interview)
# "applied" is never sent by an agent: mark_applied creates it, and only the user can Reset a record.
_SETTABLE_STATUSES = ("assessment", "interview", "offer", "no_offer", "rejected")
_STATUSES_AFTER_INTERVIEW = {"interview", "offer", "no_offer"}


def _status_is_no_op(current: str, requested: str) -> bool:
    """True when the record is already at, or past, the requested stage, so nothing needs writing."""
    if current == requested:
        return True
    if requested == "assessment" and current in _STATUSES_AFTER_INTERVIEW:
        return True
    if requested == "interview" and current in {"offer", "no_offer"}:
        return True
    return False


mcp = MCPServer(
    name="jobmatchflow",
    instructions=(
        "For every new application pulse, first ask the user to confirm JobMatchFlow Basic Info, "
        "Experience, and resume files are current; then call refresh_application_cache exactly once. "
        "Reuse that snapshot for the pulse and refresh again only if the user says data changed. "
        "Use cached resume local_path files for ATS uploads; their filenames exactly match cv_name. "
        "Basic Info is authoritative for form identity. Check tracking before submission, save generated "
        "cover-letter content to JobMatchFlow, and call mark_applied only after visible success. The App "
        "owns submission idempotency and automatically snapshots the current CV, Cover Letter, JD, score, "
        "and notes at mark time. Use application snapshot tools for later interview preparation. Do not "
        "treat an already-recorded application or later status as an error. Mail checkpoints are local read "
        "anchors only. When advancing a status, add relevant feedback without deleting existing notes. Do not "
        "install or create alternative JobMatchFlow clients. Never store ATS passwords in notes."
    ),
)


@mcp.tool()
def start_device_authorization() -> dict[str, Any]:
    """Start first-use authorization and return a verification link and user code."""
    global pending_device_code
    if TOKEN:
        return {"already_authorized": True}
    label = f"{platform.node()} (JobMatchFlow)"
    response = session.post(
        f"{API_BASE}/api/v1/agent/device/start",
        json={"label": label},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    pending_device_code = data["device_code"]
    user_code = str(data["user_code"]).strip()
    if not user_code:
        raise RuntimeError("JobMatchFlow returned an empty device authorization code")
    return {
        # Build the browser URL locally. The web app is mounted under /app; using the
        # API-provided legacy /agent-authorize URL would hit the FastAPI 404 handler.
        "verification_uri": f"{AUTHORIZATION_PAGE}?code={quote(user_code, safe='')}",
        "user_code": user_code,
        "expires_in": data["expires_in"],
    }


@mcp.tool()
def finish_device_authorization() -> dict[str, Any]:
    """Poll once after the user approves the displayed device code."""
    global pending_device_code
    if TOKEN:
        return {"authorized": True, "already_authorized": True}
    if not pending_device_code:
        raise RuntimeError("Call start_device_authorization before finishing authorization")
    response = session.post(
        f"{API_BASE}/api/v1/agent/device/poll",
        json={"device_code": pending_device_code},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    status = data.get("status")
    if status == "approved" and data.get("token"):
        pending_device_code = None
        _accept_token(data["token"])
        return {"authorized": True}
    if status in {"denied", "expired", "delivered"}:
        pending_device_code = None
    return {"authorized": False, "status": status}


@mcp.tool()
def get_mail_sync_checkpoint(provider: str, mailbox: str) -> dict[str, Any]:
    """Return the local last-read anchor for one webmail account; no email body is stored."""
    normalized_provider, normalized_mailbox, key = _mailbox_key(provider, mailbox)
    checkpoint = _read_mail_checkpoints().get(key)
    return {
        "found": checkpoint is not None,
        "provider": normalized_provider,
        "mailbox": normalized_mailbox,
        "local_only": True,
        "checkpoint_path": str(MAIL_CHECKPOINT_PATH.resolve()),
        "checkpoint": checkpoint,
    }


@mcp.tool()
def save_mail_sync_checkpoint(
    provider: str,
    mailbox: str,
    anchor_message_key: str,
    anchor_received_at: str | None = None,
    anchor_sender: str | None = None,
    anchor_subject: str | None = None,
) -> dict[str, Any]:
    """Advance a local webmail read anchor only after a scan completes successfully."""
    normalized_provider, normalized_mailbox, key = _mailbox_key(provider, mailbox)
    message_key = str(anchor_message_key or "").strip()
    if not message_key:
        raise RuntimeError("anchor_message_key is required after a successful mail scan")
    checkpoints = _read_mail_checkpoints()
    checkpoint = {
        "anchor_message_key": message_key,
        "anchor_received_at": str(anchor_received_at or "").strip() or None,
        "anchor_sender": str(anchor_sender or "").strip() or None,
        "anchor_subject": str(anchor_subject or "").strip() or None,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    checkpoints[key] = checkpoint
    _write_mail_checkpoints(checkpoints)
    return {
        "saved": True,
        "provider": normalized_provider,
        "mailbox": normalized_mailbox,
        "local_only": True,
        "checkpoint_path": str(MAIL_CHECKPOINT_PATH.resolve()),
        "checkpoint": checkpoint,
    }


@mcp.tool()
def refresh_application_cache() -> dict[str, Any]:
    """Refresh one local snapshot of profile, jobs, tracking, and all resume files."""
    global cache_created_at, cache_dir
    global cached_context, cached_jobs, cached_tracking, cached_resumes, cached_resume_files

    created_at = datetime.now(timezone.utc)
    snapshot_dir = CACHE_ROOT / created_at.strftime("snapshot-%Y%m%d-%H%M%S-%f")
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    context = _call("GET", "/api/v1/agent/experience-context")
    jobs = _call("GET", "/api/v1/agent/jobs")["jobs"]
    tracking = _call("GET", "/api/v1/agent/tracking")["rows"]
    resumes = _call("GET", "/api/v1/agent/resumes")["resumes"]

    resume_files: dict[str, dict[str, Any]] = {}
    for resume in resumes:
        slot = str(resume.get("slot") or "").strip()
        if not slot:
            continue
        payload = _call("GET", f"/api/v1/agent/resumes/{slot}/download")
        resume_files[slot] = _store_resume(resume, payload, snapshot_dir)

    _write_json(snapshot_dir / "experience-context.json", context)
    _write_json(snapshot_dir / "jobs.json", jobs)
    _write_json(snapshot_dir / "tracking.json", tracking)
    _write_json(snapshot_dir / "resumes.json", resumes)

    cache_created_at = created_at.isoformat()
    cache_dir = snapshot_dir
    cached_context = context
    cached_jobs = jobs
    cached_tracking = tracking
    cached_resumes = resumes
    cached_resume_files = resume_files

    manifest = {
        "cached_at": cache_created_at,
        "cache_dir": str(snapshot_dir.resolve()),
        "experience_context_path": str((snapshot_dir / "experience-context.json").resolve()),
        "jobs_path": str((snapshot_dir / "jobs.json").resolve()),
        "tracking_path": str((snapshot_dir / "tracking.json").resolve()),
        "resumes": list(resume_files.values()),
    }
    _write_json(snapshot_dir / "manifest.json", manifest)
    return {
        **manifest,
        "manifest_path": str((snapshot_dir / "manifest.json").resolve()),
        "job_count": len(jobs),
        "preparing_count": sum(1 for row in jobs if row.get("is_preparing")),
        "tracking_count": len(tracking),
        "resume_count": len(resume_files),
    }


@mcp.tool()
def list_jobs(offset: int = 0, limit: int = 50) -> dict[str, Any]:
    """Page through the user's job list (cached after a pulse refresh, otherwise fetched now).

    The full list can hold thousands of jobs, far more than fits in one answer, so it is returned
    `limit` at a time (default 50, at most 200) with `total` and `next_offset` (null on the last
    page). Order is the App's own: AI "Best" matches first, then Good, then Partial; higher score
    first within each. Read as many pages as the task needs and stop early when scores drop below
    what the user cares about.

    Each job carries: title, company, location, score and decision, `list_group` (1 Best, 2 Good,
    3 Partial), `intent` (the App's AI verdict: fit, want, good[], watch_out[]; null for free users
    and users without a preference interview, who are ranked by score only), salary, contact,
    company_info (industry, size, website, linkedin, address), work_permit_required,
    visa_sponsorship_offered, required_languages, required_degree, remote_mode, employment_type,
    seniority_band, job_url_direct, is_preparing (shown as Saved in the App) and user_dismissed
    (shown as Not for me). Use get_job_detail for the full description and requirements."""
    jobs = cached_jobs if cached_jobs is not None else _call("GET", "/api/v1/agent/jobs")["jobs"]
    start = max(0, int(offset))
    size = max(1, min(int(limit), 200))
    page = jobs[start : start + size]
    end = start + len(page)
    return {
        "total": len(jobs),
        "offset": start,
        "limit": size,
        "next_offset": end if end < len(jobs) else None,
        "jobs": page,
    }


@mcp.tool()
def get_job_detail(job_id: int) -> dict[str, Any]:
    """Return one job's full description, requirements (skills with required/preferred, core work,
    seniority, minimum years), company description, contact, salary, visa signals and the App's match details."""
    return _call("GET", f"/api/v1/agent/jobs/{job_id}")


@mcp.tool()
def triage_job(job_id: int, action: str) -> dict[str, Any]:
    """Mark one Jobs List entry as preparing, dismiss, or clear both."""
    normalized = str(action or "").strip().lower()
    if normalized not in {"preparing", "dismiss", "clear"}:
        raise RuntimeError("action must be preparing, dismiss, or clear")
    result = _call(
        "POST", f"/api/v1/agent/jobs/{job_id}/triage", json={"action": normalized}
    )
    _invalidate("jobs")
    return result


@mcp.tool()
def get_experience_context() -> dict[str, Any]:
    """Return cached Basic Info, experience, skills, and saved answers when available."""
    return cached_context if cached_context is not None else _call("GET", "/api/v1/agent/experience-context")


@mcp.tool()
def list_tracking() -> list[dict[str, Any]]:
    """List cached applications for duplicate checks, otherwise fetch current tracking."""
    return cached_tracking if cached_tracking is not None else _call("GET", "/api/v1/agent/tracking")["rows"]


@mcp.tool()
def list_resumes() -> list[dict[str, Any]]:
    """List resume slots; a pulse refresh also downloads their files locally."""
    return cached_resumes if cached_resumes is not None else _call("GET", "/api/v1/agent/resumes")["resumes"]


@mcp.tool()
def download_resume(slot: str) -> dict[str, Any]:
    """Return a cached local resume path whose filename exactly matches App cv_name."""
    global cached_resumes
    if slot in cached_resume_files:
        return cached_resume_files[slot]
    resumes = cached_resumes or _call("GET", "/api/v1/agent/resumes")["resumes"]
    resume = next((row for row in resumes if row.get("slot") == slot), None)
    if not resume:
        raise RuntimeError(f"Unknown resume slot: {slot}")
    target_dir = cache_dir or (CACHE_ROOT / "on-demand")
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = _call("GET", f"/api/v1/agent/resumes/{slot}/download")
    stored = _store_resume(resume, payload, target_dir)
    cached_resume_files[slot] = stored
    return stored


@mcp.tool()
def save_cover_letter_content(job_id: int, paragraphs: list[str]) -> dict[str, Any]:
    """Save generated cover-letter paragraphs back to a platform job."""
    return _call(
        "POST",
        f"/api/v1/agent/jobs/{job_id}/cover-letter",
        json={"paragraphs": paragraphs},
    )


@mcp.tool()
def upload_tailored_resume(
    job_id: int,
    local_path: str,
    filename: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    """Upload one locally verified tailored PDF or DOCX using the App material model."""
    path = Path(local_path).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"Tailored resume file does not exist: {path}")
    upload_name = _safe_exact_filename(filename or path.name)
    size = path.stat().st_size
    if size <= 0:
        raise RuntimeError("The tailored resume file is empty")
    if size > MAX_APPLICATION_MATERIAL_BYTES:
        raise RuntimeError("The tailored resume file exceeds the 15 MB upload limit")
    content = path.read_bytes()
    mime_type = _application_material_mime(upload_name, content)
    result = _call(
        "POST",
        f"/api/v1/agent/jobs/{job_id}/tailored-resumes",
        files={"file": (upload_name, content, mime_type)},
        data={"summary": str(summary or "")},
    )
    if not isinstance(result, dict):
        raise RuntimeError("JobMatchFlow returned an invalid tailored resume response")
    returned_choice = str(result.get("resume_choice") or "tailored").strip().lower()
    if returned_choice != "tailored":
        raise RuntimeError(
            "JobMatchFlow returned an incompatible resume_choice for the tailored resume"
        )
    return {**result, "resume_choice": "tailored"}


@mcp.tool()
def upload_tailored_cover_letter(
    job_id: int,
    local_path: str,
    filename: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    """Upload one locally verified standard DOCX or tailored PDF Cover Letter."""
    path = Path(local_path).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"Tailored Cover Letter file does not exist: {path}")
    upload_name = _safe_exact_filename(filename or path.name)
    size = path.stat().st_size
    if size <= 0:
        raise RuntimeError("The tailored Cover Letter file is empty")
    if size > MAX_APPLICATION_MATERIAL_BYTES:
        raise RuntimeError("The tailored Cover Letter file exceeds the 15 MB upload limit")
    content = path.read_bytes()
    mime_type = _application_material_mime(upload_name, content)
    return _call(
        "POST",
        f"/api/v1/agent/jobs/{job_id}/tailored-cover-letters",
        files={"file": (upload_name, content, mime_type)},
        data={"summary": str(summary or "")},
    )


@mcp.tool()
def mark_applied(job_id: int, resume_choice: str) -> dict[str, Any]:
    """Mark visible success using an App resume slot or an uploaded tailored-resume reference."""
    existing = _find_tracking_by_job(_fresh_tracking(), job_id)
    if existing:
        return {
            "updated": False,
            "no_op": True,
            "reason": "application_already_recorded",
            "tracking_id": _tracking_id(existing),
            "tracking": existing,
        }
    try:
        result = _call(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/mark-applied",
            json={"resume_choice": resume_choice},
        )
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 409:
            raise
        existing = _find_tracking_by_job(_fresh_tracking(), job_id)
        if not existing:
            raise
        return {
            "updated": False,
            "no_op": True,
            "reason": "application_already_recorded",
            "tracking_id": _tracking_id(existing),
            "tracking": existing,
        }
    _invalidate("jobs", "tracking")
    return result


@mcp.tool()
def get_application_context(tracking_id: int) -> dict[str, Any]:
    """Read the App-frozen application snapshot used for later interview preparation."""
    result = _call("GET", f"/api/v1/agent/tracking/{tracking_id}/snapshot")
    if not isinstance(result, dict):
        raise RuntimeError("JobMatchFlow returned an invalid application snapshot")
    return result


@mcp.tool()
def download_application_material(
    tracking_id: int, material_type: str
) -> dict[str, Any]:
    """Download a mark-time resume or Cover Letter snapshot and preserve its App filename."""
    normalized_type = str(material_type or "").strip().lower()
    if normalized_type not in {"resume", "cover_letter"}:
        raise RuntimeError("material_type must be resume or cover_letter")
    payload = _call(
        "GET",
        f"/api/v1/agent/tracking/{tracking_id}/snapshot/materials/{normalized_type}/download",
    )
    if not isinstance(payload, dict):
        raise RuntimeError("JobMatchFlow returned an invalid application material response")
    return _store_application_material(tracking_id, normalized_type, payload)


@mcp.tool()
def update_application_status(
    tracking_id: int, status: str, notes: str | None = None
) -> dict[str, Any]:
    """Advance status idempotently and append notes when a real stage change occurs.

    status is one of assessment, interview, offer, no_offer, rejected. rejected is only for a
    rejection BEFORE an interview; once the user has interviewed, a negative outcome is no_offer.
    offer and no_offer may be switched back and forth; every other move only goes forward. The
    App shows "Screening" for everything that is applied and not rejected, so do not invent it as
    a status. Resetting a record is a user action, not available here."""
    requested = str(status or "").strip().lower()
    if requested not in _SETTABLE_STATUSES:
        raise RuntimeError("status must be one of: " + ", ".join(_SETTABLE_STATUSES))
    current_row = _find_tracking_by_id(_fresh_tracking(), tracking_id)
    current = _tracking_status(current_row) if current_row else ""
    if requested == "rejected" and current in _STATUSES_AFTER_INTERVIEW:
        raise RuntimeError(
            "This application already reached the interview stage, so a negative outcome is recorded "
            "as no_offer, not rejected."
        )
    if current_row and _status_is_no_op(current, requested):
        return {
            "updated": False,
            "no_op": True,
            "reason": "status_already_equal_or_later",
            "requested_status": requested,
            "current_status": current,
            "tracking_id": tracking_id,
            "tracking": current_row,
            "notes_not_written": bool(notes),
        }
    try:
        result = _call(
            "POST",
            f"/api/v1/agent/tracking/{tracking_id}/status",
            json={"status": requested, "notes": notes},
        )
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 409:
            raise
        refreshed = _find_tracking_by_id(_fresh_tracking(), tracking_id)
        refreshed_status = _tracking_status(refreshed) if refreshed else ""
        if not refreshed or not _status_is_no_op(refreshed_status, requested):
            raise
        return {
            "updated": False,
            "no_op": True,
            "reason": "status_already_equal_or_later",
            "requested_status": requested,
            "current_status": refreshed_status,
            "tracking_id": tracking_id,
            "tracking": refreshed,
            "notes_not_written": bool(notes),
        }
    _invalidate("tracking")
    return result


@mcp.tool()
def add_application_note(tracking_id: int, note: str) -> dict[str, Any]:
    """Append one application event without changing status or replacing existing notes."""
    normalized_note = str(note or "").strip()
    if not normalized_note:
        raise RuntimeError("note must not be empty")
    result = _call(
        "POST",
        f"/api/v1/agent/tracking/{tracking_id}/note",
        json={"note": normalized_note},
    )
    _invalidate("tracking")
    return result


@mcp.tool()
def create_manual_tracking(
    url: str,
    title: str | None = None,
    company: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Record an externally discovered application after visible success."""
    result = _call(
        "POST",
        "/api/v1/agent/tracking/manual",
        json={"url": url, "title": title, "company": company, "notes": notes},
    )
    _invalidate("tracking")
    return result


@mcp.tool()
def save_agent_answer(key: str, value: str) -> dict[str, Any]:
    """Save one reusable generated answer for frontend editing."""
    result = _call(
        "POST",
        "/api/v1/agent/agent-answers",
        json={"key": key, "value": value},
    )
    _invalidate("context")
    return result


def main() -> None:
    if TOKEN:
        print("[jobmatchflow] Authorization available", file=sys.stderr)
    else:
        print("[jobmatchflow] Authorization required", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
