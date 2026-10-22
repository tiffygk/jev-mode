import glob, hashlib, json, os, subprocess, sys
import pytest

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks", "jev-ledger.py")

ROUTE_OUT = """Question: can a widget hold forty slots?  [limits a design: read in full]
Topics matched: invented topic
READ FULL | reference rule   | docs/invented__widgets.md#Slots per widget | 120 tok
          python3 /x/scripts/read.py 'docs/invented__widgets#1'
EXTRACT   | cookbook example | cookbooks/invented_demo.md#Demo layout | 900 tok NEEDS jev-9.9 | EXPERIMENTAL: invented note
          python3 /x/scripts/read.py 'cookbooks/invented_demo#2'
READ FULL | pattern          | patterns/invented.md#Fan (out) with | pipe | 55 tok | NEEDS jev-9.9
          python3 /x/scripts/read.py 'patterns/invented#0'
READ FULL items: read every one with read.py before any claim.
semantic: on
"""
READ_OUT = """SOURCE: docs/invented__widgets.md#Slots per widget | KIND: reference rule | READ: full
(lines 3-9, ~120 tokens)

Widgets hold slots.
"""
JEV_OUT = """CITE AS: docs/invented__widgets.md#Slots per widget (reference rule)
SOURCE: docs/invented__widgets.md#Slots per widget | KIND: reference rule | READ: full
(lines 3-9, ~120 tokens)

body

CITE AS: cookbooks/invented_demo.md#Demo (layout) (cookbook example) | NEEDS jev-9.9
SOURCE: cookbooks/invented_demo.md#Demo (layout) | KIND: cookbook example | READ: full
body
NOT YET READ (past the bundle cap; read it yourself): python3 /x/scripts/read.py 'docs/other#3'  # docs/other.md#Not read
EXTRACT (claims from it are unverified until read in full): python3 /x/scripts/read.py 'docs/other#4'
semantic: on
"""


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.delenv("JEV_LOG", raising=False)  # conftest turns the log off; these tests need it on
    d = tmp_path / "data"
    monkeypatch.setenv("JEV_SOURCES_DATA", str(d))
    return d


def fire(payload, raw=None):
    r = subprocess.run([sys.executable, HOOK], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env=os.environ.copy())
    return r


def payload(cmd, out, session="sess-invented-1", resp_dict=True):
    resp = {"stdout": out, "stderr": ""} if resp_dict else out
    return {"session_id": session, "cwd": "/tmp/invented", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "tool_response": resp}


def lines(d):
    out = []
    for f in glob.glob(str(d / "logs" / "ledger" / "*.jsonl")):
        out += [json.loads(x) for x in open(f)]
    return out


def test_route_output_gives_routed_refs_with_depth(data):
    r = fire(payload('python3 ~/x/jev-sources/scripts/route.py "can a widget hold forty slots?"', ROUTE_OUT))
    assert (r.returncode, r.stdout) == (0, "")
    [row] = lines(data)
    assert row["event"] == "routed" and row["session"] == "sess-invented-1" and row["cwd"] == "/tmp/invented"
    assert row["ts"].endswith("Z")
    assert row["refs"] == ["docs/invented__widgets.md#Slots per widget (READ FULL)",
                           "cookbooks/invented_demo.md#Demo layout (EXTRACT)",
                           "patterns/invented.md#Fan (out) with | pipe (READ FULL)"]


def test_read_output_gives_read_refs(data):
    fire(payload("python3 /any/where/scripts/read.py 'docs/invented__widgets#1'", READ_OUT))
    [row] = lines(data)
    assert row["event"] == "read" and row["refs"] == ["docs/invented__widgets.md#Slots per widget"]


def test_jev_output_gives_read_refs_once_each_and_ignores_unread(data):
    fire(payload('cd x && python3 s/scripts/jev.py "q" --docs-words "w"', JEV_OUT))
    [row] = lines(data)
    assert row["event"] == "read"
    assert row["refs"] == ["docs/invented__widgets.md#Slots per widget", "cookbooks/invented_demo.md#Demo (layout)"]


