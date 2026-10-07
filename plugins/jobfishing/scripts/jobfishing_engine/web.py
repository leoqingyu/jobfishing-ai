"""Local dashboard: a tiny stdlib HTTP server over the SQLite store plus one static page. Loopback only, no dependencies.

The agent writes scores into SQLite; the page polls the counts and refreshes, so both always show the same state.
"""

from __future__ import annotations

import json
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import crawl as _crawl, rank as _rank, scoring, store

STATIC = Path(__file__).with_name("static")
PORTS = range(8765, 8786)

_lock = threading.Lock()
_server: ThreadingHTTPServer | None = None
_url: str | None = None
_crawl_state: dict = {"running": False, "result": None, "started": None}


def _agent_prompt(n: int) -> str:
    return (f"Use $jobfishing-rank to score my {n} unscored local jobs. If I'm signed in to jobfishing, score against my jobfishing "
            "profile (get_scoring_profile): it is more complete than a CV. If I'm not signed in, or have no profile there, tell me "
            "that in one sentence and fall back to my CV. Score in parallel batches, save the scores, then tell me the top matches. "
            "The jobfishing dashboard updates by itself.")


def _recommend(hosted_fetch, limit: int, min_score: float) -> dict:
    hosted, note = [], None
    if hosted_fetch is not None:
        try:
            hosted = hosted_fetch()
        except Exception as e:  # not signed in or offline: local-only is a valid answer
            note = "Sign in to jobfishing to merge your jobfishing matches into this list."
    else:
        note = "Open the dashboard from your agent (open_dashboard) to merge your jobfishing matches."
    local = store.list_jobs(scored=True, limit=1000)
    return {"jobs": _rank.merge_rank(local, hosted, limit=limit, min_score=min_score), "note": note,
            "hosted_included": bool(hosted)}


def _make_handler(port: int, hosted_fetch):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class H(BaseHTTPRequestHandler):
        server_version = "jobfishing"

        def log_message(self, *a):  # quiet: stdout belongs to MCP stdio in the agent process
            pass

        def _send(self, code: int, body: bytes, ctype: str = "application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") or "json" in ctype else ""))
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
                                                       "frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode())

        def _host_ok(self) -> bool:
            # Blocks DNS-rebinding: a page on another origin can resolve to 127.0.0.1 but keeps its own Host header.
            return (self.headers.get("Host") or "") in allowed_hosts

        def do_GET(self):
            if not self._host_ok():
                return self._json({"error": "bad host"}, 403)
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path in ("/", "/index.html"):
                    return self._send(200, (STATIC / "index.html").read_bytes(), "text/html")
                if u.path == "/api/counts":
                    return self._json({**store.counts(), "crawl_running": _crawl_state["running"]})
                if u.path == "/api/jobs":
                    ms = q.get("min_score")
                    return self._json(store.search_jobs(
                        q=q.get("q", ""), scored=q.get("scored", "all"), min_score=float(ms) if ms else None,
                        sort=q.get("sort", "score"), limit=int(q.get("limit", 100)), offset=int(q.get("offset", 0))))
                if u.path.startswith("/api/jobs/"):
                    job = store.get_job(int(u.path.rsplit("/", 1)[1]))
                    if job is None:
                        return self._json({"error": "not found"}, 404)
                    if job.get("judgment"):
                        job["judgment"] = json.loads(job["judgment"])
                        job["breakdown"] = scoring.aggregate(job["judgment"])  # same numbers the score was made from
                    return self._json(job)
                if u.path == "/api/recommend":
                    return self._json(_recommend(hosted_fetch, int(q.get("limit", 30)), float(q.get("min_score", 60))))
                if u.path == "/api/crawl":
                    return self._json(_crawl_state)
                if u.path == "/api/prompt":
                    return self._json({"prompt": _agent_prompt(store.counts()["ready"])})
                return self._json({"error": "not found"}, 404)
            except (ValueError, KeyError) as e:
                return self._json({"error": str(e)}, 400)

        def do_POST(self):
            # A custom header cannot be sent cross-origin without a CORS preflight, which this server never answers.
            if not self._host_ok() or self.headers.get("X-Jobfishing") != "1":
                return self._json({"error": "forbidden"}, 403)
            if urlparse(self.path).path != "/api/crawl":
                return self._json({"error": "not found"}, 404)
            try:
                body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 65536)) or b"{}")
                terms = [str(t).strip() for t in body.get("terms", []) if str(t).strip()][:10]
                places = [str(t).strip() for t in body.get("places", []) if str(t).strip()][:6]
                if not terms or not places:
                    return self._json({"error": "give at least one job title and one place"}, 400)
                sites = tuple(x for x in body.get("sites", _crawl.SITES) if x in _crawl.SITES) or _crawl.SITES
                kw = dict(sites=sites, hours_old=int(body.get("hours_old", 72)), country=(body.get("country") or None),
                          per_search=max(1, min(int(body.get("per_search", _crawl.DEFAULT_PER_SEARCH)), _crawl.MAX_PER_SEARCH)))
            except (ValueError, TypeError) as e:
                return self._json({"error": f"bad request: {e}"}, 400)
            with _lock:
                if _crawl_state["running"]:
                    return self._json({"error": "a crawl is already running"}, 409)
                _crawl_state.update(running=True, result=None, started=time.time())

            def run():
                try:
                    res = _crawl.crawl(terms, places, **kw)
                except Exception as e:
                    res = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
                with _lock:
                    _crawl_state.update(running=False, result=res)

            threading.Thread(target=run, daemon=True).start()
            return self._json({"started": True}, 202)

    return H


def serve(hosted_fetch=None, *, open_browser: bool = False) -> str:
    """Start the dashboard once per process (a daemon thread) and return its URL; later calls return the same URL."""
    global _server, _url
    with _lock:
        if _server is None:
            for port in PORTS:
                try:
                    srv = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(port, hosted_fetch))
                except OSError:
                    continue
                threading.Thread(target=srv.serve_forever, daemon=True).start()
                _server, _url = srv, f"http://127.0.0.1:{port}/"
                break
            else:
                raise RuntimeError("no free port between 8765 and 8785 for the jobfishing dashboard")
    if open_browser:
        webbrowser.open(_url)
    return _url


def main() -> None:
    """`jobfishing-ui`: the dashboard without an agent (local data only)."""
    url = serve(None, open_browser=True)
    print(f"jobfishing dashboard: {url}  (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
