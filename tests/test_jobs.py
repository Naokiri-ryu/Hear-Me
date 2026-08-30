from types import SimpleNamespace


def _patching(monkeypatch, state, result=None):
    import api.routers.jobs as jobs_mod

    def fake_async_result(task_id):
        return SimpleNamespace(state=state, result=result)

    monkeypatch.setattr(jobs_mod.celery_app, "AsyncResult", fake_async_result)


def test_job_status_not_ready(client, token, monkeypatch):
    _patching(monkeypatch, "PENDING")
    resp = client.get("/jobs/t1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "PENDING"
    assert body["result"] is None


def test_job_status_success(client, token, monkeypatch):
    _patching(monkeypatch, "SUCCESS", {"ok": True, "reordered": 3})
    resp = client.get("/jobs/t1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "SUCCESS"
    assert body["result"] == {"ok": True, "reordered": 3}


def test_job_status_failure(client, token, monkeypatch):
    _patching(monkeypatch, "FAILURE", RuntimeError("boom"))
    resp = client.get("/jobs/t1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "FAILURE"
    assert "boom" in (body["error"] or "")


def test_job_status_requires_auth(client):
    assert client.get("/jobs/t1").status_code == 401