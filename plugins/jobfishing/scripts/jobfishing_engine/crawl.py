"""Parallel crawl on top of python-jobspy. The agent picks terms, places and the time window; this runs them at once.

No dedup, no cleaning beyond mapping columns: (site, url) uniqueness in the store is the only filter.
"""

from __future__ import annotations

import itertools
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import store

SITES = ("linkedin", "indeed")
DISTANCE_MILES = 22  # ~35 km, the radius the jobfishing crawler uses around a city


def _one(site: str, term: str, place: str, country: str | None, hours_old: int | None, wanted: int, distance: int):
    from jobspy import scrape_jobs  # imported late: pandas is slow to load and not needed for reads

    time.sleep(random.uniform(0.0, 1.5))  # spread the first requests so a burst does not look like one
    kw = dict(site_name=[site], search_term=term, location=place, results_wanted=wanted, hours_old=hours_old,
              distance=distance, linkedin_fetch_description=site == "linkedin")
    if country and site == "indeed":
        kw["country_indeed"] = country
    return scrape_jobs(**kw)


def _row(r, site: str, term: str) -> dict:
    def s(v):
        return None if v is None or v != v else str(v)  # v != v catches NaN
    lo, hi, cur = s(r.get("min_amount")), s(r.get("max_amount")), s(r.get("currency")) or ""
    return {"site": s(r.get("site")) or site, "url": s(r.get("job_url")), "title": s(r.get("title")),
            "company": s(r.get("company")), "location": s(r.get("location")), "description": s(r.get("description")),
            "date_posted": s(r.get("date_posted")), "job_type": s(r.get("job_type")),
            "salary": f"{lo or ''}-{hi or ''} {cur}".strip(" -") if (lo or hi) else None,
            "is_remote": r.get("is_remote") if r.get("is_remote") == r.get("is_remote") else None, "search_term": term}


def crawl(terms: list[str], places: list[str], *, sites: tuple[str, ...] = SITES, hours_old: int | None = 72,
          per_search: int = 30, country: str | None = None, workers: int = 6, distance: int = DISTANCE_MILES) -> dict:
    """Run every (term x place x site) search in parallel threads and store what comes back."""
    jobs = list(itertools.product(sites, terms, places))
    rows: list[dict] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(jobs) or 1))) as pool:
        futs = {pool.submit(_one, s, t, p, country, hours_old, per_search, distance): (s, t, p) for s, t, p in jobs}
        for f in as_completed(futs):
            s, t, p = futs[f]
            try:
                df = f.result()
                rows.extend(_row(r, s, t) for _, r in df.iterrows())
            except Exception as e:  # one blocked site must not lose the other results
                errors.append(f"{s} / {t} / {p}: {type(e).__name__}: {str(e)[:120]}")
    res = store.upsert_jobs(rows)
    return {"searches": len(jobs), **res, "errors": errors[:10], "error_count": len(errors)}
