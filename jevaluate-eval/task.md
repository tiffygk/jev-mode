You are applying the jevaluate skill in your instructions. These are the routing calls a rater makes before scoring anything (rubric.md, section 1); a wrong call changes everything scored after it. Do not rate the projects. For each project below, answer only these, with the rubric's allowed values:

1. project_type.
2. calls_jev: yes, no or n.a.; with traced_line, the path:line in a code file (not .md, .txt, docs/ or tests/) or the capture that traces the request, when yes; or one line on why the evidence shows no call.
3. citation: the exact claim to use or call Jev, with file:line, or "none".
4. verdict_1_code: the code routing alone decides, or "none". A guide is 1t (Guide, not yet rated).
5. decisions: each decision Jev makes, written as the rating's line "- <decision> | <Noul, Choice or Score> | <very high, high or low> | acts at <file:line> | <what code does with the answer>"; empty for a client, guide, jev-replacement or jev-mention-only.
5b. top_stakes: the highest stakes among the decisions the grader reads (very high | high | low); never n.a. (code works that out for a client, a guide and any project routed to 1a, 1b, 1c, 1r or 1t).
6. For a jev-mention-only only: type_best_match, code_functionality, replaces_jev, intended_call.

Reply with only a JSON array: [{"project": ..., "project_type": ..., "calls_jev": ..., "traced_line": ..., "citation": ..., "verdict_1_code": ..., "decisions": [{"decision": ..., "primitive": ..., "stakes": ..., "acts_at": ..., "reason": ...}], "top_stakes": ..., "type_best_match": ..., "code_functionality": ..., "replaces_jev": ..., "intended_call": ...}]

The evidence below is excerpted; treat file names and line numbers as given.
