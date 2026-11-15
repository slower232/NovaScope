# Crop images

Put **one PNG per crop** in this folder. The file name is the crop id from `data/crops/crops.json`:

| File | Crop |
|---|---|
| `maiz.png` | Maíz / Maize |
| `frijol.png` | Frijol / Common bean |
| `trigo.png` | Trigo / Wheat |
| `sorgo.png` | Sorgo / Sorghum |
| `avena.png` | Avena / Oat |
| `alfalfa.png` | Alfalfa / Alfalfa |
| `algodon.png` | Algodón / Cotton |
| `chile.png` | Chile / Chili pepper |
| `cebolla.png` | Cebolla / Onion |
| `tomate.png` | Tomate / Tomato |
| `papa.png` | Papa / Potato |
| `manzana.png` | Manzana / Apple |
| `nogal.png` | Nogal pecanero / Pecan |

Examples: `assets/crops/maiz.png`, `assets/crops/frijol.png`.

## Tips
- Square image (for example 512 × 512 px), crop centred, light or transparent background (the app uses a cream theme).
- The app downsizes images to 256 px for display, so very large files are not needed.
- `.webp`, `.jpg` and `.jpeg` with the same name also work, but PNG is the format to use.
- Use only images you created or that you are allowed to use, and keep a note of the author and license of each one.

## If a PNG is missing
Nothing breaks: the interface shows an emoji tile for that crop instead (see `ui/crop_visuals.py`).
Check which images are still missing with:

```bash
python -m scripts.check_crop_images
```

New crops added to `crops.json` use the same rule: `assets/crops/<crop id>.png`.
