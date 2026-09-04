#!/usr/bin/env python3
"""Idempotently promote explicitly successful family-cooked recipes."""
from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "recipes.json"
REGISTRY_PATH = Path.home() / ".hermes" / "profiles" / "health" / "data" / "recipes" / "blessed-recipes.json"
OFFLINE_PATH = Path.home() / ".hermes" / "profiles" / "health" / "data" / "recipes" / "offline-recipes.json"
TODAY = dt.date.today().isoformat()

REGISTRY_ENTRIES = [
    {
        "id": "chicken-sausage-brami-pasta-green-garlic-scape-pesto-broccoli",
        "title": "Chicken Sausage Brami Fusilli with Kale, Broccoli + Green Garlic Scape Pesto",
        "status": "blessed",
        "cuisine": "Italian-inspired household recipe",
        "source": {
            "publisher": "Ruths household cooking record",
            "session": "@session:health/20260616_092438_6f6457e0",
        },
        "household_use": "Confirmed weeknight keeper; Kristina called the broccoli version a slam dunk and delicious.",
        "added": TODAY,
        "notes": "Use the offline cooked-version record as canonical. The successful version used half a package of breakfast chicken sausage (10 links), half a box of Brami fusilli, half a bag of pre-chopped kale, two heads of broccoli, and approximately half a cup of basil garlic-scapе pesto. Finish with lemon juice and Parmesan; adult chili flakes are optional.",
    },
    {
        "id": "household-oven-lemon-garlic-mahi-mahi-green-garlic-spinach",
        "title": "Oven Lemon-Garlic Mahi Mahi with Pearl Couscous and Spinach",
        "status": "blessed",
        "cuisine": "Mediterranean household recipe",
        "source": {
            "publisher": "Ruths household cooking record",
            "session": "@session:health/20260614_100422_a90a2988",
        },
        "household_use": "Confirmed quick family dinner; Kristina reported the mahi-mahi with green garlic and spinach was delicious.",
        "added": TODAY,
        "notes": "Use the offline cooked-version record as canonical. The successful method bakes the mahi at 425°F, keeps firmer green-garlic pieces with the fish, sautés tender tops with spinach, and serves the fish with pearl couscous. Use scallions only as a disclosed fallback when green garlic is unavailable.",
    },
]

