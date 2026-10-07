"""Merge the jobfishing app's own scored list with locally scored jobs into one ranking."""

from __future__ import annotations


def merge_rank(local: list[dict], hosted: list[dict], limit: int = 30, min_score: float = 0) -> list[dict]:
    """Both lists carry a 0-100 `score` from the same formula, so they sort on one scale. `source` says where a job came from.

    Hosted rows are the app's `list_jobs` items; local rows are `store.list_jobs(scored=True)` items. Discarded jobs and rows
    without a score are left out."""
    rows = []
    for src, items in (("jobfishing", hosted), ("local", local)):
        for j in items:
            sc = j.get("score")
            if sc is None or j.get("decision") == "discard" or sc < min_score:
                continue
            rows.append({"source": src, "id": j.get("id"), "title": j.get("title"), "company": j.get("company"),
                         "location": j.get("location"), "score": sc, "decision": j.get("decision"),
                         "url": j.get("job_url_direct") or j.get("url")})
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:limit]
