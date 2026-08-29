#!/usr/bin/env python3
"""Attach deterministic inventory-fit metadata to public recipe data.

The private inventory is read locally and is never copied into the public site.
Only aggregate percentages and per-public-ingredient presence flags are emitted.
Quantities, freshness, and substitutions that would change a recipe's identity
are not validated.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"
INVENTORY_PATH = Path(os.environ.get(
    "WESTINAS_INVENTORY_PATH",
    "/mnt/storage/hermes-profiles/profiles/health/data/kitchen/inventory.json",
))

# Practical equivalents that are reasonable for an inventory-presence estimate.
# Exact identity-sensitive ingredients (for example shishito peppers and yeast)
# intentionally remain strict.
ALIASES = {
    "water": ["water"],
    "salt": ["standard american kitchen spices"],
    "salt and pepper": ["standard american kitchen spices"],
    "black pepper": ["standard american kitchen spices"],
    "white pepper": ["standard american kitchen spices"],
    "sugar": ["standard american kitchen spices", "honey", "maple syrup"],
    "oil": ["olive oil", "avocado oil", "grapeseed oil", "coconut oil"],
    "olive oil": ["olive oil"],
    "lemon": ["lemons"],
    "garlic": ["garlic"],
    "ginger": ["ginger"],
    "scallions": ["green onions"],
    "green onion": ["green onions"],
    "onion": ["yellow onion", "large yellow onion"],
    "leaf lettuce": ["romaine lettuce", "leaf lettuce", "lettuce"],
    "lacinato kale": ["lacinato kale", "kale"],
    "potatoes": ["golden potatoes", "hash brown potatoes"],
    "flour": ["flour"],
    "bread": ["keto bread", "bread"],
    "pecorino cheese": ["pecorino", "parmesan"],
    "parmesan cheese": ["parmesan"],
    "eggs": ["eggs"],
    "egg": ["eggs"],
    "chicken bouillon": ["chicken bouillon"],
    "chicken stock": ["chicken stock"],
    "chicken broth": ["chicken stock"],
    "soy sauce": ["regular soy sauce", "dark soy sauce"],
    "light soy sauce": ["regular soy sauce", "dark soy sauce"],
    "dark soy sauce": ["dark soy sauce"],
    "shaoxing wine": ["shaoxing wine"],
    "rice wine": ["shaoxing wine"],
    "doubanjiang": ["doubanjiang"],
    "sichuan chilli bean paste": ["doubanjiang"],
    "fermented black beans": ["douchi"],
    "leek": ["leek", "green onions"],
    "leek or green garlic": ["leek", "green garlic", "green onions"],
    "fresh red chiles": ["dried red chili peppers", "facing heaven peppers", "peppers"],
    "red pepper flakes": ["chili flakes", "red pepper powder"],
    "korean hot pepper flakes": ["red pepper powder", "chili flakes", "gochujang"],
    "sesame oil": ["sesame oil"],
    "sesame seeds": ["sesame seeds"],
    "fish sauce": ["fish sauce"],
    "white vinegar": ["white vinegar"],
    "balsamic vinegar": ["balsamic vinegar"],
    "cornstarch": ["cornstarch"],
    "orzo": ["orzo"],
    "rice": ["rice", "sushi rice", "brown rice", "purple rice"],
    "couscous": ["pearl couscous"],
    "noodles": ["noodles", "wheat noodles", "pan fried noodles"],
    "pasta": ["brami protein pasta"],
    "vermicelli": ["rice vermicelli"],
    "rice paper": ["rice paper"],
    "shrimp": ["shrimp"],
    "pork belly": ["pork belly"],
    "ground pork": ["ground pork"],
    "pork": ["pork belly", "ground pork"],
    "chicken thigh": ["chicken thighs"],
    "chicken": ["chicken", "chicken thighs", "chicken breast"],
    "beef": ["beef", "beef chuck", "ground beef", "flank steak", "karubi"],
    "lamb": ["lamb"],
    "spinach": ["spinach"],
    "broccoli": ["broccoli"],
    "carrots": ["carrots"],
    "celery": ["celery"],
    "chickpeas": ["chickpeas"],
    "artichoke": ["artichoke"],
    "mint": ["mint"],
    "basil": ["basil"],
    "herbs": ["basil", "cilantro", "parsley", "thyme", "sage", "rosemary"],
    "cheese": ["manchego cheese", "parmesan", "goat cheese", "cream cheese"],
    "cilantro": ["cilantro"],
    "parsley": ["parsley"],
    "thyme": ["thyme"],
    "sage": ["sage"],
    "rosemary": ["rosemary"],
    "tomato": ["tomatoes", "cherry tomatoes", "heirloom tomatoes", "slicer tomatoes"],
    "cucumber": ["cucumbers"],
    "pepper": ["peppers", "facing heaven peppers", "standard american kitchen spices"],
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\b\d+(?:\.\d+)?(?:[-/]\d+)?\b", " ", value)
    value = re.sub(
        r"\b(?:oz|ounce|ounces|lb|lbs|pound|pounds|cup|cups|tbsp|tsp|tablespoon|"
        r"tablespoons|teaspoon|teaspoons|clove|cloves|stalk|stalks|bunch|head|"
        r"heads|piece|pieces|large|medium|small|fresh|whole|dried|about|for|"
        r"serving|servings|to taste|optional)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def inventory_names(value):
    if isinstance(value, dict):
        if value.get("name"):
            yield str(value["name"])
        else:
            for child in value.values():
                yield from inventory_names(child)
    elif isinstance(value, list):
        for child in value:
            yield from inventory_names(child)


def flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from flatten_strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from flatten_strings(child)


def public_ingredient_lines(recipe):
    lines = []
    for line in flatten_strings(recipe.get("recipe_ingredients", [])):
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def requirements_for(recipe):
    lines = public_ingredient_lines(recipe)
    if lines:
        return lines, "public recipe ingredient lines"
    keys = [str(x).strip() for x in recipe.get("key_ingredients", []) if str(x).strip()]
    if keys:
        return keys, "catalog key ingredients"
    return [], "not enough public ingredient data"


def inventory_match(requirement, inventory_blob):
    req = normalize(requirement)
    if not req:
        return False
    # Tap water is not tracked as a kitchen-inventory item.
    if req == "water":
        return True
    # Offal is identity-sensitive: beef cuts do not satisfy a tripe requirement.
    if "tripe" in req:
        return bool(re.search(r"\btripe\b", inventory_blob))
    if "shishito" in req or "padron" in req:
        return bool(re.search(r"\b(?:shishito|padron)\b", inventory_blob))
    if "yeast" in req:
        return bool(re.search(r"\byeast\b", inventory_blob))
    for alias, candidates in sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in req:
            return any(candidate in inventory_blob for candidate in candidates)
    # Exact phrase matching is intentionally conservative. A fuzzy token match
    # can mark bean sprouts present merely because bean-thread noodles are stocked.
    return req in inventory_blob


def status_for_lines(lines, inventory_blob):
    return [
        {"name": line, "present": inventory_match(line, inventory_blob)}
        for line in lines
    ]


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory_blob = " | ".join(normalize(name) for name in inventory_names(inventory))
    as_of = dt.date.today().isoformat()
    for recipe in data["recipes"]:
        ingredient_lines = public_ingredient_lines(recipe)
        recipe["ingredient_inventory"] = status_for_lines(ingredient_lines, inventory_blob)
        requirements, basis = requirements_for(recipe)
        if not requirements:
            recipe["inventory_fit"] = {
                "percent": None,
                "matched": 0,
                "total": 0,
                "as_of": as_of,
                "basis": "not enough public ingredient data",
            }
            continue
        matched = sum(inventory_match(item, inventory_blob) for item in requirements)
        recipe["inventory_fit"] = {
            "percent": round(100 * matched / len(requirements)),
            "matched": matched,
            "total": len(requirements),
            "as_of": as_of,
            "basis": basis,
        }
    data["inventory_fit"] = {
        "updated": as_of,
        "method": "Deterministic ingredient-line presence coverage; practical equivalents accepted; quantities, freshness, and exact recipe identity are not validated.",
        "private_source": "local household inventory; not published",
    }
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
    print(f"updated inventory fit for {len(data['recipes'])} recipes as of {as_of}")
    for recipe in data["recipes"]:
        fit = recipe["inventory_fit"]
        display = "—" if fit["percent"] is None else f"{fit['percent']}%"
        print(f"{display:>4}  {recipe['title']}")


if __name__ == "__main__":
    main()
