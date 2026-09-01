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
        "id": "culinary-hill-basil-walnut-pesto",
        "title": "Basil Walnut Pesto",
        "cuisine": "Italian",
        "component_types": ["sauce"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Basil", "Garlic", "Olive oil", "Parmesan cheese", "Parsley", "Walnuts"],
        "tried": False,
        "golden": False,
        "source_url": "https://www.culinaryhill.com/basil-walnut-pesto/",
        "source_publisher": "Culinary Hill",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 150, "observed": "2026-08-31"},
        "private_attachment": False,
        "notes": "Added from the canonical Culinary Hill recipe page at Weston’s request.",
        "image_url": "https://www.culinaryhill.com/wp-content/uploads/2021/04/Basil-Walnut-Pesto-Culinary-Hill-1200x800-1.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, yield/timings, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "2 cups fresh basil leaves (packed)",
            "1 cup fresh parsley (packed)",
            "1/4 cup freshly grated Parmesan cheese (about 1 ounce)",
            "1/4 cup walnuts (about 1 ounce)",
            "3 cloves garlic",
            "1/2 cup olive oil",
            "Salt and freshly ground black pepper",
        ],
        "recipe_steps": [
            "In a food processor or blender, add basil, parsley, Parmesan cheese, walnuts, and garlic. Pulse until coarsely chopped, about 10 pulses.",
            "With the motor running, slowly drizzle in the olive oil and process until smooth. Season to taste with salt and pepper.",
        ],
        "recipe_yield": "8 servings (2 tablespoons each)",
        "recipe_timings": {"prepTime": "PT5M", "cookTime": "PT5M", "totalTime": "PT10M"},
    },
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
    {
        "id": "feel-good-foodie-creamy-cucumber-salad",
        "title": "Creamy Cucumber Salad",
        "cuisine": "American",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Cucumber", "Sour cream", "Dill"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/creamy-cucumber-salad/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 786, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2024/04/Creamy-Cucumber-Salad-TIMG.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "½ cup sour cream",
            "3 tablespoons red wine vinegar",
            "1 tablespoon chopped fresh dill",
            "1 teaspoon granulated sugar (optional)",
            "¼ teaspoon garlic powder",
            "Salt and pepper",
            "2 large English cucumbers (thinly sliced)",
            "¼ red onion (thinly sliced)",
        ],
        "recipe_steps": [
            "In a medium bowl, mix the sour cream, vinegar, dill, sugar, and garlic powder until well combined. Taste and season with salt and pepper.",
            "Add the sliced cucumbers and red onions on top of the sour cream dressing and stir to coat.",
            "Serve immediately at room temperature or refrigerate for 1 hour before serving.",
        ],
        "recipe_yield": "4 servings",
        "recipe_timings": {"prepTime": "PT5M", "totalTime": "PT5M"},
    },
    {
        "id": "feel-good-foodie-shirazi-salad",
        "title": "Shirazi Salad",
        "cuisine": "Persian",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Cucumber", "Tomatoes", "Red onion", "Cilantro", "Parsley"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/shirazi-salad/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 157, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2020/08/Shirazi-Salad-08-1.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "3 Persian cucumbers (finely chopped)",
            "3 Roma tomatoes (finely chopped)",
            "½ small red onion (finely chopped)",
            "½ small green bell pepper (optional)",
            "2 tablespoons chopped fresh cilantro",
            "2 tablespoons chopped fresh parsley",
            "2 tablespoons chopped fresh mint",
            "3 tablespoons extra-virgin olive oil",
            "3 tablespoons fresh lime juice",
            "½ teaspoon salt",
            "¼ teaspoon black pepper",
        ],
        "recipe_steps": [
            "In a large bowl, whisk together the olive oil, lime juice, salt, and pepper until well combined.",
            "Add the cucumbers, tomatoes, red onion, green pepper, cilantro, parsley, and mint on top of the dressing.",
            "Toss gently to combine the dressing with the vegetables and herbs. Serve immediately.",
        ],
        "recipe_yield": "4 servings",
        "recipe_timings": {"prepTime": "PT20M", "totalTime": "PT20M"},
    },
    {
        "id": "feel-good-foodie-tomato-cucumber-avocado-salad",
        "title": "Tomato Cucumber Avocado Salad",
        "cuisine": "Mediterranean",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Tomatoes", "Cucumber", "Avocado", "Dill", "Lemon"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/tomato-avocado-cucumber-salad/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 50, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2025/03/Tomato-Cucumber-Avocado-Salad-12.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "2 tablespoons extra virgin olive oil",
            "2 tablespoons fresh lemon juice",
            "1 teaspoon salt",
            "½ teaspoon black pepper",
            "1 pound Roma tomatoes (chopped)",
            "1 English cucumber (chopped)",
            "2 avocados (chopped)",
            "½ medium red onion (sliced)",
            "2 tablespoons fresh dill",
        ],
        "recipe_steps": [
            "In a large serving bowl, whisk together the olive oil, lemon juice, salt, and pepper until well combined and emulsified.",
            "Add the tomatoes, cucumber, avocado, red onion, and dill on top and toss gently to combine evenly. Serve immediately.",
        ],
        "recipe_yield": "4 servings",
        "recipe_timings": {"prepTime": "PT10M", "totalTime": "PT10M"},
    },
    {
        "id": "feel-good-foodie-classic-greek-salad",
        "title": "Classic Greek Salad",
        "cuisine": "Greek",
        "component_types": ["veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Tomatoes", "Cucumber", "Red onion", "Bell pepper"],
        "tried": False,
        "golden": False,
        "source_url": "https://feelgoodfoodie.net/recipe/greek-salad/",
        "source_publisher": "Feel Good Foodie",
        "source_entries": 0,
        "source_rating": {"rating": 5.0, "rating_count": 46, "observed": "2026-08-29"},
        "private_attachment": False,
        "notes": "Added from canonical page after verifying the displayed rating and recipe card.",
        "image_url": "https://feelgoodfoodie.net/wp-content/uploads/2020/05/Greek-Salad-TIMG.jpg",
        "content_status": "extracted",
        "content_note": "Ingredients, method, rating, and image extracted from the canonical recipe page JSON-LD.",
        "recipe_ingredients": [
            "3 ripe tomatoes (chopped)",
            "1 English cucumber (peeled and chopped)",
            "½ small red onion (chopped)",
            "½ green pepper (chopped)",
            "4 ounces Kalamata olives",
            "1 (8-ounce) block feta cheese (cut into cubes)",
            "4 tablespoons extra virgin olive oil",
            "2 tablespoons red wine vinegar",
            "½ teaspoon oregano",
            "¼ teaspoon salt",
            "¼ teaspoon black pepper",
        ],
        "recipe_steps": [
            "Place the tomatoes, cucumbers, red onions, green peppers, and olives in a large serving bowl. Stir to combine.",
            "Mix the salad dressing ingredients together in a small bowl and drizzle over the salad. Add the feta cheese on top.",
            "Lightly toss to combine, being careful not to over-mix or break up the feta cheese.",
        ],
        "recipe_yield": "4 servings",
        "recipe_timings": {"prepTime": "PT15M", "totalTime": "PT15M"},
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
