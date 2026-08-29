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
ci=data.get('content_import',{})
linked=sum(bool(r.get('source_url')) for r in data['recipes'])
embedded=sum(r.get('content_status') in ('extracted','extracted_fallback') for r in data['recipes'])
assert ci.get('linked_targets')==linked, (ci.get('linked_targets'),linked)
assert ci.get('extracted')==embedded, (ci.get('extracted'),embedded)
assert ci.get('extracted')+ci.get('unavailable')==linked, (ci.get('extracted'),ci.get('unavailable'),linked)
for r in data['recipes']:
    if r.get('content_status') in ('extracted','extracted_fallback'):
        assert r.get('recipe_ingredients') or r.get('recipe_steps'), r['title']
for f in ['index.html','assets/styles.css','assets/app.js']:
    assert (root/f).exists(), f
print(f"valid: {len(data['recipes'])} recipes; {sum(bool(r['golden']) for r in data['recipes'])} golden")
