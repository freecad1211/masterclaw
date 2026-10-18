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
