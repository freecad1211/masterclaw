# Developer Mode

Developer Mode coordinates scoped coding agents over isolated Git worktrees. Agents may draft patches and commit locally, but cannot push, deploy, or access arbitrary shell commands.

## Roles

- Architect: turns the goal into independent tasks with acceptance criteria and file ownership.
- Implementer: drafts a unified diff for one task in its own worktree.
- Reviewer: independently inspects the diff and requests changes when needed.
- Tester: inspects test evidence and coverage gaps.
- Integrator: orders passed branches, merges them into an integration branch, and reruns tests.

Each role can use a different OpenAI-compatible provider via environment variables FORGECLAW_AGENT_<ROLE>_BASE_URL, FORGECLAW_AGENT_<ROLE>_API_KEY, and FORGECLAW_AGENT_<ROLE>_MODEL. Unset role settings fall back to the global LLM_* provider. API keys are never returned by the profile endpoint.

## Workflow

1. Require a clean configured Git working tree before starting.
2. Plan tasks; task IDs, dependencies, and allowed paths are explicit.
3. Create a feature branch and separate Git worktree per task.
4. Request a patch from the implementer, validate it with git apply --check, and reject changes outside assigned paths.
5. Run allowlisted tests, request independent review, and retry within a configured limit.
6. Commit a task only after tests pass and review approves.
7. Merge passed task branches into integration/forgeclaw-<run-id> in dependency order. Conflicts stop the run rather than being guessed through.
8. Run the full test suite on the integration branch.
9. By default, stop at needs_approval. Local merge into the base branch requires explicit auto_merge=true, a clean original working tree, and a successful final test run. No remote push is performed.

## How Agents Modify Files and Execute Commands

- **File modifications**: Agents do not edit files directly. The Implementer role outputs a unified Git diff. The system validates the diff (no disallowed paths) and applies it with `git apply` inside an isolated Git worktree for the task.
- **Command execution**: Agents cannot run arbitrary shell commands. The system only allows a predefined allowlist of test and build commands (e.g., `pytest`, `npm test`) to be executed via the MCP `run_tests` tool or the internal workspace service. This ensures safety and reproducibility.

## Agent communication

Events form a run-scoped conversation log. Agents can read task status and prior feedback, and reviewer findings/test failures are passed back to the implementer. This is workflow messaging, not unrestricted free-form chat.

## Built-in skills

repo-exploration, implementation, test-driven-debugging, independent-code-review, git-integration, and secure-tool-use are registered in forgeclaw/services/skills.py.

## Built-in MCP server

Run python -m forgeclaw.mcp_server to expose workspace tree/read/search, Git status/diff, and allowlisted test execution as MCP tools over stdio. Configure FORGECLAW_MCP_WORKSPACE to the intended project root. The server blocks secret files and path traversal. Review your MCP client's trust model before connecting it to an untrusted repository.

## Limitations

- Implementers return unified diffs instead of using model-native tool calling.
- The server must have Git, project test dependencies, and a configured model provider installed.
- Failed review, tests, conflicts, missing model configuration, or invalid patches fail closed.
- No remote pushes, pull request creation, deployment, or arbitrary shell execution is implemented.
