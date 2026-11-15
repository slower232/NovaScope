"""Lists which crops already have an image in assets/crops/ and which still use the emoji fallback.

Usage:  python -m scripts.check_crop_images
"""
from modules.crop_rotation.crop_catalog import load_crops
from ui.crop_visuals import CROPS_DIR, crop_image_path, has_crop_image


def main():
    missing = []
    print(f"Image folder: {CROPS_DIR}")
    for crop in load_crops():
        cid = crop["id"]
        path = crop_image_path(cid)
        if path is None:
            status = f"MISSING  -> add assets/crops/{cid}.png"
            missing.append(cid)
        elif not has_crop_image(cid):
            status = f"UNREADABLE ({path.name}) -> replace the file; the emoji fallback is shown"
            missing.append(cid)
        else:
            status = f"ok       {path.name}"
        print(f"  {cid:<10} {status}")
    print(f"\n{len(load_crops()) - len(missing)} of {len(load_crops())} crops have a usable image.")


if __name__ == "__main__":
    main()