CATALOG_ENTRIES = [
    {
        "id": "chicken-sausage-brami-pasta-green-garlic-scape-pesto-broccoli",
        "title": "Chicken Sausage Brami Fusilli with Kale, Broccoli + Green Garlic Scape Pesto",
        "cuisine": "Italian-inspired household recipe",
        "component_types": ["carb", "protein", "sauce", "veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Brami fusilli", "Breakfast chicken sausage", "Garlic scapes", "Basil", "Broccoli", "Kale", "Parmesan", "Lemon"],
        "tried": True,
        "golden": True,
        "source_url": None,
        "source_publisher": "Ruths household cooking record",
        "source_entries": 0,
        "private_attachment": False,
        "golden_note": "Confirmed keeper: Kristina called the broccoli version a slam dunk and delicious.",
        "notes": "Household-cooked recipe. Canonical successful version is recorded in the offline recipe database; this is a complete dinner card, not a generic pasta template.",
        "content_status": "household_reference",
        "content_note": "Reproduced from the successful cooked version and its recorded next-time finishing note.",
        "recipe_ingredients": [
            "1/2 box Brami fusilli pasta",
            "1/2 package breakfast chicken sausage (10 links), cut into half-coins",
            "1/2 bag pre-chopped kale",
            "2 heads broccoli, cut into small florets",
            "2 green garlic white bulbs, thinly sliced, if available",
            "6 garlic scapes, trimmed and chopped",
            "Basil as the pesto herb",
            "1/4 cup nuts",
            "1/4–1/3 cup grated Parmesan for the pesto, plus more to finish",
            "Zest of 1/2 lemon plus 1–2 teaspoons lemon juice for the pesto, plus more to finish",
            "1/4–1/3 cup olive oil for the pesto, plus 1–2 tablespoons for cooking",
            "1/2 cup reserved pasta water",
            "Salt, black pepper, and optional adult chili flakes",
        ],
        "recipe_steps": [
            "Make pesto: blend the chopped garlic scapes, basil, nuts, Parmesan, lemon zest, lemon juice, olive oil, and a pinch of salt. If the scapes taste sharply raw, blanch them for 30–60 seconds first.",
            "Boil salted water. Cook the Brami fusilli until just tender; reserve 1/2 cup pasta water, then drain.",
            "While the pasta cooks, heat olive oil in a large skillet. Brown the 10 chicken-sausage half-coins for 3–5 minutes.",
            "Add the sliced green garlic with a pinch of salt. Cook gently for 2–3 minutes until soft and fragrant; do not hard-brown it.",
            "Add the broccoli and a splash of water. Cover for 2–4 minutes until bright green and just tender.",
            "Add the kale and another splash of water if needed. Cover for 1–2 minutes, then stir until wilted and tender.",
            "Add the drained pasta. Turn the heat low or off. Toss with approximately 1/2 cup pesto and splashes of pasta water until glossy.",
            "Finish with lemon juice and Parmesan to balance the garlic. Add black pepper, olive oil, and adult chili flakes at the table if desired.",
        ],
        "recipe_yield": "2 adults + Aria; possible adult lunch depending on amount",
        "recipe_timings": {"prepTime": "PT15M", "cookTime": "PT20M", "totalTime": "PT35M"},
    },
    {
        "id": "household-oven-lemon-garlic-mahi-mahi-green-garlic-spinach",
        "title": "Oven Lemon-Garlic Mahi Mahi with Pearl Couscous and Spinach",
        "cuisine": "Mediterranean household recipe",
        "component_types": ["carb", "protein", "veggie"],
        "meal_slots": ["dinner"],
        "key_ingredients": ["Mahi mahi", "Pearl couscous", "Spinach", "Green garlic", "Lemon", "Olive oil"],
        "tried": True,
        "golden": True,
        "source_url": None,
        "source_publisher": "Ruths household cooking record",
        "source_entries": 0,
        "private_attachment": False,
        "golden_note": "Confirmed keeper: Kristina reported the mahi-mahi with green garlic and spinach was delicious.",
        "notes": "Household-cooked recipe. The successful version used oven-baked mahi, pearl couscous, sautéed spinach, and green garlic; scallions are only a disclosed fallback.",
        "content_status": "household_reference",
        "content_note": "Reproduced from the successful sub-40-minute family cooking card.",
        "recipe_ingredients": [
            "1–1 1/2 lb mahi mahi",
            "1 1/2 cups pearl couscous",
            "6–8 cups spinach",
            "1–2 stalks green garlic, thinly sliced; reserve tender green tops for the spinach",
            "1–2 garlic cloves, minced or grated, optional if the green garlic is strong",
            "1 lemon",
            "1 tablespoon olive oil for the fish, plus more for couscous and spinach",
            "2 1/4 cups water or chicken stock",
            "Salt and black pepper",
            "Optional: paprika and oregano or thyme",
        ],
        "recipe_steps": [
            "Heat the oven to 425°F and line a sheet pan. Start the pearl couscous with 2 1/4 cups water or stock and a pinch of salt; simmer covered for 10–12 minutes, then rest covered.",
            "Pat the mahi dry. Mix lemon zest, the juice of 1/2 lemon, 1 tablespoon olive oil, the garlic or green garlic, pepper, and a small pinch of salt; rub over the fish.",
            "Put the fish on the sheet pan. Scatter the firmer green-garlic pieces around it with a small drizzle of oil. Bake for 8–12 minutes, depending on thickness, until it flakes and reaches 145°F if temperature-checked.",
            "While the fish bakes, sauté the spinach with olive oil and the tender green-garlic tops. Add a splash of water and cook for 2–4 minutes until wilted. Finish with the remaining lemon juice.",
            "Fluff the couscous. Serve couscous, spinach, and mahi together, spooning the lemony pan juices and roasted green garlic over the fish.",
        ],
        "recipe_yield": "2 adults + Aria",
        "recipe_timings": {"prepTime": "PT10M", "cookTime": "PT12M", "totalTime": "PT35M"},
    },
]

