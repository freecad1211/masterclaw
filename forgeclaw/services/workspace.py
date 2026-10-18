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
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if result.returncode:
            raise WorkspaceError((result.stderr or result.stdout)[-4000:])
        return result.stdout.strip()

    def create(self, branch: str, base_branch: str) -> Path:
        safe_branch = branch.replace(" ", "-")
        target = (self.worktrees / safe_branch).resolve()
        if self.worktrees.resolve() not in target.parents:
            raise WorkspaceError("Invalid worktree path.")
        if target.exists():
            raise WorkspaceError(f"Worktree path already exists: {target.name}")
        self._git(["worktree", "add", "-b", safe_branch, str(target), base_branch], timeout=60)
        return target

    def status(self, cwd: Path) -> str:
        return self._git(["status", "--short", "--branch"], cwd=cwd)

    def diff(self, cwd: Path, base_branch: str) -> str:
        return self._git(["diff", "--no-ext-diff", "--", "."], cwd=cwd) + "\n" + self._git(
            ["diff", "--no-ext-diff", f"{base_branch}...HEAD"], cwd=cwd
        )

    def commit(self, cwd: Path, message: str) -> str:
        self._git(["add", "-A"], cwd=cwd)
        if not self._git(["status", "--porcelain"], cwd=cwd):
            raise WorkspaceError("Refusing to create an empty commit.")
        self._git(["commit", "-m", message[:160]], cwd=cwd, timeout=60)
        return self._git(["rev-parse", "HEAD"], cwd=cwd)

    def run_tests(self, cwd: Path, command: str = "pytest") -> tuple[int, str]:
        if command not in {"pytest", "python -m pytest", "python -m compileall forgeclaw"}:
            raise WorkspaceError("Test command is not allowlisted.")
        args = command.split()
        try:
            result = subprocess.run(
                args, cwd=cwd, text=True, capture_output=True, timeout=300, check=False,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
        except subprocess.TimeoutExpired as exc:
            return 124, f"Test command timed out after 300 seconds: {exc.cmd}"
        return result.returncode, (result.stdout + "\n" + result.stderr)[-12000:]

    def merge_branch(self, branch: str, target_branch: str) -> str:
        self._git(["checkout", target_branch])
        try:
            self._git(["merge", "--no-ff", "--no-edit", branch], timeout=120)
        except WorkspaceError:
            # Abort any partial merge so the repository is left in a known state.
            subprocess.run(["git", "merge", "--abort"], cwd=self.repo, text=True, capture_output=True)
            raise WorkspaceError(f"Merge conflict integrating {branch} into {target_branch}; manual resolution required.")
        return self._git(["rev-parse", "HEAD"])
