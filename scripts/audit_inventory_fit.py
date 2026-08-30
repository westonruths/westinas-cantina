#!/usr/bin/env python3
"""Audit generated inventory-fit metadata without mutating the public catalog."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"
INVENTORY_PATH = Path(__import__("os").environ.get(
    "WESTINAS_INVENTORY_PATH",
    "/mnt/storage/hermes-profiles/profiles/health/data/kitchen/inventory.json",
))

spec = importlib.util.spec_from_file_location("update_inventory_fit", ROOT / "scripts" / "update_inventory_fit.py")
if spec is None or spec.loader is None:
    raise SystemExit("Could not load update_inventory_fit.py")
fit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit)


def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory_items = fit.normalized_inventory_items(inventory)
    use_first_items = fit.normalized_inventory_items(inventory.get("inventory", {}).get("use_first", []))
    mismatches = []
    positive = 0
    status_rows = 0
    for recipe in data["recipes"]:
        lines = fit.public_ingredient_lines(recipe)
        expected_status = fit.status_for_lines(lines, inventory_items)
        requirements, basis = fit.requirements_for(recipe)
        primary = fit.infer_primary_ingredients(recipe)
        primary_flags = [fit.inventory_match(item, inventory_items) for item in primary]
        expected_fit = {
            "percent": None,
            "matched": 0,
            "total": 0,
            "use_first_matches": 0,
            "primary_ingredients": primary,
            "primary_matched": sum(primary_flags),
            "primary_total": len(primary),
            "primary_present": None if not primary else all(primary_flags),
            "as_of": recipe.get("inventory_fit", {}).get("as_of"),
            "basis": "not enough public ingredient data",
        }
        if requirements:
            matched = sum(fit.inventory_match(item, inventory_items) for item in requirements)
            use_first_matches = sum(fit.inventory_match(item, use_first_items) for item in requirements)
            expected_fit.update({
                "percent": round(100 * matched / len(requirements)),
                "matched": matched,
                "total": len(requirements),
                "use_first_matches": use_first_matches,
                "basis": basis,
            })
        actual_status = recipe.get("ingredient_inventory", [])
        actual_fit = recipe.get("inventory_fit", {})
        status_rows += len(expected_status)
        positive += sum(item["present"] for item in expected_status)
        if actual_status != expected_status:
            mismatches.append(f"ingredient statuses: {recipe['title']}")
        for key, value in expected_fit.items():
            if key == "as_of":
                continue
            if actual_fit.get(key) != value:
                mismatches.append(f"fit {key}: {recipe['title']} (expected {value!r}, got {actual_fit.get(key)!r})")
    print(f"audited {len(data['recipes'])} recipes; {status_rows} ingredient lines; {positive} positive matches")
    if mismatches:
        print("metadata drift detected:")
        for mismatch in mismatches:
            print(f"- {mismatch}")
        return 1
    tripe_flags = [
        (recipe["title"], item["present"])
        for recipe in data["recipes"]
        for item in recipe.get("ingredient_inventory", [])
        if "tripe" in item["name"].lower()
    ]
    print(f"tripe checks: {tripe_flags or 'none'}")
    print("audit passed: stored metadata matches the deterministic matcher")
    return 0


if __name__ == "__main__":
    sys.exit(main())
