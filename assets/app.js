const DAYS = [
  ['monday', 'Monday'],
  ['tuesday', 'Tuesday'],
  ['wednesday', 'Wednesday'],
  ['thursday', 'Thursday'],
  ['friday', 'Friday'],
  ['saturday', 'Saturday'],
  ['sunday', 'Sunday']
];
const PLAN_KEY = 'westinas-cantina-week-plan-v2';
const params = new URLSearchParams(location.search);
const state = {
  recipes: [],
  slot: 'dinner',
  view: params.get('view') === 'components' ? 'components' : 'dishes',
  query: '',
  plan: loadPlan()
};
const labels = {
  protein: 'Proteins',
  veggie: 'Vegetables & salads',
  carb: 'Carbs & grains',
  soup: 'Soups',
  sauce: 'Sauces & extras',
  other: 'Other'
};
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}[char]));

function loadPlan() {
  const blank = Object.fromEntries(DAYS.map(([key]) => [key, []]));
  try {
    const saved = JSON.parse(localStorage.getItem(PLAN_KEY) || '{}');
    for (const [key] of DAYS) {
      if (Array.isArray(saved[key])) blank[key] = [...new Set(saved[key].filter((id) => typeof id === 'string'))];
    }
  } catch (error) {
    console.warn('Could not load the saved weekly plan', error);
  }
  return blank;
}

function savePlan() {
  try {
    localStorage.setItem(PLAN_KEY, JSON.stringify(state.plan));
  } catch (error) {
    console.warn('Could not save the weekly plan', error);
  }
}

function announce(message) {
  const status = $('#planner-status');
  if (status) status.textContent = message;
}

function humanTime(value) {
  const text = String(value ?? '');
  const match = text.match(/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/i);
  if (!match) return text;
  const output = [];
  if (match[1]) output.push(`${match[1]} hr`);
  if (match[2]) output.push(`${match[2]} min`);
  if (match[3] && !match[1] && !match[2]) output.push(`${match[3]} sec`);
  return output.join(' ');
}

function fitData(recipe) {
  return recipe.inventory_fit || {};
}

function fitPercent(recipe) {
  const value = fitData(recipe).percent;
  return Number.isFinite(value) ? value : null;
}

function fitWidget(recipe, compact = false) {
  const fit = fitData(recipe);
  const percent = fitPercent(recipe);
  const display = percent === null ? '—' : `${percent}%`;
  const label = percent === null
    ? 'Inventory fit unavailable: not enough public ingredient data'
    : `Approximate inventory fit: ${percent} percent; ${fit.matched} of ${fit.total} ingredients present; quantities not checked`;
  const classes = `fit-widget${compact ? ' compact' : ''}${percent === null ? ' unknown' : ''}`;
  const style = `--fit: ${percent === null ? 0 : percent}%;`;
  return `<span class="${classes}" title="${esc(label)}" aria-label="${esc(label)}"><span class="fit-ring" style="${style}"><span>${display}</span></span><span class="fit-copy"><strong>${compact ? 'Fit' : 'On hand'}</strong><small>${percent === null ? 'No public ingredient list' : `${fit.matched} / ${fit.total} ingredients`}</small></span></span>`;
}

function ingredientMarkup(recipe) {
  const lines = recipe.recipe_ingredients || [];
  const statuses = recipe.ingredient_inventory || [];
  return lines.map((item, index) => {
    const status = statuses[index];
    const known = status && typeof status.present === 'boolean';
    const present = known && status.present;
    const icon = !known ? '?' : present ? '✓' : '○';
    const label = !known
      ? 'Inventory status unavailable'
      : present ? 'Present in current inventory' : 'Not confirmed in current inventory';
    const className = !known ? 'unknown' : present ? 'present' : 'missing';
    return `<li><span class="ingredient-status ${className}" role="img" aria-label="${label}">${icon}</span><span>${esc(item)}</span></li>`;
  }).join('');
}

