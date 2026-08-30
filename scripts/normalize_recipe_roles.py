#!/usr/bin/env python3
"""Apply explicit household menu-role corrections to imported recipe records."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"
ROLE_OVERRIDES = {
    # Eggs are a protein/side preparation, not a vegetable recipe.
    "Steamed egg": ["other"],
    # Bacon is an ingredient, but this is a composed kale salad/vegetable side.
    "Tuscan Kale Salad": ["veggie"],
}


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    changed = 0
    for recipe in data["recipes"]:
        role = ROLE_OVERRIDES.get(recipe["title"])
        if role and recipe.get("component_types") != role:
            recipe["component_types"] = role
            changed += 1
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
    print(f"normalized {changed} recipe roles")


if __name__ == "__main__":
    main()
