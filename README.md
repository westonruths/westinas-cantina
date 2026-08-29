# Westina’s Cantina

A public, component-based family recipe menu for building meals from the Ruths household’s trusted recipe collection.

## Menu model

The site uses dayparts—**Breakfast**, **Lunch**, and **Dinner**—then filters recipes by reusable component type. Dinner is intentionally organized into **Proteins**, **Veggies**, **Carbs**, **Soups**, and **Sauces & Extras**, rather than restaurant-style “mains” and “appetizers.”

When planning a week, check the live kitchen inventory against this menu first. Explore new recipes only when the existing menu has less than roughly 50% ingredient overlap, as directed by the family workflow.

## Data provenance

- 69 recipe rows imported from the uploaded Notion export.
- 62 of 66 public source links have concise in-site ingredient and step cards; four source links remain explicitly marked unavailable because the source is video/social-only or blocked.
- Duplicate exported rows were consolidated by canonical recipe URL, and conceptual variants such as Focaccia are grouped without deleting their distinct sources.
- Household golden recipes from the health-profile registry were merged and missing golden entries were added.
- Private inline household instructions and the attached private pasta PDF are not published; those entries appear without a public source link.
- Recipe stories and extra editorial copy are not imported; the extraction script stores ingredients, yield/timing metadata, and cooking steps only.

## Local development

```bash
python3 -m http.server 8000
# open http://localhost:8000
python3 scripts/validate.py
```

The site is plain static HTML/CSS/JS so it can be hosted directly by GitHub Pages.