function sourceCredit(recipe) {
  const publisher = recipe.source_publisher && recipe.source_publisher !== 'Notion recipe list'
    ? ` · Source: ${esc(recipe.source_publisher)}`
    : '';
  const originalLink = recipe.source_url
    ? ` · <a href="${esc(recipe.source_url)}" target="_blank" rel="noopener">Original recipe ↗</a>`
    : '';
  const status = recipe.content_status === 'unavailable'
    ? 'Recipe copy unavailable'
    : 'In-site recipe copy';
  return `<span class="source-credit">${status}${publisher}${originalLink}</span>`;
}

function recipeBody(recipe) {
  const available = ['extracted', 'extracted_fallback'].includes(recipe.content_status);
  if (!available) {
    return `<div class="recipe-gap"><strong>Recipe copy unavailable.</strong><span>${esc(recipe.content_error || 'The source did not expose usable ingredient and step data.')}</span></div>`;
  }
  const ingredients = ingredientMarkup(recipe);
  const steps = (recipe.recipe_steps || []).flat(Infinity).map((step) => `<li>${esc(step)}</li>`).join('');
  const timings = Object.entries(recipe.recipe_timings || {})
    .map(([key, value]) => `${esc(key.replace('Time', ' time'))}: ${esc(humanTime(value))}`)
    .join(' · ');
  const metadata = recipe.recipe_yield || timings
    ? `<p class="recipe-meta">${recipe.recipe_yield ? `Yield: ${esc(recipe.recipe_yield)}` : ''}${recipe.recipe_yield && timings ? ' · ' : ''}${timings}</p>`
    : '';
  return `<div class="recipe-copy">${metadata}${ingredients ? `<h4>Ingredients</h4><ul class="ingredients-list">${ingredients}</ul>` : ''}${steps ? `<h4>Steps</h4><ol>${steps}</ol>` : ''}</div>`;
}

function isMainCourse(recipe) {
  const types = recipe.component_types || [];
  if (types.includes('soup')) return false;
  if (!types.includes('protein')) return false;
  if (types.includes('carb')) return true;
  return /pasta|noodle|rice|stew|congee|dumpling|gyros|khao|pierogi|pasta|couscous/i.test(recipe.title);
}

function isAppetizer(recipe) {
  return /salad|dip|artichoke|shishito|marrow|banchan|tapa|bruschetta/i.test(recipe.title);
}

function dishSection(recipe) {
  if ((recipe.component_types || []).includes('soup')) return 'soups';
  if (isMainCourse(recipe)) return 'mains';
  if (isAppetizer(recipe)) return 'appetizers';
  if ((recipe.component_types || []).includes('protein')) return 'proteins';
  return 'sides';
}

function componentSection(recipe) {
  const types = recipe.component_types || [];
  // Full protein-plus-carb dishes belong in the Dishes menu; Components is for
  // standalone building blocks that can be added alongside another dish.
  if (isMainCourse(recipe)) return null;
  if (types.includes('soup')) return 'soups';
  if (types.includes('protein')) return 'proteins';
  if (types.includes('veggie')) return 'vegetables';
  if (types.includes('carb')) return 'carbs';
  if (types.includes('sauce') || types.includes('other')) return 'extras';
  return 'extras';
}

function menuSections() {
  if (state.view === 'components') {
    return [
      ['proteins', 'Proteins', 'Standalone proteins to anchor a meal.'],
      ['vegetables', 'Vegetables & salads', 'Fresh, cooked, and composed vegetable sides.'],
      ['carbs', 'Carbs & grains', 'Rice, noodles, pasta, potatoes, and breads.'],
      ['soups', 'Soups', 'Complete bowls for lighter or one-dish meals.'],
      ['extras', 'Sauces & extras', 'Finishing sauces, toppings, dips, and other small additions.']
    ];
  }
  return [
    ['mains', 'Main courses', 'Complete dishes with a clear center of gravity.'],
    ['proteins', 'Proteins', 'A main protein ready to pair with a side.'],
    ['soups', 'Soups', 'Complete bowls and soup-centered meals.'],
    ['appetizers', 'Appetizers & small plates', 'Salads, dips, and first-bite dishes.'],
    ['sides', 'Sides & extras', 'Vegetables, grains, sauces, and supporting plates.']
  ];
}

