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
    assert r["qualification"] == 0 and "role" not in r


def test_store_roundtrip_and_url_uniqueness():
    rows = [{"site": "indeed", "url": "https://x/1", "title": "A", "company": "C"},
            {"site": "indeed", "url": "https://x/1", "title": "A again"}, {"site": "linkedin", "url": ""}]
    assert store.upsert_jobs(rows) == {"received": 3, "new": 1}
    [job] = store.list_jobs(scored=False)
    out = store.save_scores([{"job_id": job["id"], "skills": [], "role_score": 90, "seniority_fit": "match", "domain_fit": "same"},
                             {"job_id": 999}])
    assert out[0]["decision"] == "generate" and out[1]["error"]
    assert store.counts() == {"jobs": 1, "scored": 1, "unscored": 0}
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
    (tmp_path / "cx").mkdir()
    cfg = tmp_path / "cx" / "config.toml"
    cfg.write_text('model = "x"\n\n[mcp_servers.other]\ncommand = "o"\n')
    monkeypatch.setattr(install, "_skills_src", lambda: Path(__file__).resolve().parents[1] / "skills")
    install.install_codex()
    first = cfg.read_text()
    install.install_codex()
    assert cfg.read_text() == first and first.count("[mcp_servers.jobfishing]") == 1
    assert 'model = "x"' in first and "[mcp_servers.other]" in first
    assert (tmp_path / "cx" / "skills" / "jobfishing-rank" / "SKILL.md").exists()
    install.uninstall_codex()
    left = cfg.read_text()
    assert "jobfishing" not in left and "[mcp_servers.other]" in left
    assert not (tmp_path / "cx" / "skills" / "jobfishing-rank").exists()
