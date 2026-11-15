from ui.translations import en, es

_T = {"es": es.TEXTS, "en": en.TEXTS}
LANGS = {"es": "Español", "en": "English"}


def t(key: str, lang: str = "es", **kw) -> str:
    s = _T.get(lang, _T["es"]).get(key) or _T["es"].get(key) or key
    try:
        return s.format(**kw) if kw else s
    except (KeyError, IndexError):
        return s
