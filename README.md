# ForgeClaw

ForgeClaw is a free-first, self-hosted multi-agent workspace for research, collaborative coding, and evidence-based review. It runs directly on your computer with Python; Docker is not required.

## Features

- FastAPI API and SQLite-backed debate history (WAL mode, bounded busy timeout)
- OpenAI-compatible model adapter, with independent model selection per agent role
- Developer Mode with scoped tasks, parallel Git branches and worktrees, bounded revision loops, independent review, test capture, per-task commits, and integration branch
- Browser-based Control Room at `/ui`: launch runs, monitor task state and agent events, inspect test/review output, and approve local integration merges
- Structured JSON logs to stdout and optional rotating file, request IDs, duration/status logging, secret redaction, health and readiness endpoints
- Built-in skills for repository exploration, implementation, debugging, code review, Git integration, and secure tool use
- Built-in MCP stdio server for safe workspace inspection and allowlisted test commands
- Original role-specific prompts informed by public DeepSeek Harness, OpenCode, Codex, and Claude Code documentation
- Native Python launcher that creates a virtual environment, installs dependencies, initializes a local API token, starts the server, and opens the dashboard

## One-click start (no Docker)

Requirements: Python 3.11 or newer and an internet connection for the first dependency installation.

- **macOS:** double-click `start.command`. If macOS blocks it, open Terminal in this folder and run `chmod +x start.command && ./start.command`.
- **Windows:** double-click `start.bat`. Install Python 3.11+ and enable the Python Launcher (`py`) first.
- **Linux / terminal:** run `python3 start.py`.

On first launch, ForgeClaw creates `.venv`, installs its Python dependencies, copies `.env.example` to `.env`, and generates a local `FORGECLAW_API_TOKEN` if one is not already configured. It then starts the server on `127.0.0.1:8000` and opens the Control Room at http://127.0.0.1:8000/ui. Keep the launcher terminal open while using the app; press Ctrl+C to stop it.

The launcher does not install or invoke Docker. The app runs as your current operating-system user, so only point Developer Mode at repositories you trust. Keep the dashboard on localhost; do not expose it publicly without a proper deployment boundary, TLS, and network access controls.

## Configure your model

Edit `.env` and set the default provider:

    LLM_BASE_URL=http://127.0.0.1:31415/v1
    LLM_API_KEY=your-key-if-required
    LLM_MODEL=auto:default
    LLM_TIMEOUT_SECONDS=60

Use the exact API root and model identifier supported by your OpenAI-compatible provider. Local compatible endpoints may not need an API key. The sample values above match a local OpenAI-compatible proxy only if it is listening on that address.

Per-role overrides use `FORGECLAW_AGENT_<ROLE>_BASE_URL`, `_API_KEY`, and `_MODEL`. Supported role names are ARCHITECT, IMPLEMENTER, REVIEWER, TESTER, and INTEGRATOR. Leave a role override empty to inherit the global `LLM_*` setting. The profile API never returns API keys.

## Production logging and health

Logs are newline-delimited JSON. By default, they go to stdout. Configure:

    FORGECLAW_LOG_LEVEL=INFO
    FORGECLAW_LOG_FILE=./logs/forgeclaw.jsonl
    FORGECLAW_LOG_MAX_BYTES=10485760
    FORGECLAW_LOG_BACKUP_COUNT=5

The optional file handler rotates at the configured byte limit and retains the configured number of backups. Logs include a request ID, method, path (not query string), response status, and duration. Authorization/API-key/token/password-like fields and common token patterns are redacted. Never place secrets in free-form error text; redaction is defense in depth, not a substitute for secret hygiene.

- `GET /health` — process liveness
- `GET /ready` — database connectivity readiness
- `X-Request-ID` — generated for each request and returned to clients; a supplied value is bounded and propagated
- `/ui` — same-origin dashboard; the Developer Mode API token is kept in the current browser tab's session storage

The dashboard polls run status every four seconds. The token is not persisted across browser sessions. For shared machines, remove it from the dashboard and close the tab after use.

## Developer Mode API

- GET /api/v1/developer/profiles — configured role/model summary
- GET /api/v1/developer/skills — built-in skills
- GET /api/v1/developer/mcp-tools — built-in MCP tool catalog
- POST /api/v1/developer/runs — start a run
- GET /api/v1/developer/runs — list current-process runs
- GET /api/v1/developer/runs/{run_id} — run status, task status, events, reviews, test output, and commits
- POST /api/v1/developer/runs/{run_id}/messages — append a directed agent-to-agent message
- POST /api/v1/developer/runs/{run_id}/approve-merge — explicitly approve a verified integration branch for local merge

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

Supported test command values: auto, pytest, python -m pytest, python -m compileall forgeclaw, npm test, npm run lint, npm run build, pnpm test, pnpm lint, pnpm build, yarn test, yarn lint, yarn build, cargo test, and go test ./.... Auto mode detects a supported project test command from the repository manifest.

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

ForgeClaw never pushes to a remote or deploys. Merge conflicts stop the run for manual resolution. Local task worktrees and branches are retained for audit and recovery. These Git worktrees are used for parallel agent development; no Docker execution sandbox is used.

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

## Harness and security boundaries

- CI runs the Python test suite on pushes and pull requests.
- Work is split into bounded tasks with explicit file scopes; generated patches are validated before application; tests and independent review gate commits.
- Default merge behavior requires human approval. Auto-merge is opt-in and only local.
- API run state and event history are persisted in SQLite; use Git branches and commits as the durable execution audit.
- The MCP server and test/build commands execute in a trusted local workspace. Review repositories before running their scripts.
- The dashboard token is held in session storage, not cookies; use only over localhost or behind a trusted HTTPS reverse proxy with access controls.
- Model output is text-based unified diffs rather than native model tool calls.
- No remote push, pull-request automation, deployment, cancellation, or Obsidian integration is implemented yet.
- Never commit API keys, Obsidian tokens, or private Vault content.

## Test

    pytest
