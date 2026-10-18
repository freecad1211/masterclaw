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
    # Ensure LLM is not configured so the service uses demo agents
    monkeypatch.setattr("forgeclaw.core.settings.settings.llm_base_url", "")
    monkeypatch.setattr("forgeclaw.core.settings.settings.llm_model", "")
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
        assert [message["stage"] for message in created["messages"]] == [
            "proposal", "critique", "revision", "critique", "decision"
        ]
        assert len(created["messages"]) == 5

        fetched = client.get(f"/api/v1/debates/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]

        listed = client.get("/api/v1/debates")
        assert listed.status_code == 200
        assert any(item["id"] == created["id"] for item in listed.json())


def test_single_round_has_no_revision(tmp_path, monkeypatch):
    db_path = str(tmp_path / "single-round.sqlite3")
    monkeypatch.setattr("forgeclaw.core.settings.settings.database_path", db_path)
    # Ensure LLM is not configured so the service uses demo agents
    monkeypatch.setattr("forgeclaw.core.settings.settings.llm_base_url", "")
    monkeypatch.setattr("forgeclaw.core.settings.settings.llm_model", "")
    from forgeclaw.services.debate_service import DebateService
    monkeypatch.setattr("forgeclaw.api.routes.service", DebateService(database_path=db_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/debates",
            json={"topic": "Choose a testable design", "max_rounds": 1},
        )
    assert response.status_code == 201
    assert [message["stage"] for message in response.json()["messages"]] == [
        "proposal", "critique", "decision"
    ]


def test_missing_debate_returns_404(tmp_path, monkeypatch):
    db_path = str(tmp_path / "missing.sqlite3")
    monkeypatch.setattr("forgeclaw.core.settings.settings.database_path", db_path)
    with TestClient(app) as client:
        response = client.get("/api/v1/debates/not-a-real-id")
    assert response.status_code == 404
