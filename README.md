# Westina’s Cantina

A public, component-based family recipe menu for building meals from the Ruths household’s trusted recipe collection.

## Menu model

The site is a dinner planner with two restaurant-style browsing modes:

- **Dishes:** Main Courses, Proteins, Soups, Appetizers & Small Plates, and Sides & Extras.
- **Components / Sides:** standalone Proteins, Vegetables & Salads, Carbs & Grains, Soups, and Sauces & Extras.

Each recipe is published for dinner only (`meal_slots: ["dinner"]`); every planned dinner is assembled from one Protein, one Carb, and one Vegetable component.

The menu is sorted by current use-first urgency, then inventory fit. Recipes whose inferred primary ingredient is explicitly absent are excluded from the menu and suggestion pools. Fit is deterministic ingredient-line presence coverage, not a quantity or freshness check.

## Data provenance

- 80 recipe rows are currently published: the existing Notion/registry catalog plus eight source-verified additions selected for current inventory gaps or explicitly requested by the household.
- 77 linked source rows have concise in-site ingredient and step cards; one source remains explicitly unavailable because it is video/social-only or blocked, and two private/household rows have no public source link.
- The eight added candidates—How to Cook Broccoli, Lebanese Rice, Grilled Lemon Chicken, Creamy Cucumber Salad, Shirazi Salad, Tomato Cucumber Avocado Salad, Classic Greek Salad, and Basil Walnut Pesto—each display the canonical source URL and a source photo; the first seven display a 5.0 rating with at least 10 ratings, and Basil Walnut Pesto displays 5.0 from 150 ratings.
- 68 of 80 recipes have verified public source thumbnails; private, blocked, video-only, and otherwise unresolved sources remain image-less rather than receiving guessed images.
- Duplicate exported rows were consolidated by canonical recipe URL, and conceptual variants such as Focaccia are grouped without deleting their distinct sources.
- Household golden recipes from the health-profile registry were merged and missing golden entries were added.
- Private inline household instructions and the attached private pasta PDF are not published; those entries appear without a public source link.
- Recipe stories and extra editorial copy are not imported; the extraction script stores ingredients, yield/timing metadata, and cooking steps only.
- Every recipe carries deterministic inventory-fit metadata generated locally from the private household inventory. The public data includes the percentage, matched-count, date, and a present/not-present flag for each public ingredient line; raw inventory names, quantities, and missing-item lists are not published.

## Local development

```bash
python3 -m http.server 8000
# open http://localhost:8000
python3 scripts/add_trusted_candidates.py
python3 scripts/refresh_recipe_photos.py
python3 scripts/update_inventory_fit.py
python3 scripts/audit_inventory_fit.py
python3 scripts/validate.py
```

The site is plain static HTML/CSS/JS so it can be hosted directly by GitHub Pages.
