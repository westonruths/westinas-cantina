#!/usr/bin/env python3
"""Idempotently fill verified public recipe thumbnails where available."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"
PHOTO_OVERRIDES = {
    "Rotisserie chicken stock": "https://tastesbetterfromscratch.com/wp-content/uploads/2019/04/Chicken-Stock-Web-6.jpg",
    "Homemade Tzatziki": "https://hips.hearstapps.com/hmg-prod/images/tzatziki-index-6464f8fadaaff.jpg?crop=1.00xw:1.00xh;0,0&resize=1200:*",
}


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    changed = 0
    for recipe in data["recipes"]:
        image = PHOTO_OVERRIDES.get(recipe["title"])
        if image and recipe.get("image_url") != image:
            recipe["image_url"] = image
            changed += 1
    data["visuals"]["recipes_with_thumbnails"] = sum(bool(r.get("image_url")) for r in data["recipes"])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DATA_PATH.parent, delete=False) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    try:
        json.loads(temp_path.read_text(encoding="utf-8"))
        os.replace(temp_path, DATA_PATH)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    print(f"updated {changed} recipe thumbnails; {data['visuals']['recipes_with_thumbnails']} recipes now have photos")


if __name__ == "__main__":
    main()
