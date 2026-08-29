#!/usr/bin/env python3
"""Attach aggregate, non-sensitive inventory-fit scores to public recipe data.

The private inventory is read locally and is never copied into the public site.
Scores describe ingredient presence only; quantities, freshness, and substitutions
that would change a recipe's identity are not validated.
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

# Golden entries had no imported key-ingredient metadata, so give them explicit
# canonical requirements. Toppings/finishes that are genuinely optional are not
# allowed to distort the base recipe's fit score.
REQUIREMENT_OVERRIDES = {
    "Blistered Shishito Peppers": ["shishito peppers", "oil", "lemon", "salt"],
    "Overnight Focaccia": ["flour", "water", "yeast", "honey", "olive oil", "salt"],
    "Twice Cooked Pork (Hui Guo Rou, 回锅肉)": [
        "pork belly", "ginger", "oil", "doubanjiang", "fermented black beans",
        "garlic", "leek or green garlic", "fresh red chiles", "soy sauce",
        "Shaoxing wine", "sugar",
    ],
    "Hasselback potatoes": [
        "potatoes", "oil", "salt and pepper", "sage", "garlic butter",
        "parsley", "red pepper flakes",
    ],
    "Korean BBQ Salad": [
        "leaf lettuce", "garlic", "green onion", "onion", "soy sauce",
        "fish sauce", "sugar", "white vinegar", "Korean hot pepper flakes",
        "sesame oil", "sesame seeds",
    ],
    "Steamed egg": [
        "eggs", "water", "scallions", "salt", "chicken bouillon", "oil",
        "white pepper",
    ],
    "Tuscan Kale Salad": [
        "lacinato kale", "bread", "garlic", "pecorino cheese", "olive oil",
        "lemon", "salt", "black pepper",
    ],
}

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
    "fermented black beans": ["douchi"],
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


def requirements_for(recipe):
    title = recipe["title"]
    if title in REQUIREMENT_OVERRIDES:
        return REQUIREMENT_OVERRIDES[title], "canonical key ingredients"
    keys = [str(x).strip() for x in recipe.get("key_ingredients", []) if str(x).strip()]
    if keys:
        return keys, "catalog key ingredients"
    lines = []
    for line in flatten_strings(recipe.get("recipe_ingredients", [])):
        line = line.strip()
        if not line or "optional" in line.lower():
            continue
        lines.append(line)
    return lines, "recipe ingredient lines"


def inventory_match(requirement, inventory_blob):
    req = normalize(requirement)
    if not req:
        return False
    # Identity-sensitive checks must happen before broad aliases.
    if "shishito" in req or "padron" in req:
        return bool(re.search(r"\b(?:shishito|padron)\b", inventory_blob))
    if "yeast" in req:
        return bool(re.search(r"\byeast\b", inventory_blob))
    for alias, candidates in sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in req:
            return any(candidate in inventory_blob for candidate in candidates)
    # Exact phrase first, then a distinctive token for catalog keys.
    if req in inventory_blob:
        return True
    stop = {"fresh", "dried", "ground", "chopped", "sliced", "minced", "recipe", "leaves", "leaf"}
    tokens = [token for token in req.split() if len(token) >= 4 and token not in stop]
    return any(re.search(rf"\b{re.escape(token)}\b", inventory_blob) for token in tokens)


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory_blob = " | ".join(normalize(name) for name in inventory_names(inventory))
    as_of = dt.date.today().isoformat()
    for recipe in data["recipes"]:
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
        "method": "Approximate ingredient-presence coverage; practical equivalents accepted; quantities, freshness, and exact recipe identity are not validated.",
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
