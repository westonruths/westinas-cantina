#!/usr/bin/env python3
import json
import re
from itertools import combinations
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'data/recipes.json').read_text())
planner=json.loads((root/'data/dinner-planner.json').read_text())
assert data['site_name']=="Westina’s Cantina"
assert data['recipe_count']==len(data['recipes'])
assert len({r['id'] for r in data['recipes']})==len(data['recipes'])
assert data.get('inventory_fit', {}).get('private_source') == 'local household inventory; not published'
meta=planner['recipe_meta']
assert planner['limits'] == {'weekday': 29, 'weekend': 59}
assert meta and set(meta) <= {r['id'] for r in data['recipes']}
assert all(item.get('family') and isinstance(item.get('active_minutes'), int) and 0 <= item['active_minutes'] < 60 for item in meta.values())
for first, row in planner['compatibility'].items():
    for second, allowed in row.items():
        assert planner['compatibility'].get(second, {}).get(first) == allowed
recipe_by_id={r['id']: r for r in data['recipes']}
expected_basics={
    'household-rice-cooker-rice': 'carb',
    'household-roasted-any-vegetable': 'veggie',
    'household-chicken-thighs-oven-air-fryer': 'protein',
    'household-caprese-salad': 'veggie',
}
for recipe_id, component in expected_basics.items():
    recipe=recipe_by_id[recipe_id]
    assert recipe['golden'] and recipe['content_status']=='household_reference'
    assert recipe['component_types']==[component]
assert recipe_by_id['household-caprese-salad']['inventory_fit']['primary_present'] is False
assert recipe_by_id['household-chicken-thighs-oven-air-fryer']['inventory_fit']['primary_present'] is True
assert planner['compatibility']['universal']['chinese'] and planner['compatibility']['italian']['universal']
assert len(planner['recipe_meta']) >= len(expected_basics)
assert len(planner['pairings']) >= 7
for pairing in planner['pairings']:
    assert pairing['day_type'] in planner['limits']
    components=pairing['components']
    assert set(components) == {'protein', 'carb', 'veggie'}
    ids=list(components.values())
    assert len(set(ids)) == 3 and all(recipe_by_id[id]['id'] in meta for id in ids)
    families=[meta[id]['family'] for id in ids]
    assert all(planner['compatibility'][first][second] for first, second in combinations(families, 2))
    assert pairing['active_minutes'] == sum(meta[id]['active_minutes'] for id in ids)
    assert pairing['active_minutes'] < planner['limits'][pairing['day_type']]
for recipe in data['recipes']:
    fit=recipe.get('inventory_fit', {})
    assert fit.get('as_of') and fit.get('basis')
    assert fit.get('total', 0) >= fit.get('matched', 0) >= 0
    assert fit.get('use_first_matches', 0) >= 0
    assert fit.get('use_first_score', 0) >= 0
    assert isinstance(fit.get('primary_ingredients'), list)
    assert fit.get('primary_total', 0) == len(fit.get('primary_ingredients', []))
    assert fit.get('primary_matched', 0) <= fit.get('primary_total', 0)
    assert fit.get('primary_present') is None or isinstance(fit.get('primary_present'), bool)
    assert fit.get('percent') is None or 0 <= fit['percent'] <= 100
    statuses=recipe.get('ingredient_inventory', [])
    assert isinstance(statuses, list)
    assert all(isinstance(item, dict) and isinstance(item.get('name'), str) and (isinstance(item.get('present'), bool) or 'present' not in item) for item in statuses)
    if recipe.get('recipe_ingredients'):
        assert len(statuses) == len(recipe['recipe_ingredients']), recipe['title']
    if fit.get('basis') == 'public recipe ingredient lines':
        assert fit['total'] == len(statuses), recipe['title']
        assert fit['matched'] == sum(item['present'] for item in statuses), recipe['title']
    rating=recipe.get('source_rating')
    if rating:
        assert float(rating['rating']) >= 5.0
        assert int(rating['rating_count']) >= 10
        assert recipe.get('image_url')
    assert recipe['meal_slots'] == ['dinner'], recipe['title']
    assert recipe['title'] and recipe['meal_slots'] and recipe['component_types']
assert sum(bool(r['golden']) for r in data['recipes']) >= 7
ci=data.get('content_import',{})
linked=sum(bool(r.get('source_url')) for r in data['recipes'])
embedded=sum(r.get('content_status') in ('extracted','extracted_fallback') for r in data['recipes'])
household=sum(r.get('content_status') == 'household_reference' for r in data['recipes'])
assert ci.get('linked_targets')==linked, (ci.get('linked_targets'),linked)
assert ci.get('extracted')==embedded, (ci.get('extracted'),embedded)
assert ci.get('extracted')+ci.get('unavailable')==linked, (ci.get('extracted'),ci.get('unavailable'),linked)
for r in data['recipes']:
    if r.get('content_status') in ('extracted','extracted_fallback','household_reference'):
        assert r.get('recipe_ingredients') or r.get('recipe_steps'), r['title']
        steps=[]
        def flatten(value):
            if isinstance(value,list):
                for child in value: flatten(child)
            elif value: steps.append(str(value))
        flatten(r.get('recipe_steps',[]))
        assert any(len(step.split()) >= 6 for step in steps), f"steps look heading-only: {r['title']}"
for f in ['index.html','assets/styles.css','assets/app.js']:
    assert (root/f).exists(), f
print(f"valid: {len(data['recipes'])} recipes; {sum(bool(r['golden']) for r in data['recipes'])} golden")
