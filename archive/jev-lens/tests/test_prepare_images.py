import json
import sys
from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from prepare_images import main  # noqa: E402


def make_jpeg_with_exif(path):
    im = Image.new("RGB", (40, 20), "red")
    exif = Image.Exif()
    exif[0x010E] = "Two coworkers on a date"  # ImageDescription
    exif[0x0112] = 6  # Orientation: rotate 90 on display
    im.save(path, exif=exif.tobytes())


def test_strips_metadata_applies_rotation_renames(tmp_path):
    src = tmp_path / "in"; src.mkdir()
    make_jpeg_with_exif(src / "beach_date_with_bob.jpg")
    Image.new("RGBA", (5, 5)).save(src / "note.png", pnginfo=None)
    (src / "readme.txt").write_text("x")
    out = tmp_path / "run"
    assert main(["x", str(src), "--out", str(out)]) == 0
    files = sorted(p.name for p in (out / "images").iterdir())
    assert files == ["image_01.jpg", "image_02.png"]
    with Image.open(out / "images" / "image_01.jpg") as im:
        assert len(im.getexif()) == 0
        assert im.size == (20, 40)  # rotation baked into the pixels
        assert "exif" not in im.info
    manifest = json.loads((out / "manifest.json").read_text())
    assert sorted(manifest.values()) == files


def test_no_images_is_an_error(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    assert main(["x", str(tmp_path), "--out", str(tmp_path / "o")]) == 1