function recipeMatches(recipe) {
  if (!recipe.meal_slots.includes(state.slot)) return false;
  if (!state.query) return true;
  const haystack = [
    recipe.title,
    recipe.cuisine,
    ...recipe.key_ingredients,
    ...(recipe.recipe_ingredients || [])
  ].join(' ').toLowerCase();
  return haystack.includes(state.query.toLowerCase());
}

function sortedRecipes(recipes) {
  return [...recipes].sort((a, b) => {
    const aFit = fitPercent(a);
    const bFit = fitPercent(b);
    if (aFit === null && bFit === null) return a.title.localeCompare(b.title);
    if (aFit === null) return 1;
    if (bFit === null) return -1;
    return bFit - aFit || a.title.localeCompare(b.title);
  });
}

function addControls(recipe) {
  const options = DAYS.map(([key, label]) => `<option value="${key}">${label}</option>`).join('');
  return `<div class="add-controls"><select data-day-select aria-label="Choose a day for ${esc(recipe.title)}"><option value="">Add to…</option>${options}</select><button class="add-button" type="button" data-add-id="${esc(recipe.id)}" disabled>Add</button></div>`;
}

function menuEntry(recipe) {
  const tags = [...new Set((recipe.component_types || []).map((type) => labels[type] || type))].join(' · ');
  const badges = `${recipe.golden ? '<span class="badge gold">Golden</span>' : ''}${recipe.tried ? '<span class="badge">Tried</span>' : ''}`;
  return `<article class="menu-entry" draggable="true" data-recipe-id="${esc(recipe.id)}"><div class="menu-entry-row"><div class="menu-entry-copy"><span class="drag-handle" aria-hidden="true">⋮⋮</span><div><div class="menu-entry-badges">${badges}</div><h3>${esc(recipe.title)}</h3><p class="menu-meta">${esc(recipe.cuisine || 'House recipe')}${tags ? ` · ${esc(tags)}` : ''}</p></div></div><div class="menu-entry-actions">${fitWidget(recipe, true)}${addControls(recipe)}</div></div><details class="recipe-details"><summary>View recipe</summary>${recipeBody(recipe)}${sourceCredit(recipe)}</details></article>`;
}

function renderMenu() {
  const filtered = state.recipes.filter(recipeMatches);
  const sections = menuSections();
  let visible = 0;
  $('#menu').innerHTML = sections.map(([id, title, note]) => {
    const recipes = sortedRecipes(filtered.filter((recipe) => (state.view === 'components' ? componentSection(recipe) : dishSection(recipe)) === id));
    if (!recipes.length) return '';
    visible += recipes.length;
    return `<section class="menu-section" aria-labelledby="section-${id}"><div class="section-heading"><div><h3 id="section-${id}">${title}</h3><p>${note}</p></div><span>${recipes.length}</span></div><div class="menu-list">${recipes.map(menuEntry).join('')}</div></section>`;
  }).join('');
  $('#count').textContent = `${visible} ${visible === 1 ? 'recipe' : 'recipes'}`;
  $('#menu-heading').textContent = state.view === 'components' ? 'Components / Sides' : 'Dishes';
  $('.section-kicker').textContent = `${state.slot[0].toUpperCase()}${state.slot.slice(1)} menu`;
  $('#menu-note').textContent = state.view === 'components'
    ? 'Build a meal from standalone proteins, vegetables, carbs, and extras—or switch to Dishes for complete plates.'
    : 'Browse the menu like a restaurant: complete plates first, then proteins, soups, small plates, and sides.';
  $('#empty').hidden = visible > 0;
  bindMenuInteractions();
}

function renderPlanner() {
  const byId = new Map(state.recipes.map((recipe) => [recipe.id, recipe]));
  $('#week-board').innerHTML = DAYS.map(([key, label]) => {
    const ids = state.plan[key] || [];
    const items = ids.map((id) => byId.get(id)).filter(Boolean);
    return `<section class="day-slot" data-day="${key}" aria-label="${label} meal plan"><div class="day-slot-heading"><h3>${label}</h3><span>${items.length ? `${items.length} item${items.length === 1 ? '' : 's'}` : 'Open'}</span></div><div class="day-items">${items.length ? items.map((recipe) => `<div class="planned-item"><span>${esc(recipe.title)}</span><button type="button" data-remove-day="${key}" data-remove-id="${esc(recipe.id)}" aria-label="Remove ${esc(recipe.title)} from ${label}">×</button></div>`).join('') : '<p class="drop-hint">Drop a recipe here</p>'}</div></section>`;
  }).join('');
  bindPlannerInteractions();
}

