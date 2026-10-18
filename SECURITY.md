# Security Policy

## Supported versions

Security fixes target the latest code on the default branch. Pin a reviewed commit or release for deployments.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private repository content, or personal data. Use GitHub's private vulnerability reporting for this repository if enabled; otherwise contact the maintainers privately through a verified channel. Include impact, affected commit/version, reproduction steps, and a suggested mitigation where possible.

## Deployment baseline

- Keep the API on localhost or a private network unless it is behind TLS and an authenticated reverse proxy.
- Use a unique, high-entropy `FORGECLAW_API_TOKEN`; never place it in source control, URLs, screenshots, or logs.
- Use a dedicated OS account and mount only repositories the agent is allowed to modify.
- Run only trusted repositories: test/build scripts execute project code. Container isolation reduces host exposure but is not a substitute for a dedicated sandbox.
- Keep Docker read-only and non-root defaults unless a reviewed requirement needs otherwise.
- Back up the SQLite data volume and Git repositories; test restore procedures.
- Treat model prompts, generated patches, repository content, and agent event logs as untrusted input/output.
- Rotate provider credentials if exposure is suspected. Avoid putting secrets in task prompts or commit messages.
