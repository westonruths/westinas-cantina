#!/usr/bin/env python3
"""Idempotently add concise, household-defined Cantina basics."""
from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"

BASICS = [
    {
        "id": "household-rice-cooker-rice",
        "title": "Rice Cooker Rice",
        "cuisine": "Household basic",
        "component_types": ["carb"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Rice", "Water"],
        "tried": False,
        "golden": True,
        "source_url": None,
        "source_publisher": "Household reference",
        "source_entries": 0,
        "private_attachment": False,
        "golden_note": "Weeknight default: use any stocked rice in the rice cooker.",
        "notes": "Flexible household reference, not a sourced recipe. Follow the rice cooker’s water ratio for the selected rice.",
        "content_status": "household_reference",
        "content_note": "Short household method; rice variety and cooker ratio are intentionally flexible.",
        "recipe_ingredients": [
            "1 cup rice of choice (sushi, brown, purple, or another stocked rice)",
            "Water according to the rice cooker’s ratio for that rice",
            "Salt, optional",
        ],
        "recipe_steps": [
            "Rinse the rice if appropriate for the variety, then add it to the rice cooker with the recommended amount of water.",
            "Close the lid and run the matching rice setting. Rest for 5 minutes when finished, then fluff and serve.",
        ],
        "recipe_yield": "About 3 cups cooked rice",
        "recipe_timings": {"prepTime": "PT2M", "totalTime": "PT5M"},
    },
    {
        "id": "household-roasted-any-vegetable",
        "title": "Roasted Any Vegetable",
        "cuisine": "Household basic",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Vegetable", "Olive oil", "Salt", "Black pepper"],
        "tried": False,
        "golden": True,
        "source_url": None,
        "source_publisher": "Household reference",
        "source_entries": 0,
        "private_attachment": False,
        "golden_note": "Weeknight default: roast whichever sturdy vegetable needs using, in the oven or air fryer.",
        "notes": "Flexible household reference, not a sourced recipe. Current inventory examples include broccoli, beets, and potatoes; cut size determines timing.",
        "content_status": "household_reference",
        "content_note": "Short household method with oven and air-fryer timing ranges; vegetable choice is intentionally flexible.",
        "recipe_ingredients": [
            "1–2 lb vegetable of choice, cut into similarly sized pieces",
            "1–2 tablespoons olive or avocado oil",
            "Salt and black pepper",
        ],
        "recipe_steps": [
            "Toss the vegetable with oil, salt, and pepper. Spread it in one layer on a rimmed sheet pan or in the air-fryer basket.",
            "Oven: roast at 425°F until browned and tender, usually 20–35 minutes. Air fryer: cook at 400°F until browned and tender, usually 10–18 minutes; shake once if useful.",
        ],
        "recipe_yield": "2–4 servings",
        "recipe_timings": {"prepTime": "PT5M", "totalTime": "PT25M"},
    },
    {
        "id": "household-chicken-thighs-oven-air-fryer",
        "title": "Chicken Thighs (Oven or Air Fryer)",
        "cuisine": "Household basic",
        "component_types": ["protein"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Chicken thighs", "Olive oil", "Salt", "Black pepper"],
        "tried": False,
        "golden": True,
        "source_url": None,
        "source_publisher": "Household reference",
        "source_entries": 0,
        "private_attachment": False,
        "golden_note": "Weeknight default: a low-effort use for the stocked boneless skinless chicken thighs.",
        "notes": "Flexible household reference, not a sourced recipe. Use the oven or air fryer; vary seasoning without adding extra steps.",
        "content_status": "household_reference",
        "content_note": "Short household method with two appliance options and a food-safety temperature cue.",
        "recipe_ingredients": [
            "1½–2 lb boneless skinless chicken thighs",
            "1 tablespoon olive or avocado oil",
            "Salt, black pepper, and optional garlic powder or another stocked seasoning",
        ],
        "recipe_steps": [
            "Pat the chicken dry, toss with oil and seasoning, and arrange in a single layer.",
            "Air fryer: cook at 400°F for about 15–20 minutes, turning once. Oven: roast at 425°F for about 20–25 minutes. Cook until the thickest piece reaches 165°F, then rest for 5 minutes.",
        ],
        "recipe_yield": "4 servings",
        "recipe_timings": {"prepTime": "PT5M", "totalTime": "PT25M"},
    },
    {
        "id": "household-caprese-salad",
        "title": "Caprese Salad",
        "cuisine": "Italian",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Fresh tomatoes", "Mozzarella", "Basil", "Balsamic vinegar"],
        "tried": False,
        "golden": True,
        "source_url": None,
        "source_publisher": "Household reference",
        "source_entries": 0,
        "private_attachment": False,
        "golden_note": "Weeknight assembly default when fresh tomatoes, mozzarella, and basil are available.",
        "notes": "Flexible household reference, not a sourced recipe. Assemble immediately; no cooking required.",
        "content_status": "household_reference",
        "content_note": "Short household assembly card; tomato, mozzarella, and basil are the core ingredients.",
        "recipe_ingredients": [
            "2–3 ripe fresh tomatoes, sliced",
            "8 ounces fresh mozzarella, sliced or torn",
            "Fresh basil leaves",
            "Olive oil, balsamic vinegar, salt, and black pepper, to taste",
        ],
        "recipe_steps": [
            "Layer the tomatoes, mozzarella, and basil on a plate. Drizzle with olive oil and balsamic vinegar, season with salt and pepper, and serve.",
        ],
        "recipe_yield": "2–4 servings",
        "recipe_timings": {"prepTime": "PT5M", "totalTime": "PT5M"},
    },
]


def atomic_write(data: dict) -> None:
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


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    by_id = {recipe["id"]: recipe for recipe in data["recipes"]}
    added = 0
    updated = 0
    for recipe in BASICS:
        if recipe["id"] not in by_id:
            data["recipes"].append(recipe)
            by_id[recipe["id"]] = recipe
            added += 1
        elif by_id[recipe["id"]].get("content_status") != "household_reference":
            by_id[recipe["id"]].update(recipe)
            updated += 1
    data["recipe_count"] = len(data["recipes"])
    data["updated"] = dt.date.today().isoformat()
    data["visuals"]["recipes_with_thumbnails"] = sum(bool(r.get("image_url")) for r in data["recipes"])
    data["content_import"]["linked_targets"] = sum(bool(r.get("source_url")) for r in data["recipes"])
    data["content_import"]["extracted"] = sum(r.get("content_status") in ("extracted", "extracted_fallback") for r in data["recipes"])
    data["content_import"]["unavailable"] = sum(r.get("content_status") == "unavailable" for r in data["recipes"])
    data["content_import"]["updated"] = data["updated"]
    atomic_write(data)
    print(f"catalog now has {len(data['recipes'])} recipes; added {added}; updated {updated} household basics")


if __name__ == "__main__":
    main()
