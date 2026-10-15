import json, os, subprocess, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import private_text_check as ptc

SCRIPT = os.path.join(HERE, "private_text_check.py")
# Invented private values are assembled at runtime, so this file never holds a full attribution, a handle
# line or a copied run of words that a scan of this repo could mistake for the real thing.
RUN = "knab revir teiuq eht raen god yzal eht revo spmuj xof nworb kciuq eht"[::-1]
H = "alex" + "q"
DISC = "Disc" + "ord"
TS = "Type" + "Safe"
V1, V2, V3 = "sa" + "id", "report" + "ed", "to" + "ld"
PAT = "Pat" + " Example"
H3 = "S" + "EA"
WORDS = RUN.split()
SOURCE = (
    f"**21:04:34 · {H}:** {RUN}\n"
    f"**21:05:10 · {H3}:** nothing else of note was spoken at this point in the invented talk\n"
)


@pytest.fixture
def cfg(tmp_path):
    src = tmp_path / "source.md"
    src.write_text(SOURCE)
    path = tmp_path / "private.json"
    path.write_text(json.dumps({"sources": [str(src)], "names": [PAT]}))
    return str(path)


@pytest.fixture
def loaded(cfg):
    return ptc.load(cfg)


def hits(text, loaded):
    sh, names, handles = loaded
    return ptc.check(text, sh, names, handles)


def test_eight_copied_words_refused_with_line_number(loaded):
    text = "clean line\nWe saw " + ", ".join(WORDS[:8]).upper() + " today\n"
    assert [i for i, _ in hits(text, loaded)] == [2]


def test_seven_copied_words_pass(loaded):
    assert hits(" ".join(WORDS[:7]), loaded) == []


def test_name_refused_only_as_attribution(loaded):
    assert hits(f"{PAT} {V1} the limit is 64k", loaded)
    assert hits(f"the limit is 64k, accord" + f"ing to {PAT}", loaded)
    assert hits(f"{PAT}'s docs page", loaded) == []


def test_handle_refused_anywhere_when_four_plus_chars(loaded):
    assert hits(f"{H} mentioned it", loaded)
    assert hits(f"thanks {H}", loaded)
    assert hits(f"thanks {H.capitalize()}", loaded) == []  # case-sensitive


def test_short_handle_refused_only_as_attribution(loaded):
    assert hits(f"{H3} {V1} it is fine", loaded)
    assert hits("the sea is calm", loaded) == []
    assert hits(f"thanks {H3}", loaded) == []


def test_generic_attributions_refused(loaded):
    assert hits(f"a {DISC} user {V2} that it fails", loaded)
    assert hits(f"the {TS} team {V3} us it works", loaded)


def test_handle_used_as_a_github_owner_passes(loaded):
    assert hits(f"[{H}/jevtool]({H}__jevtool.md)", loaded) == []
    assert hits(f"see github.com/{H}/jevtool for it", loaded) == []
    assert hits(f"thanks {H}", loaded)


def test_plain_docs_statement_passes(loaded):
    assert hits("the docs say the limit is 64k", loaded) == []


def test_message_never_prints_private_text_or_name(loaded):
    text = f"{PAT} {V1} x\nthanks {H}\n{RUN}\n"
    for _, why in hits(text, loaded):
        for secret in (PAT.split()[0], PAT.split()[1], H, "quick", "fox"):
            assert secret not in why


def run(args, cfg_path, tmp_path):
    env = dict(os.environ, JEV_PRIVATE_CONFIG=cfg_path)
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True, env=env)


def test_cli_reports_file_and_line_and_exits_1(cfg, tmp_path):
    f = tmp_path / "page.md"
    f.write_text(f"ok\nthanks {H}\n")
    r = run([str(f)], cfg, tmp_path)
    assert r.returncode == 1
    assert r.stdout.startswith(f"{f}:2:")
    assert H not in r.stdout


def test_cli_clean_file_exits_0(cfg, tmp_path):
    f = tmp_path / "page.md"
    f.write_text("the docs say the limit is 64k\n")
    assert run([str(f)], cfg, tmp_path).returncode == 0


def test_missing_config_skips_without_flag_and_refuses_with_it(tmp_path):
    f = tmp_path / "page.md"
    f.write_text("anything\n")
    missing = str(tmp_path / "nope.json")
    assert run([str(f)], missing, tmp_path).returncode == 0
    assert run(["--require-config", str(f)], missing, tmp_path).returncode == 1


def test_unreadable_input_file_exits_1_with_a_note(cfg, tmp_path):
    r = run([str(tmp_path / "gone.md")], cfg, tmp_path)
    assert r.returncode == 1
    assert "gone.md" in r.stderr


def word_handle_cfg(tmp_path, monkeypatch, wordlist):
    BW = "Br" + "ave"  # invented handle that is also an ordinary word
    src = tmp_path / "wsource.md"
    src.write_text(f"**21:06:00 · {BW}:** a short invented remark\n")
    c = tmp_path / "wcfg.json"
    c.write_text(json.dumps({"sources": [str(src)], "names": []}))
    monkeypatch.setenv("JEV_WORD_LIST", str(wordlist))
    return BW, ptc.load(str(c))


def test_handle_that_is_an_english_word_is_refused_only_as_attribution(tmp_path, monkeypatch):
    wl = tmp_path / "words"
    wl.write_text("brave\nbold\n")
    BW, ld = word_handle_cfg(tmp_path, monkeypatch, wl)
    assert hits(f"{BW} design choices", ld) == []
    assert hits(f"{BW} {V1} it works", ld)
    assert ld[2] == []


def test_word_handle_keeps_the_bare_rule_when_no_word_list_exists(tmp_path, monkeypatch):
    BW, ld = word_handle_cfg(tmp_path, monkeypatch, tmp_path / "missing")
    assert hits(f"{BW} design choices", ld)


def test_non_word_handle_keeps_the_bare_rule_beside_a_word_list(tmp_path, monkeypatch, loaded):
    wl = tmp_path / "words"
    wl.write_text("brave\n")
    monkeypatch.setenv("JEV_WORD_LIST", str(wl))
    sh, names, handles = ptc.load(str(tmp_path / "private.json"))
    assert H in handles
    assert hits(f"thanks {H}", (sh, names, handles))
