import json
from config.settings import settings


def load_crops(path: str | None = None) -> list[dict]:
    with open(path or settings.crops_path, encoding="utf-8") as fh:
        return json.load(fh)["crops"]


def get_crop(crop_id: str, crops: list[dict] | None = None) -> dict:
    for c in crops or load_crops():
        if c["id"] == crop_id:
            return c
    raise KeyError(crop_id)


def load_weights(path: str | None = None) -> dict:
    with open(path or settings.weights_path, encoding="utf-8") as fh:
        w = json.load(fh)["weights"]
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}
