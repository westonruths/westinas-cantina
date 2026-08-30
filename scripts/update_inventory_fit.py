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
    "peanut oil": ["peanut oil"],
    "vegetable oil": ["vegetable oil"],
    "olive oil": ["olive oil"],
    "lemon": ["lemons"],
    "garlic": ["garlic"],
    "garlic powder": ["garlic powder"],
    "onion powder": ["onion powder"],
    "ginger": ["ginger"],
    "scallions": ["green onions"],
    "green onion": ["green onions"],
    "onion": ["yellow onion", "large yellow onion"],
    "kale": ["lacinato kale", "kale"],
    "lacinato kale": ["lacinato kale", "kale"],
    "lettuce": ["romaine lettuce", "lettuce"],
    "leaf lettuce": ["romaine lettuce", "leaf lettuce", "lettuce"],
    "carrot": ["carrots"],
    "potatoes": ["golden potatoes", "hash brown potatoes"],
    "flour": ["flour"],
    "bread": ["keto bread", "bread"],
    "pecorino cheese": ["pecorino", "parmesan"],
    "feta cheese": ["feta"],
    "mozzarella cheese": ["mozzarella"],
    "romano cheese": ["romano"],
    "cheddar": ["cheddar"],
    "parmesan cheese": ["parmesan"],
    "eggs": ["eggs"],
    "egg": ["eggs"],
    "chicken bouillon": ["chicken bouillon"],
    "chicken stock": ["chicken stock"],
    "chicken broth": ["chicken stock"],
    "beef broth": ["beef broth"],
    "beef stock": ["beef stock"],
    "white wine": ["white wine"],
    "red wine": ["red wine"],
    "red wine vinegar": ["red wine vinegar"],
    "white wine vinegar": ["white wine vinegar"],
    "rice vinegar": ["rice vinegar"],
    "black rice vinegar": ["chinkiang black vinegar"],
    "chinese black vinegar": ["chinkiang black vinegar"],
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
    "long hot green peppers": ["long hot green peppers"],
    "long hot red pepper": ["long hot red pepper"],
    "red bell peppers": ["red bell peppers"],
    "green bell pepper": ["green bell peppers"],
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
    "mahi mahi": ["mahi mahi"],
    "dried shrimp": ["dried shrimp"],
    "shrimp paste": ["shrimp paste"],
    "pork belly": ["pork belly"],
    "ground pork": ["ground pork"],
    "pork": ["pork belly", "ground pork"],
    "chicken thigh": ["chicken thighs"],
    "chicken": ["chicken", "chicken thighs", "chicken breast"],
    "chicken fat": ["chicken fat"],
    "whole chicken": ["whole chicken"],
    "rotisserie chicken": ["rotisserie chicken"],
    "pork shoulder": ["pork shoulder"],
    "pork chops": ["pork chops"],
    "beef shank": ["beef shank"],
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
    "oregano": ["oregano"],
    "cheese": ["manchego cheese", "parmesan", "goat cheese", "cream cheese"],
    "cilantro": ["cilantro"],
    "parsley": ["parsley"],
    "thyme": ["thyme"],
    "sage": ["sage"],
    "rosemary": ["rosemary"],
    "tomato": ["tomatoes", "cherry tomatoes", "heirloom tomatoes", "slicer tomatoes"],
    "tomato paste": ["tomato paste"],
    "sundried tomatoes": ["sundried tomatoes"],
    "sun dried tomatoes": ["sun dried tomatoes"],
    "cucumber": ["cucumbers"],
    "peppercorn": ["peppercorns"],
    "sichuan peppercorn": ["sichuan red peppercorns", "sichuan green peppercorns"],
    "pepper": ["peppers", "facing heaven peppers", "standard american kitchen spices"],
}

# These requirements must match a complete inventory item, not a substring of
# a nearby ingredient (for example red wine must not match red wine vinegar).
EXACT_CANDIDATES = {
    "beef broth", "beef stock", "white wine", "red wine", "rice vinegar",
    "black rice vinegar", "chicken fat", "whole chicken", "rotisserie chicken",
    "pork shoulder", "pork chops", "beef shank", "dried shrimp", "shrimp paste",
    "sesame seeds", "olives", "yeast", "feta", "mozzarella", "romano",
    "cumin seeds", "coriander seeds", "cloves", "jalapenos", "pesto", "chimichurri",
    "peanut oil", "vegetable oil", "garlic powder", "onion powder", "tomato paste",
    "sundried tomatoes", "sun dried tomatoes", "long hot green peppers",
    "long hot red pepper", "red bell peppers", "green bell pepper",
}

