"""Crop visuals: emoji (always available) + optional PNG per crop in assets/crops/<crop_id>.png.

If the PNG is missing, unreadable or the crop id is unsafe, a styled emoji tile is used instead,
so the interface never shows a broken image or an error.
This module does not import Streamlit, so it can be tested on its own.
"""
import base64
import html
import io
import re
from functools import lru_cache
from pathlib import Path

CROPS_DIR = Path(__file__).resolve().parent.parent / "assets" / "crops"
IMAGE_EXTENSIONS = (".png", ".webp", ".jpg", ".jpeg")  # PNG is the documented format; others are accepted as a convenience
MAX_PX = 256  # embedded thumbnails are downscaled so repeated cards stay light
_SAFE_ID = re.compile(r"^[a-z0-9_-]+$")

"""Crop emoji used consistently in selectors, labels, and field maps."""
CROP_EMOJI = {
    "maiz": "🌽", "frijol": "🫘", "trigo": "🌾", "sorgo": "🌾", "avena": "🌾",
    "alfalfa": "☘️", "algodon": "☁️", "chile": "🌶️", "cebolla": "🧅",
    "tomate": "🍅", "papa": "🥔", "manzana": "🍎", "nogal": "🌰",
}


def crop_icon(crop_id: str) -> str:
    return CROP_EMOJI.get(crop_id, "🌱")


def crop_label(crop_id: str, name: str) -> str:
    return f"{crop_icon(crop_id)} {name}"


def crop_image_path(crop_id: str):
    """Path of the crop's image (assets/crops/<crop_id>.png) or None if it does not exist."""
    if not isinstance(crop_id, str) or not _SAFE_ID.match(crop_id):
        return None
    for ext in IMAGE_EXTENSIONS:
        p = CROPS_DIR / f"{crop_id}{ext}"
        if p.is_file():
            return p
    return None


@lru_cache(maxsize=128)
def _data_uri(path_str: str, mtime_ns: int):
    """Base64 data URI of the image, downscaled when Pillow is available. None if the file cannot be read."""
    try:
        raw = Path(path_str).read_bytes()
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw))
            img.load()
            img.thumbnail((MAX_PX, MAX_PX))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        except ImportError:
            mime = "image/png" if path_str.lower().endswith(".png") else "image/jpeg" if path_str.lower().endswith((".jpg", ".jpeg")) else "image/webp"
            return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    except Exception:
        return None  # corrupt or unreadable file: the caller falls back to the emoji tile


def crop_image_uri(crop_id: str):
    p = crop_image_path(crop_id)
    if p is None:
        return None
    return _data_uri(str(p), p.stat().st_mtime_ns)


def has_crop_image(crop_id: str) -> bool:
    return crop_image_uri(crop_id) is not None


def crop_thumb(crop_id: str, size: int = 56, alt: str = "") -> str:
    """HTML for a square crop picture of `size` px, or an emoji tile when the PNG is missing."""
    size = max(16, int(size))
    uri = crop_image_uri(crop_id)
    if uri:
        return (f'<img class="fs-crop-img" src="{uri}" alt="{html.escape(alt or crop_id)}" '
                f'style="width:{size}px;height:{size}px">')
    return (f'<span class="fs-crop-fallback" role="img" aria-label="{html.escape(alt or crop_id)}" '
            f'style="width:{size}px;height:{size}px;font-size:{int(size * 0.55)}px">{crop_icon(crop_id)}</span>')


def crop_pill(crop_id: str, name: str, size: int = 26) -> str:
    """Small inline chip (picture + name) for captions and legends."""
    return (f'<span class="fs-crop-pill">{crop_thumb(crop_id, size, name)}'
            f'<span>{html.escape(name)}</span></span>')


def crop_header(crop_id: str, title: str, subtitle: str = "", size: int = 64) -> str:
    """Picture on the left, title and optional subtitle on the right."""
    sub = f'<div class="fs-small">{html.escape(subtitle)}</div>' if subtitle else ""
    return (f'<div class="fs-crop-row">{crop_thumb(crop_id, size, title)}'
            f'<div><div class="fs-crop-title">{html.escape(title)}</div>{sub}</div></div>')
