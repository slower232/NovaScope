import re
from pathlib import Path
from ui.translations import en, es

ROOT = Path(__file__).resolve().parent.parent


def test_same_keys_in_both_languages():
    assert set(es.TEXTS) == set(en.TEXTS)


def test_static_keys_used_in_code_exist():
    used = set()
    for f in list(ROOT.glob("app.py")) + list((ROOT / "ui").rglob("*.py")) + list((ROOT / "modules").rglob("*.py")):
        used |= set(re.findall(r"\bT\(\s*\"([a-z0-9_.]+)\"", f.read_text(encoding="utf-8")))
        used |= set(re.findall(r"\bt\(\s*\"([a-z0-9_.]+)\"", f.read_text(encoding="utf-8")))
    missing = sorted(k for k in used if not k.endswith(".") and k not in es.TEXTS)
    assert not missing, missing