function addToPlan(day, recipeId) {
  if (!day || !recipeId) return;
  if (!state.plan[day].includes(recipeId)) {
    state.plan[day].push(recipeId);
    savePlan();
    renderPlanner();
    announce(`${state.recipes.find((recipe) => recipe.id === recipeId)?.title || 'Recipe'} added to ${day}.`);
  } else {
    announce('That recipe is already on that day.');
  }
}

function removeFromPlan(day, recipeId) {
  state.plan[day] = state.plan[day].filter((id) => id !== recipeId);
  savePlan();
  renderPlanner();
  announce('Recipe removed from the weekly plan.');
}

function bindMenuInteractions() {
  document.querySelectorAll('.menu-entry').forEach((entry) => {
    entry.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', entry.dataset.recipeId);
      event.dataTransfer.effectAllowed = 'copy';
      entry.classList.add('dragging');
    });
    entry.addEventListener('dragend', () => entry.classList.remove('dragging'));
  });
  document.querySelectorAll('[data-day-select]').forEach((select) => {
    select.addEventListener('change', () => {
      const button = select.parentElement.querySelector('.add-button');
      button.disabled = !select.value;
      button.dataset.day = select.value;
    });
  });
  document.querySelectorAll('[data-add-id]').forEach((button) => {
    button.addEventListener('click', () => {
      addToPlan(button.dataset.day, button.dataset.addId);
      const select = button.parentElement.querySelector('[data-day-select]');
      select.value = '';
      button.disabled = true;
      delete button.dataset.day;
    });
  });
}

function bindPlannerInteractions() {
  document.querySelectorAll('.day-slot').forEach((slot) => {
    slot.addEventListener('dragover', (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
      slot.classList.add('drag-over');
    });
    slot.addEventListener('dragleave', () => slot.classList.remove('drag-over'));
    slot.addEventListener('drop', (event) => {
      event.preventDefault();
      slot.classList.remove('drag-over');
      addToPlan(slot.dataset.day, event.dataTransfer.getData('text/plain'));
    });
  });
  document.querySelectorAll('[data-remove-day]').forEach((button) => {
    button.addEventListener('click', () => removeFromPlan(button.dataset.removeDay, button.dataset.removeId));
  });
}

function render() {
  document.querySelectorAll('.view-button').forEach((button) => {
    const active = button.dataset.view === state.view;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('.daypart').forEach((button) => {
    const active = button.dataset.slot === state.slot;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', String(active));
  });
  renderMenu();
  renderPlanner();
}

async function init() {
  const response = await fetch('data/recipes.json');
  const data = await response.json();
  state.recipes = data.recipes;
  document.querySelectorAll('.daypart').forEach((button) => {
    button.addEventListener('click', () => {
      state.slot = button.dataset.slot;
      state.query = '';
      $('#search').value = '';
      render();
    });
  });
  document.querySelectorAll('.view-button').forEach((button) => {
    button.addEventListener('click', () => {
      state.view = button.dataset.view;
      state.query = '';
      $('#search').value = '';
      render();
    });
  });
  $('#search').addEventListener('input', (event) => {
    state.query = event.target.value;
    renderMenu();
  });
  $('#clear').addEventListener('click', () => {
    $('#search').value = '';
    state.query = '';
    renderMenu();
  });
  $('#clear-plan').addEventListener('click', () => {
    state.plan = Object.fromEntries(DAYS.map(([key]) => [key, []]));
    savePlan();
    renderPlanner();
    announce('Weekly plan cleared.');
  });
  render();
}

init().catch((error) => {
  $('#menu').innerHTML = '<p>Menu data could not be loaded.</p>';
  console.error(error);
});
