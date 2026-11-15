"""Crop images (with fallback), sources page data and scientific-help texts."""
import re
from pathlib import Path

from modules.crop_rotation.crop_catalog import load_crops
from ui import crop_visuals as cv
from ui.translations import en, es

ROOT = Path(__file__).resolve().parent.parent
TOPICS = ("rec", "rot", "alerts", "water", "env")


def test_every_crop_has_a_visual_even_without_png(tmp_path, monkeypatch):
    monkeypatch.setattr(cv, "CROPS_DIR", tmp_path)  # empty folder: no PNGs at all
    for c in load_crops():
        html_ = cv.crop_thumb(c["id"], 56, c["name_en"])
        assert "fs-crop-fallback" in html_ and "<img" not in html_


def test_png_is_used_when_present_and_corrupt_png_falls_back(tmp_path, monkeypatch):
    from PIL import Image
    monkeypatch.setattr(cv, "CROPS_DIR", tmp_path)
    Image.new("RGB", (400, 300), (190, 150, 40)).save(tmp_path / "maiz.png")
    assert "data:image/png;base64," in cv.crop_thumb("maiz")
    (tmp_path / "frijol.png").write_bytes(b"not an image")
    assert "fs-crop-fallback" in cv.crop_thumb("frijol")


def test_unsafe_crop_id_never_reads_files():
    assert cv.crop_image_path("../secret") is None and cv.crop_image_path("a/b") is None


def test_readme_lists_every_crop_file():
    readme = (ROOT / "assets" / "crops" / "README.md").read_text(encoding="utf-8")
    for c in load_crops():
        assert f"{c['id']}.png" in readme


def test_science_texts_exist_in_both_languages():
    for lang in (en.TEXTS, es.TEXTS):
        for t in TOPICS:
            for part in ("short", "data", "how", "meaning", "limits"):
                assert lang.get(f"sci.{t}.{part}"), (t, part)
        for k in ("observation", "estimate", "forecast", "model", "user"):
            assert lang.get(f"sci.kind.{k}") and lang.get(f"sci.kind.{k}.desc")


def test_sources_page_data():
    import pytest
    pytest.importorskip("streamlit")
    from ui.pages import sources
    seen = set()
    for item in sources.SOURCES + sources.METHODS:
        for field in item["fields"]:
            for lang in (en.TEXTS, es.TEXTS):
                assert lang.get(f"src.{item['id']}.{field}"), (item["id"], field)
        for label, url in item["links"]:
            assert url.startswith("https://") and url not in seen
            assert label in en.TEXTS and label in es.TEXTS
            seen.add(url)
    # only sources that the code really uses
    assert "power.larc.nasa.gov" in "".join(seen) and "open-meteo.com" in "".join(seen)
    assert not re.search(r"smap|nsidc|sentinel|ecostress|copernicus", "".join(seen), re.I)
