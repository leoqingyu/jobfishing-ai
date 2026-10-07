import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest

from jobfishing_engine import rank, scoring, store


@pytest.fixture(autouse=True)
def _home(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBFISHING_HOME", str(tmp_path))


def test_worked_example_matches_the_app():
    # python full(req), sql strong(req), airflow weak(pref); role 78, one_down, related -> 76.0 review
    j = {"skills": [{"importance": "required", "level": "full"}, {"importance": "required", "level": "strong"},
                    {"importance": "preferred", "level": "weak"}], "role_score": 78, "seniority_fit": "one_down", "domain_fit": "related"}
    r = scoring.aggregate(j)
    assert r["qualification"] == 74.3 and r["total"] == 76.0 and r["decision"] == "review"


def test_no_skills_is_neutral_and_missing_dimension_renormalises():
    assert scoring.qualification([]) == 60
    r = scoring.aggregate({"skills": [], "role_score": 100})  # seniority/domain missing
    assert r["total"] == round((60 * 0.30 + 100 * 0.40) / 0.70, 1)


def test_unknown_labels_never_raise():
    r = scoring.aggregate({"skills": [{"level": "bogus"}], "role_score": "x", "seniority_fit": "??"})
    assert r["qualification"] == 0 and r["role"] == 0 and r["seniority"] == 0   # present but unusable = 0, like the app


def test_store_roundtrip_and_url_uniqueness():
    rows = [{"site": "indeed", "url": "https://x/1", "title": "A", "company": "C"},
            {"site": "indeed", "url": "https://x/1", "title": "A again"}, {"site": "linkedin", "url": ""}]
    assert store.upsert_jobs(rows) == {"received": 3, "new": 1}
    [job] = store.list_jobs(scored=False)
    out = store.save_scores([{"job_id": job["id"], "skills": [], "role_score": 90, "seniority_fit": "match", "domain_fit": "same"},
                             {"job_id": 999}])
    assert out[0]["decision"] == "generate" and out[1]["error"]
    assert store.counts() == {"jobs": 1, "scored": 1, "unscored": 0, "ready": 0, "no_description": 1}
    assert store.get_job(job["id"])["score"] == out[0]["total"]


def test_merge_rank_one_scale():
    hosted = [{"id": 1, "title": "H", "score": 88, "decision": "generate"}, {"id": 2, "score": 95, "decision": "discard"}]
    local = [{"id": 7, "title": "L", "score": 91, "decision": "generate", "url": "u"}]
    assert [(r["source"], r["id"]) for r in rank.merge_rank(local, hosted)] == [("local", 7), ("jobfishing", 1)]


def test_mcp_exposes_local_tools_and_recommend_works_offline():
    pytest.importorskip("mcp")
    import jobfishing_mcp_server as m
    m._store.upsert_jobs([{"site": "indeed", "url": "u1", "title": "T", "company": "C"}])
    [res] = m.save_scores([{"job_id": 1, "skills": [], "role_score": 90, "seniority_fit": "match", "domain_fit": "same"}])
    assert res["decision"] == "generate"
    out = m.recommend(min_score=0, include_jobfishing=False)
    assert [r["source"] for r in out["jobs"]] == ["local"]


def test_local_preferences_roundtrip():
    assert store.get_preferences() is None
    store.save_preferences("Zurich, data roles, no relocation")
    assert store.get_preferences() == "Zurich, data roles, no relocation"


# ---- dashboard server ------------------------------------------------------------------------------------------------

import http.client
import json as _json


@pytest.fixture
def dash(monkeypatch):
    from jobfishing_engine import web
    web._server = None
    url = web.serve(lambda: [{"id": 5, "title": "Hosted", "score": 90, "decision": "generate", "job_url_direct": "https://h"}])
    port = int(url.rsplit(":", 1)[1].strip("/"))
    yield port
    web._server.shutdown()
    web._server = None


def _req(port, method, path, body=None, headers=None, host=None):
    c = http.client.HTTPConnection("127.0.0.1", port)
    h = {"Host": host or f"127.0.0.1:{port}", **(headers or {})}
    c.request(method, path, body=body, headers=h)
    r = c.getresponse()
    data = r.read()
    return r.status, data


def test_dashboard_reads_and_merges(dash):
    store.upsert_jobs([{"site": "indeed", "url": "u1", "title": "Data Engineer", "company": "Acme", "description": "<b>x</b>"}])
    store.save_scores([{"job_id": 1, "skills": [{"label": "SQL", "level": "full"}], "role_score": 85, "seniority_fit": "match",
                        "domain_fit": "same", "overview": "Good fit", "role_reason": "did it"}])
    st, body = _req(dash, "GET", "/")
    assert st == 200 and b"jobfishing" in body
    st, body = _req(dash, "GET", "/api/jobs?q=acme&scored=scored&min_score=70")
    assert st == 200 and _json.loads(body)["total"] == 1
    st, body = _req(dash, "GET", "/api/jobs/1")
    d = _json.loads(body)
    assert d["breakdown"]["role"] == 85 and d["judgment"]["role_reason"] == "did it"
    st, body = _req(dash, "GET", "/api/recommend?min_score=0")
    assert [r["source"] for r in _json.loads(body)["jobs"]] == ["jobfishing", "local"] or \
        [r["source"] for r in _json.loads(body)["jobs"]] == ["local", "jobfishing"]
    assert _req(dash, "GET", "/api/prompt")[0] == 200


def test_dashboard_refuses_foreign_hosts_and_unmarked_posts(dash):
    assert _req(dash, "GET", "/api/counts", host="evil.example")[0] == 403           # DNS rebinding
    assert _req(dash, "POST", "/api/crawl", body="{}", headers={"Content-Type": "application/json"})[0] == 403  # no marker header
    st, body = _req(dash, "POST", "/api/crawl", body=_json.dumps({"terms": [], "places": []}),
                    headers={"X-Jobfishing": "1", "Content-Type": "application/json"})
    assert st == 400


# ---- installer -------------------------------------------------------------------------------------------------------

def test_codex_config_is_idempotent_and_keeps_other_tables(tmp_path, monkeypatch):
    from jobfishing_engine import install
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "cx"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    legacy = tmp_path / "cx" / "skills" / "jobfishing-rank"
    legacy.mkdir(parents=True)  # what the first installer wrote
    cfg = tmp_path / "cx" / "config.toml"
    cfg.write_text('model = "x"\n\n[mcp_servers.other]\ncommand = "o"\n')
    monkeypatch.setattr(install, "_skills_src", lambda: Path(__file__).resolve().parents[1] / "skills")
    install.install_codex()
    first = cfg.read_text()
    install.install_codex()
    assert cfg.read_text() == first and first.count("[mcp_servers.jobfishing]") == 1
    assert 'model = "x"' in first and "[mcp_servers.other]" in first
    assert (tmp_path / "home" / ".agents" / "skills" / "jobfishing-rank" / "SKILL.md").exists()
    assert not legacy.exists()  # the old, unread copy is cleaned up
    install.uninstall_codex()
    left = cfg.read_text()
    assert "jobfishing" not in left and "[mcp_servers.other]" in left
    assert not (tmp_path / "home" / ".agents" / "skills" / "jobfishing-rank").exists()


def test_skills_refresh_on_start_only_where_installed(tmp_path, monkeypatch):
    from jobfishing_engine import install
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(install, "_skills_src", lambda: Path(__file__).resolve().parents[1] / "skills")
    assert install.sync_installed_skills() == []                       # nothing installed -> nothing created
    assert not (tmp_path / ".claude").exists()
    claude = tmp_path / ".claude" / "skills"
    (claude / "jobfishing-rank").mkdir(parents=True)
    (claude / "jobfishing-rank" / "SKILL.md").write_text("OLD")        # an earlier version's copy
    assert install.sync_installed_skills() == [str(claude)]
    assert (claude / "jobfishing-rank" / "SKILL.md").read_text() != "OLD"
    assert install.sync_installed_skills() == []                       # up to date -> no rewrite
    assert not (tmp_path / ".agents").exists()                         # Codex untouched


# ---- saving to jobfishing ----------------------------------------------------------------------------------------------

FULL = {
    "extraction": {"skills": [{"id": "s1", "label": "SQL", "status": "required"}, {"id": "s2", "label": "Python", "status": "preferred"}],
                   "role_summary": "Builds pipelines.", "seniority_band": "mid"},
    "skill_matches": ["s1:full", "s2:weak"], "role_score": 80, "seniority_fit": "match", "domain_fit": "related", "overview": "Good.",
}


def test_full_judgment_form_scores_like_the_simple_one():
    simple = {"skills": [{"importance": "required", "level": "full"}, {"importance": "preferred", "level": "weak"}],
              "role_score": 80, "seniority_fit": "match", "domain_fit": "related"}
    assert scoring.aggregate(FULL) == scoring.aggregate(simple)
    assert scoring.aggregate({**FULL, "skill_matches": ["s1:full"]})["qualification"] == round((0.9 * 3 + 0 * 1) / 4 * 100, 1)  # s2 ungraded = none


def test_save_to_jobfishing_sends_extraction_and_judgment(monkeypatch):
    pytest.importorskip("mcp")
    import jobfishing_mcp_server as m
    store.upsert_jobs([{"site": "indeed", "url": "https://x/1", "title": "DE", "company": "Acme", "location": "Hong Kong",
                        "description": "d" * 200}, {"site": "indeed", "url": "https://x/2", "title": "No extraction"}])
    store.save_scores([{"job_id": 1, **FULL}, {"job_id": 2, "skills": [], "role_score": 70, "seniority_fit": "match", "domain_fit": "same"}])
    sent = []
    monkeypatch.setattr(m, "_call", lambda method, path, **kw: sent.append((method, path, kw["json"])) or
                        {"results": [{"job_id": 900 + i, "score": 86.0, "saved": True} for i, _ in enumerate(kw["json"]["items"])]})
    out = m.save_to_jobfishing([1, 2, 99])["results"]
    assert out[1]["job_id"] == 900 and "extraction" in out[2]["error"] and out[99]["error"] == "no such local job"
    [(method, path, body)] = sent
    assert (method, path) == ("POST", "/api/v1/agent/jobs/import") and body["save"] is True and len(body["items"]) == 1
    item = body["items"][0]
    assert item["title"] == "DE" and item["extraction"]["skills"][0]["label"] == "SQL"
    assert item["judgment"]["skill_matches"] == ["s1:full", "s2:weak"] and "extraction" not in item["judgment"]


# ---- two-stage LinkedIn ------------------------------------------------------------------------------------------------

def test_linkedin_job_id_from_urls():
    from jobfishing_engine import crawl
    assert crawl.linkedin_job_id("https://hk.linkedin.com/jobs/view/data-engineer-at-acme-4012345678?trk=x") == "4012345678"
    assert crawl.linkedin_job_id("https://www.linkedin.com/jobs/view/4012345678/") == "4012345678"
    assert crawl.linkedin_job_id("https://hk.indeed.com/viewjob?jk=abc") is None


def _linkedin_rows(n):
    return [{"site": "linkedin", "url": f"https://www.linkedin.com/jobs/view/t-{4000000000 + i}", "title": f"T{i}"} for i in range(n)]


def test_fetch_descriptions_stores_text_and_counts(monkeypatch):
    from jobfishing_engine import crawl
    store.upsert_jobs(_linkedin_rows(3) + [{"site": "indeed", "url": "https://i/1", "title": "I", "description": "x" * 200}])
    monkeypatch.setattr(crawl, "_fetch_text", lambda session, lid: ("ok", "Posting text. " * 20) if not lid.endswith("2") else ("empty", None))
    monkeypatch.setattr(crawl.time, "sleep", lambda s: None)
    ids = [j["id"] for j in store.list_jobs(has_description=False)]
    res = crawl.fetch_descriptions(ids + [999])
    assert res["fetched"] == 2 and res["no_text_on_page"] == 1 and res["rate_limited"] is False and "message" not in res
    assert store.counts()["ready"] == 3 and store.counts()["no_description"] == 1       # 2 fetched + the Indeed job, 1 still titles-only
    assert crawl.fetch_descriptions(ids)["fetched"] == 0                                 # already-fetched jobs are not asked for again


def test_fetch_descriptions_stops_at_the_first_rate_limit_and_points_to_the_app(monkeypatch):
    from jobfishing_engine import crawl
    store.upsert_jobs(_linkedin_rows(6))
    calls = []
    def fake(session, lid):
        calls.append(lid)
        return ("rate_limited", None) if len(calls) >= 2 else ("ok", "Posting text. " * 20)
    monkeypatch.setattr(crawl, "_fetch_text", fake)
    monkeypatch.setattr(crawl.time, "sleep", lambda s: None)
    res = crawl.fetch_descriptions([j["id"] for j in store.list_jobs()], workers=1)
    assert res["rate_limited"] is True and res["fetched"] == 1 and len(res["retry_ids"]) == 5
    assert "wait a few minutes" in res["message"].lower() and "jobfishing app" in res["message"]
    assert len(calls) == 2                                                               # it did not keep hammering after the limit


def test_ready_jobs_filter_and_dashboard_prompt_uses_the_jobfishing_profile():
    from jobfishing_engine import web
    store.upsert_jobs(_linkedin_rows(2) + [{"site": "indeed", "url": "https://i/1", "title": "I", "description": "x" * 200}])
    assert [j["site"] for j in store.list_jobs(scored=False, has_description=True)] == ["indeed"]
    assert len(store.list_jobs(has_description=False)) == 2
    p = web._agent_prompt(store.counts()["ready"])
    assert "my 1 unscored" in p and "get_scoring_profile" in p and "fall back to my CV" in p


def test_dashboard_caches_the_jobfishing_list_but_not_failures():
    from jobfishing_engine import web
    calls = []
    def fetch():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("not signed in")
        return [{"id": 1, "score": 90, "decision": "generate"}]
    f = web._cached(fetch, ttl=60)
    try:
        f()
    except RuntimeError:
        pass
    assert f()[0]["id"] == 1 and f()[0]["id"] == 1 and len(calls) == 2      # the failure was retried, the success was kept


# ---- clear and save prompts ---------------------------------------------------------------------------------------------

def _scored_job(url, title="DE"):
    store.upsert_jobs([{"site": "indeed", "url": url, "title": title, "company": "Acme", "description": "d" * 200}])
    jid = [j["id"] for j in store.list_jobs() if j["url"] == url][0]
    store.save_scores([{"job_id": jid, "skills": [], "role_score": 90, "seniority_fit": "match", "domain_fit": "same"}])
    return jid


def test_clear_hides_everywhere_keeps_the_row_and_survives_a_recrawl():
    a, b = _scored_job("https://x/a"), _scored_job("https://x/b")
    assert store.clear_jobs([a, 999]) == 1 and store.clear_jobs([a]) == 0          # only live rows count, once
    assert [j["id"] for j in store.list_jobs()] == [b]
    assert [j["id"] for j in store.search_jobs()["jobs"]] == [b]
    assert store.counts()["jobs"] == 1 and store.counts()["scored"] == 1
    assert store.get_job(a)["cleared_at"] is not None and store.get_job(a)["score"] is not None   # still in the file, score kept
    assert store.upsert_jobs([{"site": "indeed", "url": "https://x/a", "title": "DE"}])["new"] == 0   # crawling it again adds nothing
    assert [j["id"] for j in store.list_jobs()] == [b]                              # ...and it does not come back


def test_a_database_from_before_clear_existed_is_migrated(tmp_path, monkeypatch):
    import sqlite3
    old = tmp_path / "jobfishing.db"
    con = sqlite3.connect(old)
    con.executescript("CREATE TABLE jobs (id INTEGER PRIMARY KEY, site TEXT NOT NULL, url TEXT NOT NULL, title TEXT, company TEXT, "
                      "location TEXT, country TEXT, description TEXT, date_posted TEXT, salary TEXT, job_type TEXT, is_remote INTEGER, "
                      "search_term TEXT, created_at REAL NOT NULL, UNIQUE (site, url)); "
                      "INSERT INTO jobs (site,url,title,created_at) VALUES ('indeed','https://old/1','Old job',1);")
    con.commit(); con.close()
    monkeypatch.setenv("JOBFISHING_HOME", str(tmp_path))
    assert [j["title"] for j in store.list_jobs()] == ["Old job"]                   # opens, adds the column, nothing lost
    assert store.clear_jobs([1]) == 1 and store.list_jobs() == []


def test_dashboard_clear_endpoint_and_the_three_prompts(dash):
    a = _scored_job("https://x/a", "Data Engineer")
    store.upsert_jobs([{"site": "linkedin", "url": "https://www.linkedin.com/jobs/view/t-4000000001", "title": "Title only"}])
    st, _ = _req(dash, "POST", "/api/clear", body=_json.dumps({"ids": [a]}), headers={"Content-Type": "application/json"})
    assert st == 403 and store.counts()["jobs"] == 2                                # no marker header: refused, nothing cleared
    st, body = _req(dash, "GET", "/api/prompt?kind=fetch")
    fetch = _json.loads(body)["prompt"]
    assert "1 jobs I just crawled have only a title" in fetch and "fetch_descriptions" in fetch and "rate-limiting" in fetch
    st, body = _req(dash, "GET", f"/api/prompt?kind=save&ids={a},9999")
    save = _json.loads(body)["prompt"]
    assert f"[{a}]" in save and "Data Engineer at Acme" in save and "save_to_jobfishing" in save and "full form" in save
    assert _req(dash, "GET", "/api/prompt?kind=save&ids=")[0] == 400                # nothing picked
    st, body = _req(dash, "POST", "/api/clear", body=_json.dumps({"ids": [a]}),
                    headers={"X-Jobfishing": "1", "Content-Type": "application/json"})
    assert st == 200 and _json.loads(body) == {"cleared": 1} and store.counts()["jobs"] == 1
    assert _req(dash, "GET", f"/api/prompt?kind=save&ids={a}")[0] == 400            # a cleared job cannot be put in a save prompt
