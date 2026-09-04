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
        "id": "julies-eats-treats-air-fryer-broccoli",
        "title": "Air Fryer Broccoli",
        "cuisine": "American",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Broccoli", "Olive oil", "Garlic powder", "Salt", "Black pepper"],
        "tried": False,
        "golden": True,
        "source_url": "https://www.julieseatsandtreats.com/air-fryer-broccoli/",
        "source_publisher": "Julie’s Eats & Treats",
        "source_entries": 0,
        "source_rating": None,
        "private_attachment": False,
        "golden_note": "Golden weeknight broccoli side when fresh broccoli is in inventory.",
        "notes": "Added after checking the canonical recipe page; chosen for five simple ingredients and an air-fryer-only method.",
        "content_status": "extracted",
        "content_note": "Ingredients, method, and timings transcribed from the canonical recipe page; the source has no displayed rating included here.",
        "recipe_ingredients": [
            "4 cups fresh broccoli (about 1 lb, trimmed into even-sized florets)",
            "1 tablespoon olive oil",
            "⅛ teaspoon kosher salt",
            "⅛ teaspoon ground black pepper",
            "⅛ teaspoon garlic powder",
        ],
        "recipe_steps": [
            "Preheat the air fryer to 390°F according to the manufacturer’s instructions.",
            "Toss the broccoli with olive oil first, then add the salt, pepper, and garlic powder and toss until evenly coated.",
            "Place the broccoli in the air-fryer basket and cook at 390°F for 7–9 minutes, until roasted to your preference.",
        ],
        "recipe_yield": "2–4 servings",
        "recipe_timings": {"prepTime": "PT5M", "cookTime": "PT7M", "totalTime": "PT12M"},
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
    migrated = 0
    legacy_id = "household-roasted-any-vegetable"
    replacement_id = "julies-eats-treats-air-fryer-broccoli"
    if legacy_id in by_id and replacement_id not in by_id:
        data["recipes"] = [recipe for recipe in data["recipes"] if recipe["id"] != legacy_id]
        by_id.pop(legacy_id)
        migrated = 1
    added = 0
    updated = 0
    for recipe in BASICS:
        if recipe["id"] not in by_id:
            data["recipes"].append(recipe)
            by_id[recipe["id"]] = recipe
            added += 1
        elif by_id[recipe["id"]].get("content_status") != recipe.get("content_status"):
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
    print(f"catalog now has {len(data['recipes'])} recipes; added {added}; migrated {migrated}; updated {updated} household basics")


if __name__ == "__main__":
    main()
