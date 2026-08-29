#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'data/recipes.json').read_text())
assert data['site_name']=="Westina’s Cantina"
assert data['recipe_count']==len(data['recipes'])
assert len({r['id'] for r in data['recipes']})==len(data['recipes'])
assert all(r['title'] and r['meal_slots'] and r['component_types'] for r in data['recipes'])
assert sum(bool(r['golden']) for r in data['recipes']) >= 7
for f in ['index.html','assets/styles.css','assets/app.js']:
    assert (root/f).exists(), f
print(f"valid: {len(data['recipes'])} recipes; {sum(bool(r['golden']) for r in data['recipes'])} golden")
