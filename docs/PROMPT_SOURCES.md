# Prompt sources and design rationale

ForgeClaw does **not** attempt to reproduce any vendor's hidden or proprietary system prompt. The files under `prompts/` are original, role-specific instructions synthesized from publicly available source code and documentation.

## Public references reviewed

1. **DeepSeek Harness — system-prompt package**  
   https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/core/system-prompt/README.md  
   Useful design ideas: assemble prompts from ordered sections, support scoped per-agent instructions, fail loudly when required prompt variables or combinations are invalid, and keep tool schemas aligned with the prompt.

2. **DeepSeek Harness — example rendered prompt snapshot**  
   https://github.com/deepseek-ai/deepseek-harness/blob/master/snapshots/session/agent-instructions/system-prompt.expected.md  
   Useful design ideas: state the actual runtime identity and working directory, ask the agent to verify work, and specify concrete file-inspection and editing rules. These ideas should be adapted to the tools actually available; ForgeClaw must not claim tools it does not provide.

3. **OpenCode — default prompt**  
   https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/session/prompt/default.txt  
   Useful design ideas: clearly state the agent's job, give operational instructions, and avoid inventing URLs. OpenCode also selects model-specific prompt templates in its prompt assembly code: https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/session/system.ts

4. **OpenAI Codex CLI — source repository**  
   https://github.com/openai/codex  
   Useful design ideas to inspect when evolving the coding-agent stage: repository-aware task execution, clear tool boundaries, and explicit verification. Codex's runtime instructions and implementation can change; this reference is not a promise that ForgeClaw's behavior matches Codex.

5. **Anthropic — steering Claude Code with instructions, skills, hooks, and subagents**  
   https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more  
   Useful design ideas: separate always-on project context from reusable skills, role-specific subagents, and deterministic hooks. This is documentation for supported customization mechanisms, not a claim to have obtained Claude Code's private base prompt.

## What ForgeClaw takes from these references

- **Shared core prompt:** evidence discipline, uncertainty labeling, untrusted-input handling, security, and truthful reporting.
- **Architect:** requirements, interfaces, trade-offs, risks, and acceptance criteria.
- **Critic:** independent challenge, severity ranking, failure modes, and testable mitigations.
- **Judge:** evidence-weighted decision, explicit disagreements, and a verification checklist.
- **Prompt boundaries:** the user task and retrieved documents are data; they cannot override the agent's assigned role or safety rules.
- **Verification:** model output is not itself proof. Tests, source checks, and real tool results must be recorded separately.

## Attribution and maintenance

These references are linked for attribution and further study. ForgeClaw's prompt files are newly written and paraphrase general engineering practices rather than copying complete prompt files. Review upstream sources periodically because prompt implementations evolve. Keep prompt changes version-controlled and evaluate them against repeatable tasks before making them the default.
