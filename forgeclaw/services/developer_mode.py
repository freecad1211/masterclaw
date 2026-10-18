from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from forgeclaw.models.developer import AgentEvent, DeveloperRun, DeveloperRunRequest, DeveloperTask
from forgeclaw.services.model_router import AgentModelRouter
from forgeclaw.services.workspace import GitWorkspace, WorkspaceError


PROMPT_ROOT = Path(__file__).resolve().parents[2] / "prompts"


def _prompt(name: str) -> str:
    try:
        return (PROMPT_ROOT / name).read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Missing prompt file: {name}") from exc


def _strip_fence(value: str) -> str:
    value = value.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        return "\n".join(lines).strip()
    return value


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower()
    return (slug or "task")[:36]


class DeveloperModeService:
    """Runs bounded multi-agent work in isolated Git worktrees."""

    def __init__(self) -> None:
        self.models = AgentModelRouter()
        self._runs: dict[str, DeveloperRun] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="forgeclaw-run")

    def profiles(self) -> list[dict[str, str | bool]]:
        return self.models.available_profiles()

    def skills(self) -> list[dict[str, object]]:
        from forgeclaw.services.skills import list_skills
        return list_skills()

    def tools(self) -> list[dict[str, str]]:
        from forgeclaw.services.mcp_catalog import list_mcp_tools
        return list_mcp_tools()

    def get_run(self, run_id: str) -> DeveloperRun | None:
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(self) -> list[DeveloperRun]:
        with self._lock:
            return sorted(self._runs.values(), key=lambda run: run.created_at, reverse=True)[:50]

    def start(self, request: DeveloperRunRequest) -> DeveloperRun:
        run = DeveloperRun(
            goal=request.goal,
            repo_path=str(Path(request.repo_path).expanduser().resolve()),
            base_branch=request.base_branch,
            tasks=request.tasks,
            integration_branch=f"integration/forgeclaw-{uuid4().hex[:8]}",
        )
        with self._lock:
            self._runs[run.id] = run
        self._emit(run, "orchestrator", "status", "Developer Mode run queued.")
        self._executor.submit(self.execute, run.id, request)
        return run

    def _emit(self, run: DeveloperRun, agent: str, event_type: str, content: str, task_id: str | None = None, recipient: str | None = None) -> AgentEvent:
        event = AgentEvent(run_id=run.id, agent=agent, event_type=event_type, content=content[:20000], task_id=task_id, recipient=recipient)
        with self._lock:
            run.events.append(event)
            run.updated_at = datetime.now(timezone.utc)
        return event

    def send_message(self, run_id: str, sender: str, recipient: str, content: str, task_id: str | None = None) -> AgentEvent:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError("Developer run not found.")
        allowed = {"architect", "implementer", "reviewer", "tester", "integrator"}
        if sender not in allowed or recipient not in allowed:
            raise ValueError("Unknown agent role.")
        return self._emit(run, sender, "message", content, task_id, recipient=recipient)

    def approve_merge(self, run_id: str) -> DeveloperRun:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError("Developer run not found.")
        if run.status != "needs_approval":
            raise ValueError("Only a run in needs_approval status can be merged.")
        workspace = GitWorkspace(run.repo_path, run.id)
        run.final_commit = workspace.merge_to_base(run.integration_branch, run.base_branch)
        run.status = "completed"
        self._emit(run, "integrator", "merge", f"User approved local merge into {run.base_branch} at {run.final_commit}.")
        return run

    def _complete(self, role: str, task: str, *, system_extra: str = "", temperature: float = 0.1) -> str:
        client = self.models.client_for(role)
        if not client.is_configured:
            raise RuntimeError(f"No model configured for {role}; set role-specific settings or global LLM_BASE_URL and LLM_MODEL.")
        core = _prompt("system.md")
        role_prompt = _prompt(f"roles/{role}.md")
        system = f"{core}\n\n--- Assigned role ---\n{role_prompt}"
        if system_extra:
            system += "\n\n--- Task-specific rules ---\n" + system_extra
        return client.complete(system_prompt=system, user_prompt=task, temperature=temperature)

    def _plan_tasks(self, run: DeveloperRun, request: DeveloperRunRequest) -> list[DeveloperTask]:
        if request.tasks:
            tasks = request.tasks
        else:
            response = self._complete(
                "architect",
                "Create a parallelizable software implementation plan for the goal below. Return only a JSON array. "
                "Each item must have id, title, description, owner (implementer), depends_on (array of task IDs), "
                "and allowed_paths (non-empty list of repository-relative paths/globs). Use unique short IDs. "
                "Keep tasks independently committable, avoid overlapping allowed_paths when possible, and include acceptance criteria.\n\n"
                f"Repository: {run.repo_path}\nGoal:\n{run.goal}",
                temperature=0.1,
            )
            try:
                payload = json.loads(_strip_fence(response))
                tasks = [DeveloperTask.model_validate(item) for item in payload]
            except (ValueError, ValidationError, TypeError) as exc:
                raise RuntimeError("Architect returned an invalid task plan; expected a JSON array of scoped tasks.") from exc
        if not tasks:
            raise RuntimeError("Task plan is empty.")
        if len(tasks) > 12:
            raise RuntimeError("Task plan exceeds the 12-task limit.")
        ids = {task.id for task in tasks}
        if len(ids) != len(tasks):
            raise RuntimeError("Task IDs must be unique.")
        for task in tasks:
            if not task.allowed_paths:
                raise RuntimeError(f"Task {task.id} has no allowed_paths; refusing unrestricted edits.")
            unknown = set(task.depends_on) - ids
            if unknown:
                raise RuntimeError(f"Task {task.id} depends on unknown task IDs: {sorted(unknown)}")
            if task.id in task.depends_on:
                raise RuntimeError(f"Task {task.id} cannot depend on itself.")
        self._topological_waves(tasks)  # also validates cycles
        return tasks

    @staticmethod
    def _topological_waves(tasks: list[DeveloperTask]) -> list[list[DeveloperTask]]:
        pending = {task.id: task for task in tasks}
        completed: set[str] = set()
        waves: list[list[DeveloperTask]] = []
        while pending:
            ready = [task for task in pending.values() if set(task.depends_on) <= completed]
            if not ready:
                raise RuntimeError("Task dependencies contain a cycle.")
            waves.append(ready)
            for task in ready:
                completed.add(task.id)
                pending.pop(task.id)
        return waves

    @staticmethod
    def _extract_patch(response: str) -> str:
        response = _strip_fence(response)
        start = response.find("diff --git ")
        if start < 0:
            raise RuntimeError("Implementer did not return a unified diff; refusing to modify the worktree.")
        return response[start:].strip() + "\n"

    def _run_task(
        self,
        run: DeveloperRun,
        task: DeveloperTask,
        workspace: GitWorkspace,
        branch_base: str,
        max_revisions: int,
    ) -> DeveloperTask:
        task.branch = f"feature/forgeclaw-{run.id[:8]}-{_safe_slug(task.id)}"
        try:
            worktree = workspace.create(task.branch, branch_base)
            task.status = "running"
            self._emit(run, task.owner, "status", f"Started {task.title} on {task.branch}, based on {branch_base}.", task.id)
            feedback = ""
            for attempt in range(max_revisions + 1):
                prompt = (
                    f"Repository goal:\n{run.goal}\n\nTask ID: {task.id}\nTitle: {task.title}\n"
                    f"Description and acceptance criteria:\n{task.description}\n\n"
                    f"Allowed paths (no other file may change): {json.dumps(task.allowed_paths)}\n"
                    f"Branch: {task.branch}\nAttempt: {attempt + 1} of {max_revisions + 1}\n"
                    f"Previous test/review feedback:\n{feedback or '(none yet)'}\n\n"
                    "Return a valid unified Git diff only. Paths must be relative to repository root. "
                    "Do not include explanations, shell commands, secrets, or files outside allowed_paths."
                )
                current_diff = workspace.diff(worktree, branch_base)
                if current_diff:
                    prompt += "\n\nCurrent worktree diff (already applied; return only an incremental patch that applies on top of this state):\n" + current_diff[-16000:]
                response = self._complete("implementer", prompt, temperature=0.1)
                try:
                    patch = self._extract_patch(response)
                    workspace.apply_patch(worktree, patch)
                    changed = workspace.changed_paths(worktree)
                    allowed = task.allowed_paths
                    unexpected = [
                        path for path in changed
                        if not any(Path(path).match(pattern) or path == pattern.rstrip("/") or path.startswith(pattern.rstrip("/") + "/")
                                   for pattern in allowed)
                    ]
                    if unexpected:
                        workspace.reset_changes(worktree)
                        feedback = f"PATCH REJECTED: changes outside allowed paths: {unexpected[:20]}. Return a patch limited to {allowed}."
                        if attempt < max_revisions:
                            continue
                        raise WorkspaceError(feedback)
                except WorkspaceError as exc:
                    feedback = f"PATCH VALIDATION FAILED: {exc}. Return a corrected incremental patch."
                    if attempt < max_revisions:
                        continue
                    raise
                code, test_output = workspace.run_tests(worktree, request.test_command)
                task.test_output = f"exit_code={code}\n{test_output}"
                self._emit(run, "tester", "test", f"pytest exit code: {code}\n{test_output[-5000:]}", task.id)
                if code != 0:
                    feedback = "TESTS FAILED. Fix the implementation. Captured test output:\n" + test_output[-7000:]
                    if attempt < max_revisions:
                        continue
                    raise WorkspaceError("Tests failed after the configured revision limit.")
                task.status = "reviewing"
                diff = workspace.diff(worktree, branch_base)
                review = self._complete(
                    "reviewer",
                    f"Review this task independently. Goal: {run.goal}\nTask: {task.title}\nAcceptance criteria: {task.description}\n"
                    f"Allowed paths: {json.dumps(allowed)}\nTest evidence (exit code 0):\n{test_output[-5000:]}\n\nPatch:\n{diff[-18000:]}\n\n"
                    "If no blocking correctness, security, or regression issue remains, begin your response with exactly APPROVED. "
                    "Otherwise begin with CHANGES_REQUESTED and list actionable findings by severity.",
                    temperature=0.0,
                )
                task.review_output = review[:10000]
                self._emit(run, "reviewer", "review", review[:8000], task.id)
                self._emit(run, "reviewer", "message", review[:8000], task.id, recipient="implementer")
                if review.lstrip().startswith("APPROVED"):
                    task.commit_sha = workspace.commit(worktree, f"feat({task.id}): {task.title}")
                    task.status = "passed"
                    self._emit(run, task.owner, "commit", f"Committed {task.commit_sha} on {task.branch}.", task.id)
                    return task
                feedback = "INDEPENDENT REVIEW REQUESTED CHANGES:\n" + review[-7000:]
                if attempt >= max_revisions:
                    raise WorkspaceError("Independent review did not approve within the revision limit.")
            raise WorkspaceError("Task did not reach a verified state.")
        except Exception as exc:
            task.status = "failed"
            self._emit(run, task.owner, "error", f"{type(exc).__name__}: {str(exc)[:3000]}", task.id)
            return task

    def execute(self, run_id: str, request: DeveloperRunRequest) -> None:
        run = self.get_run(run_id)
        if run is None:
            return
        try:
            run.status = "planning"
            workspace = GitWorkspace(run.repo_path, run.id)
            workspace.ensure_clean_base(run.base_branch)
            self._emit(run, "orchestrator", "status", "Repository is clean; preparing task plan.")
            run.tasks = self._plan_tasks(run, request)
            waves = self._topological_waves(run.tasks)
            run.status = "running"
            task_branches: dict[str, str] = {}
            for wave in waves:
                # A task with dependencies starts from its last declared dependency branch,
                # while independent tasks in this wave run concurrently.
                futures = {}
                with ThreadPoolExecutor(max_workers=min(request.max_agents, len(wave))) as pool:
                    for task in wave:
                        parent_branch = task_branches.get(task.depends_on[-1], run.base_branch) if task.depends_on else run.base_branch
                        futures[pool.submit(self._run_task, run, task, workspace, parent_branch, request.max_revisions)] = task
                    for future in as_completed(futures):
                        task = future.result()
                        if task.status == "passed":
                            task_branches[task.id] = task.branch
                if any(task.status != "passed" for task in wave):
                    run.status = "failed"
                    run.error = "At least one task failed review or verification; integration was not attempted."
                    return

            run.status = "integrating"
            integration_path = workspace.create_integration(run.integration_branch, run.base_branch)
            for wave in waves:
                for task in wave:
                    workspace.merge_branch(task.branch, integration_path)
                    self._emit(run, "integrator", "merge", f"Merged {task.branch} into {run.integration_branch}.", task.id)
            code, output = workspace.run_tests(integration_path, request.test_command)
            self._emit(run, "tester", "test", f"Integration suite exit code: {code}\n{output[-8000:]}")
            if code != 0:
                run.status = "failed"
                run.error = "Full integration test suite failed; base branch was not merged."
                return
            run.final_commit = workspace._git(["rev-parse", "HEAD"], cwd=integration_path)
            if request.auto_merge:
                run.final_commit = workspace.merge_to_base(run.integration_branch, run.base_branch)
                run.status = "completed"
                self._emit(run, "integrator", "merge", f"Explicit auto_merge enabled; merged into {run.base_branch} at {run.final_commit}.")
            else:
                run.status = "needs_approval"
                self._emit(run, "integrator", "status", f"Integration passed. Review and approve local merge of {run.integration_branch} into {run.base_branch}. No remote push was performed.")
        except Exception as exc:
            run.status = "failed"
            run.error = f"{type(exc).__name__}: {str(exc)[:3000]}"
            self._emit(run, "orchestrator", "error", run.error)
        finally:
            run.updated_at = datetime.now(timezone.utc)
