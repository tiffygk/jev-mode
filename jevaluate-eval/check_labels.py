"""Blind labeler answers pass the same call-line rule `library.py check` applies to ratings, before they are sealed.
A "calls Jev: yes" label must cite path:line in a code file (not .md, .txt, docs/ or tests/) that the packet shows
making a hosted call (not an import, comment, dependency, throw or declaration). A "no" label must name each file the packet shows making a call.

  check_labels.py check <packet.md> <label.json>     print refusals, exit 1 if any
  check_labels.py run <prompt.md> <packet.md> <out.json>   run the labeler (headless, no tools); on a refusal,
                                                     rerun once with the refusal appended; both answers are kept
"""
import json, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "jevaluate" / "scripts")); sys.path.insert(0, str(HERE))
import jev_callsites, library, build_cards

CMD = ["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "", "--model", "claude-sonnet-5-5",
       "--effort", "medium", "--output-format", "json"]

def call_lines(packet):
    """{path: [line numbers]} of hosted-call lines in the packet's non-test code files (the shared jev_callsites.calls_in rule)."""
    return jev_callsites.calls_in(build_cards.parse(packet).items())

def citable_lines(packet):
    """{path: [line numbers]} an F0 yes may cite (the shared jev_callsites.citable_in rule)."""
    return jev_callsites.citable_in(build_cards.parse(packet).items())

def citable_paths(packet):
    return list(build_cards.parse(packet))

def problems(label, packet):
    calls, value = call_lines(packet), str(label.get("calls_jev", "")).strip().lower()
    cite_text = str(label.get("call_line") or "")
    shown = ", ".join(f"{p}:{n[0]}" for p, n in calls.items()) or "none"
    if value == "yes":
        cites = [(m.group(1), int(m.group(2))) for m in library.CITE.finditer(cite_text)]
        if not cites: return [f"calls Jev is yes but call_line cites no path:line; cite the code line that makes the call (lines the packet shows calling: {shown})"]
        code = [(f, n) for f, n in cites if library.is_code_cite(f)]
        if not code:
            return [f"calls Jev is yes but {', '.join(f'{f}:{n}' for f, n in cites)} is not a code file (a README, design doc or other .md file "
                    f"describes code, it doesn't run it); cite a code line that makes the call, or answer no (lines the packet shows calling: {shown})"]
        citable = citable_lines(packet)
        if not any(library.same_file(f, p) for f, _ in code for p in citable_paths(packet)):
            return [f"calls Jev is yes but {', '.join(f'{f}:{n}' for f, n in code)} is not a file in the packet; cite a file the packet shows (lines the packet shows calling: "
                    + (", ".join(f"{p}:{n[0]}" for p, n in citable.items()) or "none") + ")"]
        if not library.cites_a_call(code, citable):
            shown = ", ".join(f"{p}:{n[0]}" for p, n in citable.items()) or "none"
            return [f"calls Jev is yes but {', '.join(f'{f}:{n}' for f, n in code)} is not a hosted call (an import, comment, dependency, throw, declaration or regex does not count; "
                    f"cite the line that creates the client, posts to api.typesafe.ai, names the model ID or calls it); lines the packet shows calling: {shown}"]
        return []
    if value == "no":
        said = cite_text + " " + str(label.get("reason") or "")
        missing = [p for p in calls if not library.no_reasoned(said, p)]
        if missing: return [f"calls Jev is no but the packet shows calls in {', '.join(f'{p}:{calls[p][0]}' for p in missing)}; name each file followed by at least three words on why it is not the project calling Jev, or answer yes"]
        return []
    return [f"calls Jev is '{value}'; answer yes or no"]

def parse_label(stdout):
    d = json.loads(stdout); m = re.search(r"\{.*\}", d.get("result") or "", re.S)
    return json.loads(m.group(0)) if m else {}

def run(prompt_file, packet_file, out):
    packet = pathlib.Path(packet_file).read_text(); prompt = pathlib.Path(prompt_file).read_text().replace("PACKET", packet)
    first = subprocess.run(CMD, input=prompt, capture_output=True, text=True).stdout
    record = {"first": json.loads(first), "refusals": problems(parse_label(first), packet)}
    if record["refusals"]:
        retry = prompt + "\n\nYour previous answer was refused by the call-line check:\n- " + "\n- ".join(record["refusals"]) + "\nAnswer again, in the same JSON."
        second = subprocess.run(CMD, input=retry, capture_output=True, text=True).stdout
        record["second"] = json.loads(second); record["second_refusals"] = problems(parse_label(second), packet)
    pathlib.Path(out).write_text(json.dumps(record, indent=1))
    tok = sum(sum(r.get("usage", {}).get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
              for r in (record["first"], record.get("second", {})))
    print(f"{out}: {'refused, rerun once' if record['refusals'] else 'passed'}; tokens {tok}")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["check"] and len(a) == 3:
        ps = problems(json.loads(pathlib.Path(a[2]).read_text()), pathlib.Path(a[1]).read_text()); print("\n".join(ps) or "ok"); sys.exit(1 if ps else 0)
    elif a[:1] == ["run"] and len(a) == 4: run(*a[1:])
    else: print(__doc__); sys.exit(0 if a[:1] in (["-h"], ["--help"]) else 2)
