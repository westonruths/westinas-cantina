#!/usr/bin/env python3
"""Regression checks for the dinner pairing and active-time contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
PLANNER = json.loads((ROOT / "data" / "dinner-planner.json").read_text(encoding="utf-8"))

assert PLANNER["limits"] == {"weekday": 29, "weekend": 59}
recipes_by_id = {recipe["id"]: recipe for recipe in RECIPES["recipes"]}
meta = PLANNER["recipe_meta"]
assert meta
assert set(meta) <= set(recipes_by_id)
assert all(item["family"] and isinstance(item["active_minutes"], int) for item in meta.values())
assert all(0 <= item["active_minutes"] < 60 for item in meta.values())

pairings = PLANNER["pairings"]
assert len(pairings) >= 7
assert all(set(pairing["components"]) == {"protein", "carb", "veggie"} for pairing in pairings)
assert all(pairing["active_minutes"] < (29 if pairing["day_type"] == "weekday" else 59) for pairing in pairings)

# The regression case must not be accepted as a dinner pairing.
assert not PLANNER["compatibility"]["chinese"]["american"]
print(f"planner contract valid: {len(meta)} recipe metadata rows; {len(pairings)} pairings")
