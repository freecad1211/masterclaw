import json
import logging

from fastapi.testclient import TestClient

from forgeclaw.core.logging import JsonFormatter, _redact
from forgeclaw.main import app


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


def test_control_room_is_served():
    with TestClient(app) as client:
        response = client.get("/ui")
    assert response.status_code == 200
    assert "ForgeClaw" in response.text
    assert "개발 실행 시작" in response.text
