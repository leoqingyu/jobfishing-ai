"""SQLite store: jobs and scores only. Tracking, resumes and applications live in the jobfishing app, not here."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .scoring import aggregate


def home() -> Path:
    p = Path(os.environ.get("JOBFISHING_HOME") or Path.home() / ".jobfishing")
    p.mkdir(parents=True, exist_ok=True)
    return p


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  site TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT, company TEXT, location TEXT, country TEXT,
  description TEXT, date_posted TEXT, salary TEXT, job_type TEXT, is_remote INTEGER,
  search_term TEXT, created_at REAL NOT NULL,
  cleared_at REAL,
  UNIQUE (site, url)
);
CREATE TABLE IF NOT EXISTS scores (
  job_id INTEGER PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
  total REAL NOT NULL, decision TEXT NOT NULL,
  qualification REAL, role REAL, seniority REAL, domain REAL,
  judgment TEXT NOT NULL, overview TEXT, scored_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS scores_total ON scores(total DESC);
"""


@contextmanager
def connect(path: Path | None = None):
    con = sqlite3.connect(str(path or home() / "jobfishing.db"), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")  # the UI reads while the agent writes
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    if "cleared_at" not in {r[1] for r in con.execute("PRAGMA table_info(jobs)")}:  # a database from before "clear" existed
        con.execute("ALTER TABLE jobs ADD COLUMN cleared_at REAL")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def upsert_jobs(rows: list[dict]) -> dict:
    """Insert crawled rows. (site, url) is the only uniqueness: anything smarter is the agent's call."""
    new = 0
    with connect() as con:
        for r in rows:
            if not r.get("url"):
                continue
            cur = con.execute(
                "INSERT OR IGNORE INTO jobs (site,url,title,company,location,country,description,date_posted,salary,job_type,"
                "is_remote,search_term,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r.get("site") or "", r["url"], r.get("title"), r.get("company"), r.get("location"), r.get("country"),
                 r.get("description"), r.get("date_posted"), r.get("salary"), r.get("job_type"),
                 None if r.get("is_remote") is None else int(bool(r["is_remote"])), r.get("search_term"), time.time()),
            )
            new += cur.rowcount
    return {"received": len(rows), "new": new}


