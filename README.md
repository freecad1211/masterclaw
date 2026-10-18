# ForgeClaw

ForgeClaw is a free-first, self-hostable multi-agent workspace for knowledge-grounded debate and collaborative coding.

## MVP scope

- FastAPI service for debate sessions
- Role-separated agent interface (architect, critic, judge)
- SQLite persistence for debate records
- Deterministic demo agents so the flow can be tested without an API key
- Planned adapters for OpenAI-compatible model APIs and Obsidian

> The current demo provider is deterministic scaffolding, not a real LLM. Model and Obsidian integrations are the next milestones.

## Quick start

Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn forgeclaw.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## Test

```bash
pytest
```

## API

- `GET /health`
- `POST /api/v1/debates`
- `GET /api/v1/debates`
- `GET /api/v1/debates/{debate_id}`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/debates \
  -H 'Content-Type: application/json' \
  -d '{"topic":"How should ForgeClaw store agent decisions?","max_rounds":2}'
```

## Design principles

1. Orchestration owns workflow; agents return structured messages.
2. Independent proposals precede critique to reduce anchoring.
3. Decisions consider evidence, requirements, risk, and tests—not majority vote.
4. Separate facts, hypotheses, and decisions; preserve source provenance.
5. Least privilege by default; privileged shell, write, deployment, and external-send actions require scoped approval.
6. Bound rounds, timeouts, retries, and budgets.
7. Never claim tests passed without recording actual results.

## Roadmap

- [x] API skeleton and SQLite persistence
- [x] Deterministic debate flow for integration tests
- [ ] OpenAI-compatible model provider
- [ ] Per-agent model/system-prompt configuration
- [ ] Obsidian read/search adapter
- [ ] Draft-only Obsidian decision-note writer
- [ ] Session UI and approval queue
- [ ] Isolated Git worktrees for coding agents
- [ ] Independent code review and test-result capture

## Security

Do not expose this API publicly without authentication and TLS. Never commit API keys, Obsidian tokens, or private Vault content. Keep agent and Obsidian endpoints on a private network or authenticated tunnel.
