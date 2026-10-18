# Contributing

## Local checks

    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    pytest
    python -m compileall forgeclaw

## Pull request expectations

- Keep changes scoped and explain the user-visible impact.
- Add regression tests for behavior changes and failure paths.
- Never commit credentials, local databases, private repository content, or logs containing sensitive data.
- Treat model output as untrusted. Validate paths and patches before filesystem writes; do not add unrestricted shell execution.
- Document configuration changes in `.env.example` and README.
- Include test evidence and note any checks that could not run.
- Avoid enabling automatic merge, remote push, or deployment by default.
