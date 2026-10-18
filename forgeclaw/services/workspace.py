from __future__ import annotations

import os
import subprocess
from pathlib import Path


class WorkspaceError(RuntimeError):
    pass


class GitWorkspace:
    """Create task-isolated worktrees and execute a small test-command allowlist."""

    def __init__(self, repo_path: str, run_id: str) -> None:
        self.repo = Path(repo_path).expanduser().resolve()
        if not (self.repo / ".git").exists():
            raise WorkspaceError("repo_path must point to a Git repository root.")
        self.worktrees = self.repo / ".forgeclaw" / "worktrees" / run_id
        self.worktrees.mkdir(parents=True, exist_ok=True)
        self._git(["rev-parse", "--show-toplevel"])

    def _git(self, args: list[str], *, cwd: Path | None = None, timeout: int = 30) -> str:
        result = subprocess.run(
            ["git", *args], cwd=cwd or self.repo, text=True, capture_output=True,
            timeout=timeout, check=False,
            env={
                **os.environ, "GIT_TERMINAL_PROMPT": "0",
                "GIT_AUTHOR_NAME": os.getenv("GIT_AUTHOR_NAME", "ForgeClaw Agent"),
                "GIT_AUTHOR_EMAIL": os.getenv("GIT_AUTHOR_EMAIL", "forgeclaw@localhost"),
                "GIT_COMMITTER_NAME": os.getenv("GIT_COMMITTER_NAME", "ForgeClaw Agent"),
                "GIT_COMMITTER_EMAIL": os.getenv("GIT_COMMITTER_EMAIL", "forgeclaw@localhost"),
            },
        )
        if result.returncode:
            raise WorkspaceError((result.stderr or result.stdout)[-4000:])
        return result.stdout.strip()

    def ensure_clean_base(self, base_branch: str) -> None:
        current = self._git(["branch", "--show-current"])
        if current != base_branch:
            raise WorkspaceError(f"Repository must be checked out on base branch {base_branch!r}; current branch is {current!r}.")
        status = self._git(["status", "--porcelain"])
        if status:
            raise WorkspaceError("Repository has uncommitted changes. Commit or stash them before Developer Mode.")
        self._git(["rev-parse", "--verify", base_branch])

    def create(self, branch: str, base_branch: str) -> Path:
        safe_branch = branch.replace(" ", "-")
        target = (self.worktrees / safe_branch.split("/")[-1]).resolve()
        if self.worktrees.resolve() not in target.parents:
            raise WorkspaceError("Invalid worktree path.")
        if target.exists():
            raise WorkspaceError(f"Worktree path already exists: {target.name}")
        self._git(["worktree", "add", "-b", safe_branch, str(target), base_branch], timeout=60)
        return target

    def create_integration(self, branch: str, base_branch: str) -> Path:
        safe_branch = branch.replace(" ", "-")
        target = (self.worktrees / "integration").resolve()
        if self.worktrees.resolve() not in target.parents or target.exists():
            raise WorkspaceError("Integration worktree path already exists or is invalid.")
        self._git(["worktree", "add", "-b", safe_branch, str(target), base_branch], timeout=60)
        return target

    def status(self, cwd: Path) -> str:
        return self._git(["status", "--short", "--branch"], cwd=cwd)

    def apply_patch(self, cwd: Path, patch: str) -> None:
        if not patch.strip() or "diff --git " not in patch:
            raise WorkspaceError("Model did not return a standard unified Git diff.")
        for flag in ("GIT_DIR=", "GIT_WORK_TREE=", "\x00"):
            if flag in patch:
                raise WorkspaceError("Patch contains an invalid control sequence.")
        check = subprocess.run(
            ["git", "apply", "--check", "--whitespace=error"],
            input=patch, cwd=cwd, text=True, capture_output=True, timeout=30,
        )
        if check.returncode:
            raise WorkspaceError("Patch validation failed: " + (check.stderr or check.stdout)[-3000:])
        applied = subprocess.run(
            ["git", "apply", "--whitespace=error"],
            input=patch, cwd=cwd, text=True, capture_output=True, timeout=30,
        )
        if applied.returncode:
            raise WorkspaceError("Patch application failed: " + (applied.stderr or applied.stdout)[-3000:])

    def changed_paths(self, cwd: Path) -> list[str]:
        result = self._git(["diff", "--name-only"], cwd=cwd)
        untracked = self._git(["ls-files", "--others", "--exclude-standard"], cwd=cwd)
        return sorted(set(filter(None, result.splitlines() + untracked.splitlines())))

    def diff(self, cwd: Path, base_branch: str) -> str:
        return self._git(["diff", "--no-ext-diff", f"{base_branch}...HEAD"], cwd=cwd)

    def commit(self, cwd: Path, message: str) -> str:
        self._git(["add", "-A"], cwd=cwd)
        if not self._git(["status", "--porcelain"], cwd=cwd):
            raise WorkspaceError("Refusing to create an empty commit.")
        self._git(["commit", "-m", message[:160]], cwd=cwd, timeout=60)
        return self._git(["rev-parse", "HEAD"], cwd=cwd)

    def run_tests(self, cwd: Path, command: str = "pytest") -> tuple[int, str]:
        allowed = {
            "pytest": ["pytest"],
            "python -m pytest": ["python", "-m", "pytest"],
            "python -m compileall forgeclaw": ["python", "-m", "compileall", "forgeclaw"],
        }
        if command not in allowed:
            raise WorkspaceError("Test command is not allowlisted.")
        try:
            result = subprocess.run(
                allowed[command], cwd=cwd, text=True, capture_output=True, timeout=300, check=False,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
        except subprocess.TimeoutExpired as exc:
            return 124, f"Test command timed out after 300 seconds: {exc.cmd}"
        except OSError as exc:
            return 127, f"Test command could not start: {type(exc).__name__}"
        return result.returncode, (result.stdout + "\n" + result.stderr)[-12000:]

    def merge_branch(self, branch: str, integration_path: Path) -> str:
        try:
            self._git(["merge", "--no-ff", "--no-edit", branch], cwd=integration_path, timeout=120)
        except WorkspaceError as exc:
            subprocess.run(["git", "merge", "--abort"], cwd=integration_path, text=True, capture_output=True)
            raise WorkspaceError(f"Merge conflict integrating {branch}; manual resolution required.") from exc
        return self._git(["rev-parse", "HEAD"], cwd=integration_path)

    def merge_to_base(self, integration_branch: str, base_branch: str) -> str:
        self.ensure_clean_base(base_branch)
        try:
            self._git(["merge", "--no-ff", "--no-edit", integration_branch], timeout=120)
        except WorkspaceError as exc:
            subprocess.run(["git", "merge", "--abort"], cwd=self.repo, text=True, capture_output=True)
            raise WorkspaceError("Final merge conflict; base branch was not changed.") from exc
        return self._git(["rev-parse", "HEAD"])
