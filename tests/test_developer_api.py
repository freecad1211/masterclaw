from fastapi.testclient import TestClient

from forgeclaw.main import app


def test_developer_metadata_endpoints():
    with TestClient(app) as client:
        profiles = client.get("/api/v1/developer/profiles")
        skills = client.get("/api/v1/developer/skills")
        tools = client.get("/api/v1/developer/mcp-tools")

    assert profiles.status_code == 200
    assert {item["role"] for item in profiles.json()} >= {
        "architect", "implementer", "reviewer", "tester", "integrator"
    }
    assert skills.status_code == 200
    assert len(skills.json()) >= 6
    assert tools.status_code == 200
    assert {item["name"] for item in tools.json()} >= {
        "read_file", "search_files", "git_status", "git_diff", "run_tests"
    }


def test_run_message_bus_and_merge_approval_state():
    from forgeclaw.api.developer_routes import service
    from forgeclaw.models.developer import DeveloperRun

    run = DeveloperRun(
        goal="Test message routing",
        repo_path="/tmp/not-used",
        base_branch="main",
        status="queued",
    )
    service._runs[run.id] = run

    with TestClient(app) as client:
        message = client.post(
            f"/api/v1/developer/runs/{run.id}/messages",
            json={
                "sender": "reviewer",
                "recipient": "implementer",
                "content": "Please add an edge-case test.",
            },
        )
        approval = client.post(f"/api/v1/developer/runs/{run.id}/approve-merge")

    assert message.status_code == 200
    assert message.json()["recipient"] == "implementer"
    assert message.json()["content"] == "Please add an edge-case test."
    assert approval.status_code == 409
