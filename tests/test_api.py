from fastapi.testclient import TestClient

from forgeclaw.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "forgeclaw"}


def test_create_and_read_debate(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.sqlite3")
    monkeypatch.setattr("forgeclaw.core.settings.settings.database_path", db_path)
    monkeypatch.setattr("forgeclaw.api.routes.settings.database_path", db_path)
    from forgeclaw.services.debate_service import DebateService
    monkeypatch.setattr("forgeclaw.api.routes.service", DebateService(database_path=db_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/debates",
            json={"topic": "How should we store decisions?", "max_rounds": 2},
        )
        assert response.status_code == 201
        created = response.json()
        assert created["status"] == "completed"
        assert len(created["messages"]) == 3

        fetched = client.get(f"/api/v1/debates/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]

        listed = client.get("/api/v1/debates")
        assert listed.status_code == 200
        assert any(item["id"] == created["id"] for item in listed.json())


def test_missing_debate_returns_404(tmp_path, monkeypatch):
    db_path = str(tmp_path / "missing.sqlite3")
    monkeypatch.setattr("forgeclaw.core.settings.settings.database_path", db_path)
    with TestClient(app) as client:
        response = client.get("/api/v1/debates/not-a-real-id")
    assert response.status_code == 404