def list_jobs(*, scored: bool | None = None, limit: int = 50, offset: int = 0, with_description: bool = False,
              has_description: bool | None = None) -> list[dict]:
    """has_description filters to jobs whose text has / has not been fetched yet (LinkedIn jobs arrive as titles only)."""
    cols = "j.*" if with_description else "j.id,j.site,j.url,j.title,j.company,j.location,j.country,j.date_posted,j.salary"
    conds = ["j.cleared_at IS NULL"]  # cleared jobs stay in the file but are out of every list
    if scored is not None:
        conds.append("s.job_id IS NOT NULL" if scored else "s.job_id IS NULL")
    if has_description is not None:
        conds.append(("length(coalesce(j.description,'')) >= 120") if has_description else "length(coalesce(j.description,'')) < 120")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    with connect() as con:
        rows = con.execute(
            f"SELECT {cols}, length(coalesce(j.description,'')) >= 120 AS has_description, s.total AS score, s.decision "
            f"FROM jobs j LEFT JOIN scores s ON s.job_id=j.id {where} "
            "ORDER BY j.created_at DESC, j.id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    return [dict(r) for r in rows]


def set_description(job_id: int, text: str) -> None:
    with connect() as con:
        con.execute("UPDATE jobs SET description=? WHERE id=?", (text, job_id))


def get_job(job_id: int) -> dict | None:
    with connect() as con:
        r = con.execute("SELECT j.*, s.total AS score, s.decision, s.judgment, s.overview FROM jobs j "
                        "LEFT JOIN scores s ON s.job_id=j.id WHERE j.id=?", (job_id,)).fetchone()
    return dict(r) if r else None


def save_scores(items: list[dict]) -> list[dict]:
    """items: [{job_id, skills, role_score, seniority_fit, domain_fit, overview?, *_reason?}] -> the aggregated scores.
    Several at once, so a parallel scoring pass writes one batch."""
    out = []
    with connect() as con:
        for it in items:
            jid = int(it["job_id"])
            if not con.execute("SELECT 1 FROM jobs WHERE id=?", (jid,)).fetchone():
                out.append({"job_id": jid, "error": "unknown job_id"})
                continue
            agg = aggregate(it)
            con.execute(
                "INSERT INTO scores (job_id,total,decision,qualification,role,seniority,domain,judgment,overview,scored_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET total=excluded.total,decision=excluded.decision,"
                "qualification=excluded.qualification,role=excluded.role,seniority=excluded.seniority,domain=excluded.domain,"
                "judgment=excluded.judgment,overview=excluded.overview,scored_at=excluded.scored_at",
                (jid, agg["total"], agg["decision"], agg.get("qualification"), agg.get("role"), agg.get("seniority"),
                 agg.get("domain"), json.dumps(it, ensure_ascii=False), it.get("overview"), time.time()))
            out.append({"job_id": jid, **agg})
    return out


def counts() -> dict:
    """Counts of what is still on the dashboard: cleared jobs are not counted anywhere."""
    live = "j.cleared_at IS NULL"
    with connect() as con:
        r = con.execute(
            f"SELECT (SELECT COUNT(*) FROM jobs j WHERE {live}) jobs, "
            f"(SELECT COUNT(*) FROM scores s JOIN jobs j ON j.id=s.job_id WHERE {live}) scored, "
            f"(SELECT COUNT(*) FROM jobs j WHERE {live} AND length(coalesce(j.description,'')) < 120) no_description, "
            f"(SELECT COUNT(*) FROM jobs j WHERE {live} AND length(coalesce(j.description,'')) >= 120 "
            "   AND NOT EXISTS (SELECT 1 FROM scores s WHERE s.job_id=j.id)) ready").fetchone()
    # unscored = every live job without a score; ready = those with their text, i.e. the ones that can be scored right now
    return {"jobs": r["jobs"], "scored": r["scored"], "unscored": r["jobs"] - r["scored"], "ready": r["ready"],
            "no_description": r["no_description"]}


def clear_all() -> int:
    """Take every job off the dashboard: scored or not, with or without text. Same soft clear as clear_jobs."""
    with connect() as con:
        return con.execute("UPDATE jobs SET cleared_at=? WHERE cleared_at IS NULL", [time.time()]).rowcount


def clear_jobs(ids: list[int]) -> int:
    """Take these jobs off the dashboard. The rows (and their scores) stay in the database file, and because (site, url) is
    unique, crawling the same posting again does not bring a cleared job back."""
    ids = [int(i) for i in ids][:500]
    if not ids:
        return 0
    with connect() as con:
        cur = con.execute(f"UPDATE jobs SET cleared_at=? WHERE cleared_at IS NULL AND id IN ({','.join('?' * len(ids))})",
                          [time.time(), *ids])
        return cur.rowcount


def get_preferences() -> str | None:
    f = home() / "preferences.md"
    return f.read_text(encoding="utf-8") if f.exists() else None


def save_preferences(profile: str) -> None:
    (home() / "preferences.md").write_text(profile, encoding="utf-8")


def search_jobs(*, q: str = "", scored: str = "all", min_score: float | None = None, sort: str = "score",
                limit: int = 100, offset: int = 0) -> dict:
    """The dashboard list: text search over title/company/location, scored filter, minimum score, sort by score or recency."""
    where, args = ["j.cleared_at IS NULL"], []
    for term in q.split():
        where.append("(j.title LIKE ? OR j.company LIKE ? OR j.location LIKE ?)")
        args += [f"%{term}%"] * 3
    if scored == "scored":
        where.append("s.job_id IS NOT NULL")
    elif scored == "unscored":
        where.append("s.job_id IS NULL")
    if min_score is not None:
        where.append("s.total >= ?")
        args.append(min_score)
    cond = ("WHERE " + " AND ".join(where)) if where else ""
    order = "s.total DESC NULLS LAST, j.created_at DESC" if sort == "score" else "j.created_at DESC, j.id DESC"
    base = f"FROM jobs j LEFT JOIN scores s ON s.job_id=j.id {cond}"
    with connect() as con:
        total = con.execute(f"SELECT COUNT(*) {base}", args).fetchone()[0]
        rows = con.execute(
            f"SELECT j.id,j.site,j.url,j.title,j.company,j.location,j.date_posted,j.salary,s.total AS score,s.decision,s.overview "
            f"{base} ORDER BY {order} LIMIT ? OFFSET ?", [*args, max(1, min(limit, 200)), max(0, offset)]).fetchall()
    return {"total": total, "jobs": [dict(r) for r in rows]}