def test_extract_read_is_not_a_read(data):
    out = "SOURCE: docs/a.md#B | KIND: reference rule | READ: extract, not a full read\n"
    fire(payload("python3 scripts/read.py 'docs/a#1' --extract foo", out))
    assert lines(data) == []


def test_string_tool_response(data):
    fire(payload("python3 scripts/read.py 'docs/invented__widgets#1'", READ_OUT, resp_dict=False))
    assert lines(data)[0]["refs"] == ["docs/invented__widgets.md#Slots per widget"]


def test_other_commands_write_nothing(data):
    for cmd in ["ls -la", "python3 scripts/build_index.py", "cat notes/jev.py.txt", "python3 scripts/route_check.py"]:
        fire(payload(cmd, ROUTE_OUT))
    assert lines(data) == []


def test_no_refs_in_output_writes_nothing(data):
    fire(payload("python3 scripts/route.py 'q'", "no section found; refresh the library"))
    assert lines(data) == []


def test_missing_session_writes_nothing(data):
    for s in (None, ""):
        fire(payload("python3 scripts/read.py 'x'", READ_OUT, session=s))
    assert lines(data) == []


def test_session_id_is_hashed_into_ledger_folder(data):
    fire(payload("python3 scripts/read.py 'x'", READ_OUT, session="../../x"))
    name = hashlib.sha1(b"../../x").hexdigest()[:16] + ".jsonl"
    assert os.path.exists(data / "logs" / "ledger" / name)
    assert [p for p in data.rglob("*.jsonl")] == [data / "logs" / "ledger" / name]


def test_same_session_appends_to_one_file(data):
    fire(payload("python3 scripts/route.py 'q'", ROUTE_OUT))
    fire(payload("python3 scripts/read.py 'x'", READ_OUT))
    assert [r["event"] for r in lines(data)] == ["routed", "read"]


@pytest.mark.parametrize("raw", ["", "not json", "[1, 2]", "null", '{"session_id": "s", "tool_input": "str"}',
                                 '{"session_id": "s", "tool_input": {"command": 5}, "tool_response": 7}',
                                 '{"session_id": "s", "tool_input": {"command": "read.py x"}, "tool_response": {"stdout": null}}'])
def test_malformed_payloads_never_raise_or_print(data, raw):
    r = fire(None, raw=raw)
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")
    assert lines(data) == []


def test_unwritable_folder_never_raises_or_prints(tmp_path, monkeypatch):
    monkeypatch.delenv("JEV_LOG", raising=False)
    blocker = tmp_path / "file"
    blocker.write_text("x")
    monkeypatch.setenv("JEV_SOURCES_DATA", str(blocker / "sub"))  # a path under a regular file cannot be created
    r = fire(payload("python3 scripts/read.py 'x'", READ_OUT))
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")


def test_jev_log_off_writes_nothing(data, monkeypatch):
    monkeypatch.setenv("JEV_LOG", "off")
    fire(payload("python3 scripts/read.py 'x'", READ_OUT))
    assert lines(data) == []


def test_plugin_registers_ledger_on_bash():
    # The plugin's hooks live in the marketplace entry: its source is the repo root, so Codex finds the skill folder.
    market = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HOOK))), ".claude-plugin", "marketplace.json")
    [plugin] = [p for p in json.load(open(market))["plugins"] if p["name"] == "jev-sources"]
    [entry] = plugin["hooks"]["PostToolUse"]
    assert entry["matcher"] == "Bash" and "jev-ledger.py" in entry["hooks"][0]["command"]


def test_plugin_hook_commands_point_at_files_that_exist():
    root = os.path.dirname(os.path.dirname(os.path.dirname(HOOK)))
    [plugin] = [p for p in json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json")))["plugins"]
                if p["name"] == "jev-sources"]
    assert plugin["source"] == "./" and plugin["skills"] == ["./jev-sources"]
    for event in plugin["hooks"].values():
        for entry in event:
            for h in entry["hooks"]:
                rel = h["command"].split("${CLAUDE_PLUGIN_ROOT}/")[1].rstrip('"')
                assert os.path.exists(os.path.join(root, rel)), rel
