import importlib, os, sys
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
HF_AT_COLLECTION = os.environ.get("HF_HOME")


def test_a_temp_library_import_sets_hf_home_inside_the_temp_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.delenv("HF_HOME", raising=False)
    for n in ("paths", "semantic"):
        sys.modules.pop(n, None)
    importlib.import_module("semantic")
    assert os.environ["HF_HOME"].startswith(str(tmp_path))


def test_the_next_test_sees_hf_home_as_it_was_before_the_temp_import():
    assert os.environ.get("HF_HOME") == HF_AT_COLLECTION
