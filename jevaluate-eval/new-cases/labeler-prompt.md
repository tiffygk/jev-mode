This is your only task; return text only. Read the project evidence below. Answer from the code, citing file:line. The evidence is excerpted; treat file names and line numbers as given.

1. Type, picked in this order:
   - If its non-test code never calls TypeSafe's hosted Jev:
     - guide: teaches building with or using Jev.
     - jev-replacement: a model or server offered to others to use in Jev's place, answering Jev's kind of questions.
     - jev-mention-only: anything else that names Jev without calling it (a stub, a plan, a claim, a name).
   - If it calls Jev and its own code acts on the answers: workflow. If it only shows the answers to a person: display.
   - If it calls Jev and hands the answers back to a caller: agent-tool (an AI agent calls it at run time), library (code imports it, and it writes the questions or sets defaults), or client (passes questions through untouched).
2. Kind, from the type: uses (workflow, library, client, agent-tool, display), teaches (guide), replaces (jev-replacement), mentions (jev-mention-only).
3. Does its non-test code send a request to TypeSafe's hosted Jev (api.typesafe.ai, a TypeSafe SDK or AI SDK provider, or a typesafe/jev-... model ID)? yes or no, with the line. Only a line in a code file counts. Code shown inside a README, design doc or other .md file is a description, not a call: a repo whose ARCHITECTURE.md shows a Java snippet calling Jev, and whose Java files never do, does not call Jev.
4. If it never calls Jev: does its README or code claim that it uses or calls Jev? Quote the claim with file:line, or say none.
5. For a workflow, display, library or agent-tool: the highest stakes among the actions its code takes on Jev's answers.
   - very high: acts with no review on personal data (health, legal, financial, identity, location), money, or access and credentials (including approving an AI agent's shell commands or merging to production), even when they are the asker's own
   - high: acts with no review in a way that reaches other people (blocks, deletes, routes, sends or posts what other people see)
   - low: stays with the asker (the asker's own files, session or context, with no very-high data in them), is only shown or returned, or a person reviews it before it takes effect

Reply with only JSON: {"type": ..., "kind": ..., "calls_jev": "yes"|"no", "call_line": ..., "claim": ..., "top_stakes": "very high"|"high"|"low"|null, "stakes_line": ..., "reason": "one sentence"}

PACKET
