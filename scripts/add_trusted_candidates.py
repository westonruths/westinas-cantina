#!/usr/bin/env python3
"""Idempotently add source-verified component recipes to the Cantina catalog."""
from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"

CANDIDATES = [
    {
        "id": "feel-good-foodie-how-to-cook-broccoli",
        "title": "How to Cook Broccoli",
        "cuisine": "American",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Broccoli"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/how-to-cook-broccoli/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 768, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2021/04/how-to-cook-broccoli-4.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, methods, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "1 head broccoli (cut into florets)",
            "8 cups water",
            "2 tablespoons salt",
            "3 tablespoons olive oil",
            "¼ teaspoon salt",
            "¼ teaspoon black pepper",
        ],
        "recipe_steps": [
            "Bring a pot of water and salt to a boil.",
            "Carefully place the broccoli in the boiling water and simmer for 2–3 minutes or until tender.",
            "Once tender, carefully remove or strain the broccoli.",
            "Preheat oven to 425°F and line a baking sheet with parchment paper, if desired.",
            "Toss broccoli in the olive oil, salt, and black pepper.",
            "Place the broccoli on a roasting pan and roast until tender and slightly colored, about 7–10 minutes.",
            "Serve immediately.",
        ],
        "recipe_yield": "2 servings",
        "recipe_timings": {"prepTime": "PT5M", "cookTime": "PT10M", "totalTime": "PT15M"},
    },
    {
        "id": "feel-good-foodie-lebanese-rice",
        "title": "Lebanese Rice",
        "cuisine": "Lebanese",
        "component_types": ["carb"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Rice", "Vermicelli", "Olive oil"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/lebanese-rice/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 964, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2018/12/Lebanese-Rice-8-1.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "2 cups long grain white rice",
            "½ cup dried rice vermicelli noodles",
            "2 tablespoons extra virgin olive oil",
            "½ teaspoon salt",
            "dash cinnamon (optional)",
            "parsley (optional, for garnish)",
        ],
        "recipe_steps": [
            "Rinse the rice with cold water until the water runs clear. Drain well and set aside.",
            "In a medium non-stick pot, heat the olive oil on medium heat. Add the vermicelli and cook, stirring frequently, until deep golden brown.",
            "Transfer the rice over the cooked vermicelli and stir to combine. Season with salt and cinnamon, if desired.",
            "Add 4 cups water and bring the mixture to a boil. Reduce the heat to low, cover, and cook for 15 minutes.",
            "Remove from the heat and allow the rice to steam for 5 minutes. Uncover and fluff with a fork.",
            "Serve warm with fresh parsley and toasted nuts, if desired.",
        ],
        "recipe_yield": "8 servings",
        "recipe_timings": {"cookTime": "PT15M", "totalTime": "PT15M"},
    },
    {
        "id": "feel-good-foodie-grilled-lemon-chicken",
        "title": "Grilled Lemon Chicken",
        "cuisine": "Mediterranean",
        "component_types": ["protein"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Chicken", "Garlic", "Lemon", "Parsley"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/grilled-lemon-chicken/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 1064, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2019/07/Grilled-Lemon-Chicken-08.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "4 (6-ounce) boneless skinless chicken breasts",
            "¼ cup olive oil",
            "1 large lemon (zest and juice)",
            "4 garlic cloves (minced)",
            "1 tablespoon oregano",
            "¾ teaspoon salt",
            "½ teaspoon black pepper",
            "Chopped parsley (for serving)",
            "Lemon wedges (for serving)",
        ],
        "recipe_steps": [
            "Pat chicken dry and pound any thick parts so the pieces are even. Combine olive oil, lemon juice and zest, garlic, oregano, salt, and pepper in a bowl. Add chicken and toss well. Cover and marinate for 30 minutes to 2 hours.",
            "Preheat the grill or grill pan to medium-high heat. Grill the chicken for 5–7 minutes per side, or until cooked through.",
            "Remove chicken from the grill. Sprinkle with parsley and serve with lemon wedges, if desired.",
        ],
        "recipe_yield": "4 servings",
        "recipe_timings": {"prepTime": "PT10M", "cookTime": "PT15M", "totalTime": "PT55M"},
    },
]


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = {recipe["id"] for recipe in data["recipes"]}
    added = 0
    for recipe in CANDIDATES:
        if recipe["id"] not in existing:
            data["recipes"].append(recipe)
            existing.add(recipe["id"])
            added += 1
    data["recipe_count"] = len(data["recipes"])
    data["updated"] = dt.date.today().isoformat()
    data["visuals"]["recipes_with_thumbnails"] = sum(bool(r.get("image_url")) for r in data["recipes"])
    data["content_import"]["linked_targets"] = sum(bool(r.get("source_url")) for r in data["recipes"])
    data["content_import"]["extracted"] = sum(r.get("content_status") in ("extracted", "extracted_fallback") for r in data["recipes"])
    data["content_import"]["unavailable"] = sum(r.get("content_status") == "unavailable" for r in data["recipes"])
    data["content_import"]["updated"] = data["updated"]
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
    print(f"catalog now has {len(data['recipes'])} recipes; added {added} researched candidates")


if __name__ == "__main__":
    main()
