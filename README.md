# ForgeClaw

ForgeClaw is a free-first, self-hosted multi-agent workspace for research, collaborative coding, and evidence-based review.

## Features

- FastAPI API and SQLite-backed debate history
- OpenAI-compatible model adapter, with independent model selection per agent role
- Developer Mode with scoped tasks, parallel Git branches and worktrees, bounded revision loops, independent review, test capture, per-task commits, and integration branch
- Built-in skills for repository exploration, implementation, debugging, code review, Git integration, and secure tool use
- Built-in MCP stdio server for safe workspace inspection and allowlisted test commands
- Original role-specific prompts informed by public DeepSeek Harness, OpenCode, Codex, and Claude Code documentation

## Quick start

Python 3.11+

    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    cp .env.example .env
    uvicorn forgeclaw.main:app --reload

Open http://127.0.0.1:8000/docs. Before using Developer Mode, generate a strong token and set FORGECLAW_API_TOKEN in .env; the write/run/history/message/merge endpoints require an Authorization: Bearer token. For example, generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))".

## Model configuration

Set the default provider in .env:

    LLM_BASE_URL=https://your-provider.example/v1
    LLM_API_KEY=your-key-if-required
    LLM_MODEL=your-model-id
    LLM_TIMEOUT_SECONDS=60

The provider must expose POST {LLM_BASE_URL}/chat/completions. Use the exact API root and model identifier from your provider documentation. Local compatible endpoints may not need an API key.

Per-role overrides use FORGECLAW_AGENT_<ROLE>_BASE_URL, _API_KEY, and _MODEL. Supported role names are ARCHITECT, IMPLEMENTER, REVIEWER, TESTER, and INTEGRATOR. If a role override is empty, the global LLM_* settings are used. The profile API never returns API keys.

## Developer Mode API

- GET /api/v1/developer/profiles — configured role/model summary
- GET /api/v1/developer/skills — built-in skills
- GET /api/v1/developer/mcp-tools — built-in MCP tool catalog
- POST /api/v1/developer/runs — start a run
- GET /api/v1/developer/runs — list current-process runs
- GET /api/v1/developer/runs/{run_id} — run status, task status, events, reviews, test output, and commits\n- POST /api/v1/developer/runs/{run_id}/messages — append a directed agent-to-agent message\n- POST /api/v1/developer/runs/{run_id}/approve-merge — explicitly approve a verified integration branch for local merge

Every Developer Mode run/history/message/merge request must include the configured Bearer token in the Authorization header. Example request:

    {
      "goal": "Add a feature and cover it with tests",
      "repo_path": "/absolute/path/to/a/local/git/repository",
      "base_branch": "main",
      "max_agents": 3,
      "max_revisions": 2,
      "test_command": "auto",
      "auto_merge": false,
      "tasks": []
    }

If tasks is empty, the architect model must return a JSON task plan with unique IDs, dependencies, acceptance criteria, and non-empty allowed-path scopes. Alternatively, provide tasks explicitly. The task schema includes id, title, description, owner, depends_on, and allowed_paths.

Supported test command values: auto, pytest, python -m pytest, npm test, npm run lint, npm run build, pnpm test, pnpm lint, pnpm build, yarn test, yarn lint, yarn build, cargo test, go test ./..., and python -m compileall forgeclaw. Auto mode detects a supported project test command from the repository manifest.

## Developer workflow

1. The orchestrator verifies the repository is clean and checked out on the selected base branch.
2. The architect decomposes the goal into scoped tasks. Dependency-free tasks run concurrently, up to max_agents.
3. Each task receives its own feature/forgeclaw-<run>-<task> branch and isolated Git worktree.
4. The implementer returns a unified diff. ForgeClaw validates and applies it, then rejects any file outside the assigned scope.
5. The configured test command runs inside the worktree. A separate reviewer inspects the patch and captured test output.
6. Test failures or review findings are sent back to the implementer for a bounded number of revisions.
7. A task is committed only after tests pass and the reviewer returns APPROVED.
8. Passed branches are merged in dependency order into integration/forgeclaw-<run>, followed by a full integration test.
9. Default behavior is needs_approval: the integration branch remains available for inspection. Set auto_merge: true only when you explicitly want a successful run to merge locally into the selected base branch.

ForgeClaw never pushes to a remote or deploys. Merge conflicts stop the run for manual resolution. Local task worktrees and branches are retained for audit and recovery.

## Built-in MCP server

Run the stdio MCP server from the repository you want to inspect:

    FORGECLAW_MCP_WORKSPACE=/absolute/path/to/repo python -m forgeclaw.mcp_server

Built-in tools: workspace_tree, read_file, search_files, workspace_status, git_status, git_diff, and run_tests. Read tools block secret files and path traversal. Test execution accepts only a small allowlist; arbitrary shell commands are not exposed.

## Prompt library

- prompts/system.md — shared evidence, security, and verification rules
- prompts/roles/architect.md — architecture and task planning
- prompts/roles/implementer.md — isolated patch authoring
- prompts/roles/reviewer.md — independent code review
- prompts/roles/tester.md — test evidence and coverage analysis
- prompts/roles/integrator.md — branch integration and final verification
- prompts/roles/critic.md and prompts/roles/judge.md — debate workflow

References and design rationale: docs/PROMPT_SOURCES.md. These are original ForgeClaw prompts informed by public documentation; they are not claimed to be copies of proprietary vendor system prompts.

## Limitations and security

- Run state and event history are currently held in process memory; restarting the API loses run history, but Git branches and commits remain in the repository.
- Model output is text-based unified diffs rather than native model tool calls.
- The MCP server is intended for a trusted local workspace. Review any repository before allowing an agent to execute project test/build scripts.
- No authentication is included yet. Do not expose the API publicly without adding authentication and TLS.
- Never commit API keys, Obsidian tokens, or private Vault content.
- Obsidian integration, remote push/PR creation, deployment, cancellation, and UI are not implemented yet.

## Test

    pytest
