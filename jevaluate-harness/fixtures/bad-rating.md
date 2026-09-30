---
project: ticket-router
url: https://github.com/example/ticket-router
owner: example
rated: 2026-09-29
rubric: 2026-09-29
commit: abc123def456789
depth: full
lineage: new
stages: [data-prep, question-state, execution, decision]
closes_loop: none
verdict: 4
scores: {execution: 3, fit: 3, coverage: 3, evidence: 2}
via: direct
project_type: guide
rater: claude-sonnet-5-5
effort: medium
kind: teaches
verdict_1_code: none
citation: none
top_stakes: low
---
## Summary
Invented example for release checks: a workflow that routes support tickets with one Jev call per ticket.
## Decisions
- flag unclear commit | Noul | low | acts at src/x.py:9 | shows the flag to the author
## Facts (with evidence)
- F0 Calls hosted Jev -- yes. Builds the client and calls it (src/x.py:5)
- F1 check1 -- yes. evidence:1
- F2 check2 -- yes. evidence:2
- F3 check3 -- yes. evidence:3
- F4 check4 -- yes. evidence:4
- F5 check5 -- yes. evidence:5
- F6 check6 -- yes. evidence:6
- F7 check7 -- yes. evidence:7
- F8 check8 -- yes. evidence:8
- F9 check9 -- yes. evidence:9
- F10 check10 -- yes. evidence:10
- F11 check11 -- yes. evidence:11
- F12 check12 -- yes. evidence:12
- F13 check13 -- n.a. No high or very high Choice
- F14 check14 -- yes. evidence:14
- F15 check15 -- yes. evidence:15
- F16 check16 -- yes. evidence:16
- F17 check17 -- yes. evidence:17
- F18 check18 -- yes. evidence:18
- F19 check19 -- yes. evidence:19
- F20 check20 -- yes. evidence:20
- F21 check21 -- yes. evidence:21
- F22 check22 -- yes. evidence:22
- F23 check23 -- yes. evidence:23
## Verdict and reasoning
Test fixture.