STRICT_TERMS = {
    *EXACT_CANDIDATES,
    "feta cheese", "mozzarella cheese", "romano cheese", "cheddar",
    "red wine vinegar", "white wine vinegar", "chinese black vinegar",
    "bean sprouts", "whole chicken", "rotisserie chicken", "pork shoulder",
    "pork chops", "beef shank", "chicken fat", "dried shrimp", "shrimp paste",
    "garlic powder", "onion powder", "tomato paste", "sundried tomatoes",
    "sun dried tomatoes", "peanut oil", "vegetable oil",
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\b\d+(?:\.\d+)?(?:[-/]\d+)?\b", " ", value)
    value = re.sub(
        r"\b(?:oz|ounce|ounces|lb|lbs|pound|pounds|cup|cups|tbsp|tsp|tablespoon|"
        r"tablespoons|teaspoon|teaspoons|clove|cloves|stalk|stalks|bunch|head|"
        r"heads|piece|pieces|about|for|serving|servings|to taste|optional)\b",
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


def normalized_inventory_items(value):
    return [normalize(name) for name in inventory_names(value) if normalize(name)]


def phrase_in(text, phrase):
    return bool(re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text))


def term_matches(text, term):
    term = normalize(term)
    variants = [term]
    if term.endswith("s"):
        variants.append(term[:-1])
    else:
        variants.append(term + "s")
    return any(phrase_in(text, variant) for variant in variants)


def inventory_has(items, candidate, exact=False):
    candidate = normalize(candidate)
    if exact:
        return candidate in items
    return any(phrase_in(item, candidate) for item in items)


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


PRIMARY_PRODUCE = [
    "shishito", "artichoke", "kale", "broccoli", "cauliflower", "bok choy",
    "spinach", "eggplant", "cucumber", "tomato", "beet", "leek", "potato",
    "lettuce", "zucchini", "carrot", "celery", "chickpea", "egg",
]
PRIMARY_PROTEINS = [
    "chicken", "pork", "beef", "lamb", "shrimp", "salmon", "mahi mahi",
    "duck", "tofu", "sausage", "turkey", "fish",
]
PRIMARY_CARBS = [
    "rice", "noodle", "pasta", "orzo", "couscous", "focaccia", "fettuccine", "bread",
    "dumpling", "pierogi", "quinoa", "millet",
]
PRIMARY_CANONICAL = {
    "kale": "lacinato kale",
    "potato": "potatoes",
    "lettuce": "leaf lettuce",
    "carrot": "carrots",
    "egg": "eggs",
    "focaccia": "flour",
    "fettuccine": "pasta",
    "noodle": "noodles",
    "pasta": "pasta",
    "orzo": "orzo",
    "couscous": "couscous",
    "rice": "rice",
    "bread": "bread",
}


def canonical_primary(term):
    return PRIMARY_CANONICAL.get(term, term)


def infer_primary_ingredients(recipe):
    """Return one identity-bearing ingredient for the recipe's main food."""
    title = normalize(recipe.get("title", ""))
    types = set(recipe.get("component_types", []))
    ingredient_text = " ".join(normalize(line) for line in public_ingredient_lines(recipe))
    primary_cut_rules = [
        ("honeycomb beef tripe", "tripe"),
        ("pork shoulder", "pork shoulder"),
        ("pork belly", "pork belly"),
        ("whole chicken", "whole chicken"),
        ("rotisserie chicken", "rotisserie chicken"),
        ("beef shank", "beef shank"),
        ("rack of lamb", "lamb"),
    ]
    for phrase, canonical in primary_cut_rules:
        if phrase in ingredient_text:
            return [canonical]
    # Produce-led salads, dips, and vegetable dishes should not inherit a
    # secondary protein tag as their primary ingredient.
    if re.search(r"salad|dip|banchan|shishito|artichoke|kale|broccoli|cauliflower|bok choy|spinach|eggplant|cucumber|tomato|beet|leek|potato|lettuce", title):
        for term in PRIMARY_PRODUCE:
            if term in title:
                return [canonical_primary(term)]
    if "protein" in types:
        for term in PRIMARY_PROTEINS:
            if term in title:
                return [canonical_primary(term)]
    if "carb" in types:
        for term in PRIMARY_CARBS:
            if term in title:
                return [canonical_primary(term)]
    keys = [str(x).strip() for x in recipe.get("key_ingredients", []) if str(x).strip()]
    preferred_groups = []
    if "protein" in types:
        preferred_groups.append(PRIMARY_PROTEINS)
    if "veggie" in types:
        preferred_groups.append(PRIMARY_PRODUCE)
    if "carb" in types:
        preferred_groups.append(PRIMARY_CARBS)
    for group in preferred_groups:
        for key in keys:
            key_normalized = normalize(key)
            for term in group:
                if term in key_normalized:
                    return [canonical_primary(term)]
    for key in keys:
        key_normalized = normalize(key)
        for term in PRIMARY_PRODUCE + PRIMARY_PROTEINS + PRIMARY_CARBS:
            if term in key_normalized:
                return [canonical_primary(term)]
    return []


def inventory_match(requirement, inventory_items_list):
    req = normalize(requirement)
    if not req:
        return False
    # Tap water is not tracked as a kitchen-inventory item.
    if req == "water":
        return True
    # Specific identities short-circuit generic aliases. Keep evaluating only
    # when the source line explicitly offers an alternative with "or".
    for strict in sorted(STRICT_TERMS, key=len, reverse=True):
        if term_matches(req, strict):
            candidates = ALIASES.get(strict, [strict])
            matched = any(inventory_has(inventory_items_list, candidate, exact=True) for candidate in candidates)
            if matched or " or " not in req:
                return matched
    # Identity-sensitive checks must happen before broad aliases.
    if "tripe" in req:
        return inventory_has(inventory_items_list, "tripe")
    if "shishito" in req or "padron" in req:
        return inventory_has(inventory_items_list, "shishito") or inventory_has(inventory_items_list, "padron")
    if "yeast" in req:
        return inventory_has(inventory_items_list, "yeast")
    for alias, candidates in sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if term_matches(req, alias):
            return any(
                inventory_has(
                    inventory_items_list,
                    candidate,
                    exact=normalize(candidate) in EXACT_CANDIDATES,
                )
                for candidate in candidates
            )
    # Exact phrase matching is intentionally conservative. A fuzzy token match
    # can mark bean sprouts present merely because bean-thread noodles are stocked.
    return inventory_has(inventory_items_list, req, exact=True)


def status_for_lines(lines, inventory_items_list):
    return [
        {"name": line, "present": inventory_match(line, inventory_items_list)}
        for line in lines
    ]


def use_first_score(requirements, use_first_items):
    score = 0
    for requirement in requirements:
        for index, item in enumerate(use_first_items):
            if inventory_match(requirement, [item]):
                score += len(use_first_items) - index
                break
    return score


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory_items_list = normalized_inventory_items(inventory)
    use_first_items = normalized_inventory_items(inventory.get("inventory", {}).get("use_first", []))
    as_of = dt.date.today().isoformat()
    for recipe in data["recipes"]:
        ingredient_lines = public_ingredient_lines(recipe)
        recipe["ingredient_inventory"] = status_for_lines(ingredient_lines, inventory_items_list)
        primary = infer_primary_ingredients(recipe)
        primary_flags = [inventory_match(item, inventory_items_list) for item in primary]
        primary_present = None if not primary else all(primary_flags)
        requirements, basis = requirements_for(recipe)
        if not requirements:
            recipe["inventory_fit"] = {
                "percent": None,
                "matched": 0,
                "total": 0,
                "use_first_matches": 0,
                "use_first_score": 0,
                "primary_ingredients": primary,
                "primary_matched": sum(primary_flags),
                "primary_total": len(primary),
                "primary_present": primary_present,
                "as_of": as_of,
                "basis": "not enough public ingredient data",
            }
            continue
        matched = sum(inventory_match(item, inventory_items_list) for item in requirements)
        use_first_matches = sum(inventory_match(item, use_first_items) for item in requirements)
        recipe["inventory_fit"] = {
            "percent": round(100 * matched / len(requirements)),
            "matched": matched,
            "total": len(requirements),
            "use_first_matches": use_first_matches,
            "use_first_score": use_first_score(requirements, use_first_items),
            "primary_ingredients": primary,
            "primary_matched": sum(primary_flags),
            "primary_total": len(primary),
            "primary_present": primary_present,
            "as_of": as_of,
            "basis": basis,
        }
    data["inventory_fit"] = {
        "updated": as_of,
        "method": "Deterministic ingredient-line presence coverage plus ordered use-first priority score; practical equivalents accepted; quantities, freshness, and exact recipe identity are not validated.",
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
