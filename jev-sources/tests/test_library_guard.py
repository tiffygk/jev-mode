"""The suite never writes into the library it is pointed at (conftest checks this at the end of the session)."""
import os
import stat
from conftest import copy_library, library_state


def make_lib(root):
    os.makedirs(os.path.join(root, "docs"))
    with open(os.path.join(root, "docs", "a.md"), "w") as f:
        f.write("# A\n")
    with open(os.path.join(root, "sections.jsonl"), "w") as f:
        f.write("{}\n")
    return root


def test_state_changes_when_a_page_folder_gains_a_file(tmp_path):
    lib = make_lib(str(tmp_path / "lib"))
    os.utime(os.path.join(lib, "docs"), ns=(1, 1))
    before = library_state(lib)
    open(os.path.join(lib, "docs", "b.md"), "w").write("# B\n")
    os.utime(os.path.join(lib, "docs", "b.md"), None)
    assert library_state(lib) != before


def test_state_changes_when_raw_appears(tmp_path):
    lib = make_lib(str(tmp_path / "lib"))
    before = library_state(lib)
    os.makedirs(os.path.join(lib, "raw"))
    assert library_state(lib)["raw"] is not None and library_state(lib) != before


def test_copy_of_a_read_only_library_is_writable(tmp_path):
    src = make_lib(str(tmp_path / "src"))
    os.chmod(os.path.join(src, "docs"), stat.S_IRUSR | stat.S_IXUSR)
    try:
        dst = copy_library(src, str(tmp_path / "dst"))
        open(os.path.join(dst, "docs", "new.md"), "w").write("x")  # would raise if permissions were copied
        assert open(os.path.join(dst, "docs", "a.md")).read() == "# A\n"
    finally:
        os.chmod(os.path.join(src, "docs"), stat.S_IRWXU)