OFFLINE_ENTRIES = [
    {
        "id": "household-oven-lemon-garlic-mahi-mahi-green-garlic-spinach",
        "title": "Oven Lemon-Garlic Mahi Mahi with Pearl Couscous and Spinach",
        "status": "keeper",
        "registry_status": "blessed",
        "added": TODAY,
        "source": "Household-cooked recipe from the June 14 dinner session; Kristina reported the mahi-mahi with green garlic and spinach was delicious.",
        "serves": "2 adults + Aria",
        "time": "About 10 minutes prep; 8–12 minutes oven; under 40 minutes elapsed with couscous and spinach.",
        "tags": ["weeknight", "mahi-mahi", "pearl-couscous", "spinach", "green-garlic", "toddler-adaptable", "keeper"],
        "ingredients": {
            "main": [
                "1–1 1/2 lb mahi mahi",
                "1 1/2 cups pearl couscous",
                "6–8 cups spinach",
                "1–2 stalks green garlic, firmer and tender parts separated",
                "1–2 garlic cloves, optional",
                "1 lemon",
                "Olive oil, salt, and black pepper",
                "2 1/4 cups water or chicken stock",
                "Optional paprika and oregano or thyme",
            ]
        },
        "steps": [
            "Heat the oven to 425°F and line a sheet pan. Simmer pearl couscous with 2 1/4 cups water or stock and a pinch of salt for 10–12 minutes, then rest covered.",
            "Pat the mahi dry. Rub with lemon zest, the juice of 1/2 lemon, olive oil, garlic or green garlic, pepper, and a small pinch of salt.",
            "Scatter the firmer green-garlic pieces around the fish and bake for 8–12 minutes, until flaky and 145°F if temperature-checked.",
            "Sauté spinach with olive oil and the tender green-garlic tops for 2–4 minutes until wilted. Finish with the remaining lemon juice.",
            "Fluff couscous and serve with spinach and mahi, spooning the lemony pan juices over the fish.",
        ],
        "cooked_versions": [
            {
                "date": "2026-06-14",
                "cook": "Ruths household",
                "result": "Delicious, per Kristina.",
                "adjustments": ["Used oven-baked mahi-mahi with green garlic and sautéed spinach; served with pearl couscous."],
                "unknowns": [],
                "aria_response": "Not recorded.",
            }
        ],
        "aria_notes": "Flake fish carefully and check for bones. Keep her portion lower-salt and finely chop the cooked spinach/green garlic.",
        "household_notes": "Blessed because the household cooked it and Kristina explicitly reported it was delicious. Scallions are only a disclosed fallback for unavailable green garlic.",
    }
]


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    try:
        json.loads(temp_path.read_text(encoding="utf-8"))
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def upsert_by_id(items: list[dict], additions: list[dict], *, replace: bool = False) -> tuple[int, int]:
    by_id = {item["id"]: item for item in items}
    added = updated = 0
    for item in additions:
        if item["id"] not in by_id:
            items.append(item)
            by_id[item["id"]] = item
            added += 1
        elif replace:
            by_id[item["id"]].update(item)
            updated += 1
    return added, updated


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["recipes"] = [
        recipe for recipe in catalog["recipes"]
        if recipe["id"] != "household-chicken-sausage-brami-garlic-scape-pesto"
    ]
    catalog_added, catalog_updated = upsert_by_id(catalog["recipes"], CATALOG_ENTRIES, replace=True)
    catalog["recipe_count"] = len(catalog["recipes"])
    catalog["updated"] = TODAY
    atomic_write(CATALOG_PATH, catalog)

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry["recipes"] = [
        recipe for recipe in registry["recipes"]
        if recipe["id"] != "household-chicken-sausage-brami-garlic-scape-pesto"
    ]
    registry_added, registry_updated = upsert_by_id(registry["recipes"], REGISTRY_ENTRIES, replace=True)
    registry["updated"] = TODAY
    atomic_write(REGISTRY_PATH, registry)

    offline = json.loads(OFFLINE_PATH.read_text(encoding="utf-8"))
    offline_added, offline_record_updated = upsert_by_id(offline["recipes"], OFFLINE_ENTRIES, replace=True)
    blessed_ids = {entry["id"] for entry in REGISTRY_ENTRIES}
    offline_updated = offline_record_updated
    for recipe in offline["recipes"]:
        if recipe["id"] in blessed_ids and recipe.get("registry_status") != "blessed":
            recipe["registry_status"] = "blessed"
            offline_updated += 1
    offline["updated"] = TODAY
    atomic_write(OFFLINE_PATH, offline)

    print(
        f"promoted family keepers: catalog +{catalog_added}/~{catalog_updated}; "
        f"registry +{registry_added}/~{registry_updated}; offline +{offline_added}/~{offline_updated}; "
        f"catalog total {len(catalog['recipes'])}"
    )


if __name__ == "__main__":
    main()
