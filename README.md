# Westina’s Cantina

A public, component-based family recipe menu for building meals from the Ruths household’s trusted recipe collection.

## Menu model

The site uses dayparts—**Breakfast**, **Lunch**, and **Dinner**—with two restaurant-style browsing modes:

- **Dishes:** Main Courses, Proteins, Soups, Appetizers & Small Plates, and Sides & Extras.
- **Components / Sides:** standalone Proteins, Vegetables & Salads, Carbs & Grains, Soups, and Sauces & Extras.

Every menu item can be dragged into the persistent seven-day weekly board, or added through the day selector for touch/mobile use. The board stores only in the browser’s local storage; it is not published.

The menu is sorted by current inventory fit within each section. Fit is deterministic ingredient-line presence coverage, not a quantity or freshness check.

## Data provenance

- 69 recipe rows imported from the uploaded Notion export.
- 62 of 66 public source links have concise in-site ingredient and step cards; four source links remain explicitly marked unavailable because the source is video/social-only or blocked.
- Duplicate exported rows were consolidated by canonical recipe URL, and conceptual variants such as Focaccia are grouped without deleting their distinct sources.
- Household golden recipes from the health-profile registry were merged and missing golden entries were added.
- Private inline household instructions and the attached private pasta PDF are not published; those entries appear without a public source link.
- Recipe stories and extra editorial copy are not imported; the extraction script stores ingredients, yield/timing metadata, and cooking steps only.
- Every recipe carries deterministic inventory-fit metadata generated locally from the private household inventory. The public data includes the percentage, matched-count, date, and a present/not-present flag for each public ingredient line; raw inventory names, quantities, and missing-item lists are not published.

## Local development

```bash
python3 -m http.server 8000
# open http://localhost:8000
python3 scripts/update_inventory_fit.py
python3 scripts/audit_inventory_fit.py
python3 scripts/validate.py
```

The site is plain static HTML/CSS/JS so it can be hosted directly by GitHub Pages.
