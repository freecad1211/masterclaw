from forgeclaw.services.mcp_catalog import list_mcp_tools
from forgeclaw.services.skills import list_skills


def test_builtin_skills_have_instructions_and_tools():
    skills = list_skills()
    assert {"repo-exploration", "implementation", "test-driven-debugging",
            "independent-code-review", "git-integration", "secure-tool-use"} <= {
        skill["name"] for skill in skills
    }
    assert all(skill["instructions"] and skill["tools"] for skill in skills)


def test_builtin_mcp_catalog_is_bounded_and_documented():
    tools = list_mcp_tools()
    assert {"workspace_tree", "read_file", "search_files", "git_status", "git_diff", "run_tests"} == {
        tool["name"] for tool in tools
    }
    assert all(tool["description"] and tool["safety"] for tool in tools)
