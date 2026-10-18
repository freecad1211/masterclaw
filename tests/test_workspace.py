import subprocess

import pytest

from forgeclaw.services.workspace import GitWorkspace, WorkspaceError


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_workspace_creates_isolated_branch_and_applies_patch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "ForgeClaw Test")
    _git(repo, "config", "user.email", "forgeclaw-test@example.invalid")
    (repo / ".gitignore").write_text(".forgeclaw/\n", encoding="utf-8")
    (repo / "hello.txt").write_text("before\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    workspace = GitWorkspace(str(repo), "test-run")
    workspace.ensure_clean_base("main")
    tree = workspace.create("feature/test-run-task-a", "main")
    patch = (
        "diff --git a/hello.txt b/hello.txt\n"
        "--- a/hello.txt\n"
        "+++ b/hello.txt\n"
        "@@ -1 +1 @@\n"
        "-before\n"
        "+after\n"
    )
    workspace.apply_patch(tree, patch)

    assert (tree / "hello.txt").read_text(encoding="utf-8") == "after\n"
    assert workspace.changed_paths(tree) == ["hello.txt"]
    assert workspace._git(["branch", "--show-current"], cwd=tree) == "feature/test-run-task-a"


def test_workspace_rejects_arbitrary_test_command(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".forgeclaw/\n", encoding="utf-8")
    workspace = GitWorkspace(str(repo), "command-test")
    with pytest.raises(WorkspaceError, match="allowlisted"):
        workspace.run_tests(repo, "rm -rf /")


def test_auto_detect_uses_package_script_when_tests_folder_is_javascript(tmp_path):
    repo = tmp_path / "jsrepo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "tests").mkdir()
    (repo / "tests" / "sample.test.ts").write_text("export {}\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"name":"sample","scripts":{"test":"vitest run","build":"next build"}}',
        encoding="utf-8",
    )
    workspace = GitWorkspace(str(repo), "js-test-run")
    assert workspace._resolve_test_command(repo, "auto") == ["npm", "test"]


def test_repository_context_excludes_common_secret_files(tmp_path):
    repo = tmp_path / "secret-repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("safe project description\n", encoding="utf-8")
    (repo / ".env.local").write_text("VERY_SECRET_VALUE=do-not-send\n", encoding="utf-8")
    (repo / ".npmrc").write_text("//registry.example/:_authToken=do-not-send\n", encoding="utf-8")
    (repo / "api_secret.txt").write_text("another-secret-value\n", encoding="utf-8")

    workspace = GitWorkspace(str(repo), "secret-context-test")
    snapshot = workspace.context_snapshot(repo)

    assert "safe project description" in snapshot
    assert "VERY_SECRET_VALUE" not in snapshot
    assert "_authToken" not in snapshot
    assert "another-secret-value" not in snapshot
