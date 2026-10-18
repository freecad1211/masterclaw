import json
import logging

from fastapi.testclient import TestClient

from forgeclaw.core.logging import JsonFormatter, _redact
from forgeclaw.main import app
from forgeclaw.models.developer import DeveloperRun
from forgeclaw.storage.database import initialize_database, list_developer_runs, save_developer_run


def test_redacts_secrets_from_nested_payloads():
    result = _redact({"api_key": "super-secret", "nested": {"Authorization": "Bearer abc123"}, "message": "Bearer eyJhbGciOiJIUzI1NiJ9"})
    assert result["api_key"] == "[REDACTED]"
    assert result["nested"]["Authorization"] == "[REDACTED]"
    assert "[REDACTED]" in result["message"]
    assert "abc123" not in json.dumps(result)


def test_json_formatter_outputs_valid_json_and_fields():
    record = logging.LogRecord("forgeclaw.test", logging.INFO, __file__, 1, "request complete", (), None)
    record.request_id = "req-test"
    record.status_code = 200
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "request complete"
    assert payload["request_id"] == "req-test"
    assert payload["status_code"] == 200


def test_control_room_is_served_with_security_headers():
    with TestClient(app) as client:
        response = client.get("/ui", headers={"x-request-id": "test.req-1"})
        ready = client.get("/ready")
    assert response.status_code == 200
    assert "ForgeClaw" in response.text
    assert "개발 실행 시작" in response.text
    assert response.headers["x-request-id"] == "test.req-1"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert ready.status_code == 200


def test_developer_run_history_persists(tmp_path):
    db = str(tmp_path / "forgeclaw.sqlite3")
    initialize_database(db)
    run = DeveloperRun(goal="Persist run test", repo_path=str(tmp_path), base_branch="main")
    save_developer_run(db, run.model_dump(mode="json"))
    saved = list_developer_runs(db)
    assert len(saved) == 1
    assert saved[0]["id"] == run.id
    assert saved[0]["goal"] == "Persist run test"
