# ForgeClaw

ForgeClaw is a free-first, self-hostable multi-agent workspace for knowledge-grounded debate and collaborative coding.

## Current MVP

- FastAPI API for debate sessions and SQLite persistence
- Bounded proposal → critique → revision → decision workflow
- Deterministic demo mode that runs without a model API key
- OpenAI-compatible `/chat/completions` adapter for hosted gateways and local compatible servers
- Separate core instructions and role prompts for architect, critic, and judge
- GitHub Actions test workflow

**Model mode selection:** if `LLM_BASE_URL` and `LLM_MODEL` are set, ForgeClaw uses the configured model. Otherwise it uses deterministic demo agents. A configured provider failure returns HTTP 502; it does not silently pretend the demo was a live model response.

## Quick start

Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn forgeclaw.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## Configure a model

Edit the local `.env` file:

```dotenv
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your-key-if-required
LLM_MODEL=your-model-id
LLM_TIMEOUT_SECONDS=60
```

The base URL must be the API root that exposes `POST {LLM_BASE_URL}/chat/completions`. This is a compatibility contract, not a claim that every provider uses the same URL or request schema. For a local server, use its actual reachable base URL; the API key may be blank if the server does not require one.

Never commit real keys. Do not expose the API publicly without authentication and TLS.

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

## Prompt library

- `prompts/system.md`: shared rules for evidence, uncertainty, safety, and verification
- `prompts/roles/architect.md`: design and acceptance criteria
- `prompts/roles/critic.md`: independent adversarial review
- `prompts/roles/judge.md`: evidence-weighted synthesis

The prompts are original ForgeClaw instructions informed by public documentation and source code; they are not claimed to be exact copies of any vendor's private system prompt. See [prompt sources and design notes](docs/PROMPT_SOURCES.md).

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
- [x] OpenAI-compatible model provider
- [x] Role-specific prompt library
- [ ] Per-agent model and temperature configuration
- [ ] Obsidian read/search adapter
- [ ] Draft-only Obsidian decision-note writer
- [ ] Session UI and approval queue
- [ ] Isolated Git worktrees for coding agents
- [ ] Independent code review and test-result capture

## Security

Treat retrieved documents and tool output as untrusted input. Do not expose this API publicly without authentication and TLS. Never commit API keys, Obsidian tokens, or private Vault content. Keep agent and Obsidian endpoints on a private network or authenticated tunnel.
