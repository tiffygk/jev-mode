[← All ratings](README.md)

> **jkudish/jev-mcp** at [`fcd18d8`](https://github.com/jkudish/jev-mcp/tree/fcd18d8609ba05a2f1988af91407d86377801ca0) · agent tool
> ### Verdict 3: Use with a fix
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ○○○
>
> - This MCP server exposes twelve Jev judgment tools to agents, with typed questions and advisory probability-based actions.
> - It batches related questions, validates answers, and fails closed on malformed responses.
> - Instructions embedded in state and unmeasured performance claims limit the rating.

## What holds it back

- **Measured in workflow** (F7): README asserts 150–500 ms without a project-specific measured distribution or accuracy study ([`README.md:27`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L27)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Sample size adequate** (F15): The 150–500 ms claim supplies neither sample size nor measurement conditions ([`README.md:27`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L27)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **No instructions in state** (F21): State contains a directive-like `purpose` that tells Jev to verify each claim ([`src/server.ts:229`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L229)). https://docs.typesafe.ai/concepts/state

**Minor:** Pinned model (F12); Size limits respected (F14); Data as fields (F20); Untrusted text as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/jkudish__jev-mcp--gpt-6-sol.md)

