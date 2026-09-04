# Westina’s Cantina

A public, component-based family recipe menu for building meals from the Ruths household’s trusted recipe collection.

## Menu model

The site is a dinner planner with two restaurant-style browsing modes:

- **Dishes:** Main Courses, Proteins, Soups, Appetizers & Small Plates, and Sides & Extras.
- **Components / Sides:** standalone Proteins, Vegetables & Salads, Carbs & Grains, Soups, and Sauces & Extras.

Each recipe is published for dinner only (`meal_slots: ["dinner"]`); every planned dinner is assembled from one Protein, one Carb, and one Vegetable component. The planner uses `data/dinner-planner.json` to keep those components cuisine-compatible and under 30 active minutes on weekdays or 60 active minutes on weekends; oven and air-fryer time is excluded.

The planner is a rolling local-date calendar: it starts on the browser’s current day, shows the next seven dates, resets saved plans when the date changes, and reloads itself after local midnight. On page load and every five minutes while open, it checks the latest published aggregate inventory-fit timestamp and reloads when that timestamp changes. The inventory line displays the latest published aggregate refresh date; private inventory is never sent to the browser. Run `scripts/update_inventory_fit.py` and publish the updated data for refreshed inventory fit to appear on the public site.
The menu is sorted by current use-first urgency, then inventory fit. Recipes whose inferred primary ingredient is explicitly absent are excluded from the menu and suggestion pools. The automatic calendar limits each protein category to two dinners per seven-day plan; exact recipe reuse is considered only after the category rotation is applied. Fit is deterministic ingredient-line presence coverage, not a quantity or freshness check.

## Data provenance

- 84 recipe rows are currently published: the existing Notion/registry catalog, eight source-verified additions selected for current inventory gaps or explicitly requested by the household, and four concise household-reference basics for weekday convenience.
- 78 linked source rows have concise in-site ingredient and step cards; one source remains explicitly unavailable because it is video/social-only or blocked, and five private/household rows have no public source link.
- The eight added candidates—How to Cook Broccoli, Lebanese Rice, Grilled Lemon Chicken, Creamy Cucumber Salad, Shirazi Salad, Tomato Cucumber Avocado Salad, Classic Greek Salad, and Basil Walnut Pesto—each display the canonical source URL and a source photo; the first seven display a 5.0 rating with at least 10 ratings, and Basil Walnut Pesto displays 5.0 from 150 ratings.
- 68 of 84 recipes have verified public source thumbnails; private, blocked, video-only, and otherwise unresolved sources remain image-less rather than receiving guessed images.
- Duplicate exported rows were consolidated by canonical recipe URL, and conceptual variants such as Focaccia are grouped without deleting their distinct sources.
- Four Golden convenience additions are intentionally short and flexible: Rice Cooker Rice, Air Fryer Broccoli, Chicken Thighs (Oven or Air Fryer), and Caprese Salad. Rice and chicken remain household references; Air Fryer Broccoli is linked to the verified Julie’s Eats & Treats recipe page and selected for its five simple ingredients and 7–9 minute air-fryer method. Caprese requires fresh tomatoes and is inventory-gated when those are unavailable.
- Private inline household instructions and the attached private pasta PDF are not published; those entries appear without a public source link.
- Recipe stories and extra editorial copy are not imported; the extraction script stores ingredients, yield/timing metadata, and cooking steps only.
- Every recipe carries deterministic inventory-fit metadata generated locally from the private household inventory. The public data includes the percentage, matched-count, date, and a present/not-present flag for each public ingredient line; raw inventory names, quantities, and missing-item lists are not published.

## Local development

```bash
python3 -m http.server 8000
# open http://localhost:8000
python3 scripts/add_trusted_candidates.py
python3 scripts/add_household_basics.py
python3 scripts/refresh_recipe_photos.py
python3 scripts/update_inventory_fit.py
python3 scripts/audit_inventory_fit.py
python3 scripts/validate.py
python3 scripts/test_dinner_planner.py
```

The site is plain static HTML/CSS/JS so it can be hosted directly by GitHub Pages.
