# ForgeClaw architecture

## Runtime boundaries

- `api/`: HTTP validation and response mapping.
- `services/`: orchestration flow.
- `agents/`: role-specific behavior behind a shared protocol.
- `models/`: validated domain contracts.
- `storage/`: SQLite persistence.
- Planned `providers/`: model/API adapters.
- Planned `knowledge/`: Obsidian retrieval and draft-note adapters.
- Planned `execution/`: isolated worktrees, command allowlists, approvals, and test capture.

## Debate lifecycle

1. Validate the topic and cap the number of rounds.
2. Collect independent proposals to reduce anchoring.
3. Collect critiques and revisions.
4. Synthesize based on requirements, evidence, risks, and testability—not vote count.
5. Persist messages, decision, provenance, and unresolved questions.

The current demo agents are deterministic test fixtures. They are not real LLM calls and do not provide external evidence.

## Security model

- Read-only tools by default.
- Scope write access to explicit workspaces.
- Require approval for deployment, destructive changes, shell actions outside allowlists, and external sends.
- Keep model and Obsidian credentials in environment variables or a secret store.
- Do not expose the API outside a trusted network without authentication and TLS.

## Next milestones

1. Add an OpenAI-compatible chat-completions provider.
2. Configure each agent's model, system prompt, timeout, and retry policy.
3. Add Obsidian search/read with source references in agent messages.
4. Write results only to a draft folder; never silently overwrite canonical notes.
5. Add a session UI and approval queue.
6. Run coding agents in disposable Git worktrees and capture real test output.
