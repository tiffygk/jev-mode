"""Warn when this skill's copy of jev-rules.md differs from Jevaluate's, if Jevaluate is installed.

Usage: python rules_sync.py      (exit code 0 either way; it only warns)
The rules started in Jevaluate; Jev Lens ships a copy so it works on its own.
Standard library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "jev-rules.md"
CANDIDATES = [HERE.parent.parent / "jevaluate" / "jev-rules.md",
              Path.home() / ".claude" / "skills" / "jevaluate" / "jev-rules.md"]


def main():
    other = next((p for p in CANDIDATES if p.exists() and p.resolve() != HERE), None)
    if other is None:
        print("Jevaluate not installed; using this skill's own jev-rules.md.")
    elif other.read_text(encoding="utf-8") != HERE.read_text(encoding="utf-8"):
        print(f"WARNING: jev-rules.md differs from {other}. The newer file wins; copy it over the older one.")
    else:
        print("jev-rules.md matches Jevaluate's copy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
