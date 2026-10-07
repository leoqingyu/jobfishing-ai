"""Parallel crawl on top of python-jobspy. The agent picks terms, places and the time window; this runs them at once.

No dedup, no cleaning beyond mapping columns: (site, url) uniqueness in the store is the only filter.
"""

from __future__ import annotations

import itertools
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import store

SITES = ("linkedin", "indeed")
DISTANCE_MILES = 22  # ~35 km, the radius the jobfishing crawler uses around a city
MAX_PER_SEARCH = 300  # jobspy pages on its own (LinkedIn stops near 1000 results); this is our own ceiling
DEFAULT_PER_SEARCH = 100


def _one(site: str, term: str, place: str, country: str | None, hours_old: int | None, wanted: int, distance: int):
    from jobspy import scrape_jobs  # imported late: pandas is slow to load and not needed for reads

    time.sleep(random.uniform(0.0, 1.5))  # spread the first requests so a burst does not look like one
    kw = dict(site_name=[site], search_term=term, location=place, results_wanted=wanted, hours_old=hours_old,
              distance=distance, linkedin_fetch_description=False)  # LinkedIn: titles first, text later (fetch_descriptions)
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
          per_search: int = DEFAULT_PER_SEARCH, country: str | None = None, workers: int = 6, distance: int = DISTANCE_MILES) -> dict:
    """Run every (term x place x site) search in parallel threads and store what comes back."""
    per_search = max(1, min(int(per_search), MAX_PER_SEARCH))
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


# ---- LinkedIn job text, second stage -----------------------------------------------------------------------------------
# The jobfishing app does it in two steps too: crawl the listing (titles only, cheap), then fetch the text of the jobs worth it
# from a separate worker. Here the agent picks the jobs from the titles, then calls fetch_descriptions for just those.

RATE_LIMIT_HINT = (
    "LinkedIn is limiting requests from this connection. Wait a few minutes and call fetch_descriptions again for the rest. "
    "The jobfishing app crawls LinkedIn continuously with its own proxies, so for Switzerland, Luxembourg, Frankfurt, Munich, "
    "Stuttgart, Amsterdam and Rotterdam its job list already has these jobs, with full text."
)
_LI_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "accept-language": "en-US,en;q=0.9",
    "accept": "text/html,application/xhtml+xml",
}
MIN_DESCRIPTION = 120  # shorter than this is not a real posting text (the app uses the same bar)


def linkedin_job_id(url: str | None) -> str | None:
    m = re.search(r"/jobs/view/(?:[^/?#]*-)?(\d{6,})", url or "")
    return m.group(1) if m else None


def _fetch_text(session, job_id: str) -> tuple[str, str | None]:
    """-> (status, text): status is ok | empty | rate_limited | blocked."""
    from bs4 import BeautifulSoup
    from markdownify import markdownify

    try:
        r = session.get(f"https://www.linkedin.com/jobs/view/{job_id}", timeout=15, allow_redirects=True)
    except Exception:
        return "blocked", None
    if r.status_code in (429, 999):
        return "rate_limited", None
    if r.status_code != 200 or "authwall" in r.url or "linkedin.com/signup" in r.url:
        return "blocked", None
    box = BeautifulSoup(r.text, "html.parser").find("div", class_=lambda c: c and "show-more-less-html__markup" in c)
    if box is None:
        return "empty", None
    text = markdownify(str(box)).strip()
    return ("ok", text) if len(text) >= MIN_DESCRIPTION else ("empty", None)


def fetch_descriptions(job_ids: list[int], *, workers: int = 3) -> dict:
    """Fetch the posting text of the given LinkedIn jobs and store it. Deliberately gentle (few threads, random pauses):
    there is no proxy here, and LinkedIn limits one address quickly. The first sign of a limit stops the whole batch."""
    import requests

    todo = []
    with store.connect() as con:
        for jid in dict.fromkeys(int(i) for i in job_ids):
            row = con.execute("SELECT id, site, url, description FROM jobs WHERE id=?", (jid,)).fetchone()
            if row is None or len(row["description"] or "") >= MIN_DESCRIPTION:
                continue  # unknown, or it already has its text
            lid = linkedin_job_id(row["url"]) if row["site"] == "linkedin" else None
            if lid:
                todo.append((jid, lid))
    stop = threading.Event()
    out: dict[int, str] = {}
    session = requests.Session()
    session.headers.update(_LI_HEADERS)

    def work(item):
        jid, lid = item
        if stop.is_set():
            return jid, "skipped", None
        time.sleep(random.uniform(0.8, 2.0))
        status, text = _fetch_text(session, lid)
        if status in ("rate_limited", "blocked"):
            stop.set()
        return jid, status, text

    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        for jid, status, text in pool.map(work, todo):
            out[jid] = status
            if status == "ok":
                store.set_description(jid, text)
    count = lambda k: sum(1 for v in out.values() if v == k)  # noqa: E731
    limited = stop.is_set()
    res = {"requested": len(job_ids), "fetched": count("ok"), "no_text_on_page": count("empty"),
           "not_attempted": count("skipped"), "rate_limited": limited}
    if limited:
        res["retry_ids"] = [j for j, v in out.items() if v in ("skipped", "rate_limited", "blocked")]
        res["message"] = RATE_LIMIT_HINT
    return res
