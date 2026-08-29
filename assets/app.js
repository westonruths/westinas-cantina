const DAYS = [
  ['monday', 'Monday'],
  ['tuesday', 'Tuesday'],
  ['wednesday', 'Wednesday'],
  ['thursday', 'Thursday'],
  ['friday', 'Friday'],
  ['saturday', 'Saturday'],
  ['sunday', 'Sunday']
];
const MEALS = [
  ['breakfast', 'Breakfast'],
  ['lunch', 'Lunch'],
  ['dinner', 'Dinner']
];
const PLAN_KEY = 'westinas-cantina-calendar-plan-v3';
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

function blankPlan() {
  return Object.fromEntries(DAYS.map(([day]) => [day, Object.fromEntries(MEALS.map(([meal]) => [meal, null]))]));
}

function loadPlan() {
  const blank = blankPlan();
  try {
    const saved = JSON.parse(localStorage.getItem(PLAN_KEY) || '{}');
    for (const [day] of DAYS) {
      for (const [meal] of MEALS) {
        const value = saved?.[day]?.[meal];
        if (typeof value === 'string') blank[day][meal] = value;
      }
    }
  } catch (error) {
    console.warn('Could not load the saved calendar plan', error);
  }
  return blank;
}

function savePlan() {
  try {
    localStorage.setItem(PLAN_KEY, JSON.stringify(state.plan));
  } catch (error) {
    console.warn('Could not save the calendar plan', error);
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
  return `<span class="${classes}" title="${esc(label)}" aria-label="${esc(label)}"><span class="fit-ring" style="${style}"><span>${display}</span></span><span class="fit-copy"><strong>${compact ? 'Fit' : 'On hand'}</strong><small>${percent === null ? 'No public ingredient list' : `${fit.matched} / ${fit.total}`}</small></span></span>`;
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
  if (types.includes('soup') || !types.includes('protein')) return false;
  if (types.includes('carb')) return true;
  return /pasta|noodle|rice|stew|congee|dumpling|gyros|khao|pierogi|couscous/i.test(recipe.title);
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
  if (isMainCourse(recipe)) return null;
  if (types.includes('soup')) return 'soups';
  if (types.includes('protein')) return 'proteins';
  if (types.includes('veggie')) return 'vegetables';
  if (types.includes('carb')) return 'carbs';
  return 'extras';
}

function menuSections() {
  if (state.view === 'components') {
    return [
      ['proteins', 'Proteins', 'Standalone proteins to anchor a meal.'],
      ['vegetables', 'Vegetables & salads', 'Fresh, cooked, and composed vegetable sides.'],
      ['carbs', 'Carbs & grains', 'Rice, noodles, pasta, potatoes, and breads.'],
      ['soups', 'Soups', 'Complete bowls for lighter or one-dish meals.'],
      ['extras', 'Sauces & extras', 'Finishing sauces, toppings, dips, and other additions.']
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
  const haystack = [recipe.title, recipe.cuisine, ...recipe.key_ingredients, ...(recipe.recipe_ingredients || [])]
    .join(' ').toLowerCase();
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

function addDialogOptions() {
  $('#add-day').innerHTML = DAYS.map(([key, label]) => `<option value="${key}">${label}</option>`).join('');
}

function openAddDialog(recipeId) {
  const recipe = state.recipes.find((item) => item.id === recipeId);
  if (!recipe) return;
  $('#add-recipe-id').value = recipe.id;
  $('#add-recipe-name').textContent = recipe.title;
  $('#add-meal').value = recipe.meal_slots.includes(state.slot) ? state.slot : 'dinner';
  const dialog = $('#add-dialog');
  if (typeof dialog.showModal === 'function') dialog.showModal();
}

function menuEntry(recipe) {
  const tags = [...new Set((recipe.component_types || []).map((type) => labels[type] || type))].join(' · ');
  const badges = `${recipe.golden ? '<span class="badge gold">Golden</span>' : ''}${recipe.tried ? '<span class="badge">Tried</span>' : ''}`;
  return `<article class="menu-entry" draggable="true" data-recipe-id="${esc(recipe.id)}"><div class="menu-entry-row"><div class="menu-entry-copy"><span class="drag-handle" aria-hidden="true">⋮⋮</span><div><div class="menu-entry-badges">${badges}</div><h3>${esc(recipe.title)}</h3><p class="menu-meta">${esc(recipe.cuisine || 'House recipe')}${tags ? ` · ${esc(tags)}` : ''}</p></div></div><div class="menu-entry-actions">${fitWidget(recipe, true)}<button class="add-button" type="button" data-add-id="${esc(recipe.id)}">Add</button></div></div><details class="recipe-details"><summary>View recipe</summary>${recipeBody(recipe)}${sourceCredit(recipe)}</details></article>`;
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
  $('#menu-note').textContent = state.view === 'components'
    ? 'Standalone building blocks for adding a protein, vegetable, carb, soup, or finishing extra to the week.'
    : 'Complete plates first, then proteins, soups, small plates, and sides—organized like a restaurant menu.';
  $('#empty').hidden = visible > 0;
  bindMenuInteractions();
}

function plannedItem(recipe, day, meal) {
  return `<div class="planned-item" draggable="true" data-plan-day="${day}" data-plan-meal="${meal}"><span class="planned-title">${esc(recipe.title)}</span>${fitWidget(recipe, true)}<button type="button" data-remove-day="${day}" data-remove-meal="${meal}" aria-label="Remove ${esc(recipe.title)} from ${day} ${meal}; another option will be suggested">×</button></div>`;
}

function renderCalendar() {
  const byId = new Map(state.recipes.map((recipe) => [recipe.id, recipe]));
  $('#week-calendar').innerHTML = DAYS.map(([day, dayLabel]) => {
    const slots = MEALS.map(([meal, mealLabel]) => {
      const recipe = byId.get(state.plan[day][meal]);
      return `<section class="meal-slot" data-day="${day}" data-meal="${meal}" aria-label="${dayLabel} ${mealLabel}"><div class="meal-slot-label"><strong>${mealLabel}</strong><small>${recipe ? 'Suggested' : 'Open'}</small></div><div class="meal-slot-content">${recipe ? plannedItem(recipe, day, meal) : `<p class="slot-empty">Drop a recipe here</p><button class="fill-slot" type="button" data-fill-day="${day}" data-fill-meal="${meal}">Suggest one</button>`}</div></section>`;
    }).join('');
    return `<article class="day-card"><div class="day-card-heading"><h3>${dayLabel}</h3><span>${day === 'saturday' || day === 'sunday' ? 'Weekend' : 'Weekday'}</span></div>${slots}</article>`;
  }).join('');
  bindCalendarInteractions();
}

function candidatePool(meal, excluded = []) {
  const blocked = new Set(excluded);
  return sortedRecipes(state.recipes.filter((recipe) => recipe.meal_slots.includes(meal) && !blocked.has(recipe.id)));
}

function allPlannedIds() {
  return DAYS.flatMap(([day]) => MEALS.map(([meal]) => state.plan[day][meal])).filter(Boolean);
}

function chooseSuggestion(day, meal, extraExcluded = []) {
  const excluded = [...allPlannedIds(), ...extraExcluded];
  const pool = candidatePool(meal, excluded);
  if (pool.length) return pool[0];
  return candidatePool(meal, extraExcluded)[0] || null;
}

function proposeWeek() {
  state.plan = blankPlan();
  for (const [day] of DAYS) {
    for (const [meal] of MEALS) {
      const shouldSuggest = meal === 'breakfast' || meal === 'dinner' || (meal === 'lunch' && (day === 'saturday' || day === 'sunday'));
      if (shouldSuggest) {
        const recipe = chooseSuggestion(day, meal);
        if (recipe) state.plan[day][meal] = recipe.id;
      }
    }
  }
  savePlan();
  renderCalendar();
  announce('A suggested week is ready. Drag recipes between slots to edit it.');
}

function replaceSlot(day, meal, removedId = null) {
  const replacement = chooseSuggestion(day, meal, removedId ? [removedId] : []);
  state.plan[day][meal] = replacement ? replacement.id : null;
  savePlan();
  renderCalendar();
  announce(replacement ? `Suggested replacement: ${replacement.title}.` : 'No replacement was available for that meal.');
}

function putInSlot(day, meal, recipeId) {
  const recipe = state.recipes.find((item) => item.id === recipeId);
  if (!recipe) return;
  state.plan[day][meal] = recipe.id;
  savePlan();
  renderCalendar();
  announce(`${recipe.title} added to ${day} ${meal}.`);
}

function movePlanItem(sourceDay, sourceMeal, destinationDay, destinationMeal) {
  if (sourceDay === destinationDay && sourceMeal === destinationMeal) return;
  const moving = state.plan[sourceDay][sourceMeal];
  const displaced = state.plan[destinationDay][destinationMeal];
  state.plan[destinationDay][destinationMeal] = moving;
  state.plan[sourceDay][sourceMeal] = displaced || null;
  savePlan();
  renderCalendar();
  announce('Meal moved to the new calendar slot.');
}

function bindMenuInteractions() {
  document.querySelectorAll('.menu-entry').forEach((entry) => {
    entry.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', `recipe|${entry.dataset.recipeId}`);
      event.dataTransfer.effectAllowed = 'copy';
      entry.classList.add('dragging');
    });
    entry.addEventListener('dragend', () => entry.classList.remove('dragging'));
  });
  document.querySelectorAll('[data-add-id]').forEach((button) => {
    button.addEventListener('click', () => openAddDialog(button.dataset.addId));
  });
}

function bindCalendarInteractions() {
  document.querySelectorAll('.meal-slot').forEach((slot) => {
    slot.addEventListener('dragover', (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
      slot.classList.add('drag-over');
    });
    slot.addEventListener('dragleave', () => slot.classList.remove('drag-over'));
    slot.addEventListener('drop', (event) => {
      event.preventDefault();
      slot.classList.remove('drag-over');
      const payload = event.dataTransfer.getData('text/plain').split('|');
      if (payload[0] === 'recipe') putInSlot(slot.dataset.day, slot.dataset.meal, payload[1]);
      if (payload[0] === 'plan') movePlanItem(payload[1], payload[2], slot.dataset.day, slot.dataset.meal);
    });
  });
  document.querySelectorAll('.planned-item').forEach((item) => {
    item.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', `plan|${item.dataset.planDay}|${item.dataset.planMeal}`);
      event.dataTransfer.effectAllowed = 'move';
    });
  });
  document.querySelectorAll('[data-remove-day]').forEach((button) => {
    button.addEventListener('click', () => replaceSlot(button.dataset.removeDay, button.dataset.removeMeal, state.plan[button.dataset.removeDay][button.dataset.removeMeal]));
  });
  document.querySelectorAll('[data-fill-day]').forEach((button) => {
    button.addEventListener('click', () => replaceSlot(button.dataset.fillDay, button.dataset.fillMeal));
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
  renderCalendar();
  renderMenu();
}

async function init() {
  addDialogOptions();
  const response = await fetch('data/recipes.json');
  const data = await response.json();
  state.recipes = data.recipes;
  const saved = localStorage.getItem(PLAN_KEY);
  if (!saved) proposeWeek();
  document.querySelectorAll('.daypart').forEach((button) => {
    button.addEventListener('click', () => {
      state.slot = button.dataset.slot;
      state.query = '';
      $('#search').value = '';
      renderMenu();
    });
  });
  document.querySelectorAll('.view-button').forEach((button) => {
    button.addEventListener('click', () => {
      state.view = button.dataset.view;
      state.query = '';
      $('#search').value = '';
      renderMenu();
    });
  });
  $('#search').addEventListener('input', (event) => {
    state.query = event.target.value;
    renderMenu();
  });
  $('#clear-search').addEventListener('click', () => {
    $('#search').value = '';
    state.query = '';
    renderMenu();
  });
  $('#propose-week').addEventListener('click', proposeWeek);
  $('#clear-plan').addEventListener('click', () => {
    state.plan = blankPlan();
    savePlan();
    renderCalendar();
    announce('Calendar cleared.');
  });
  $('#add-form').addEventListener('submit', (event) => {
    if (event.submitter?.value !== 'add') return;
    event.preventDefault();
    putInSlot($('#add-day').value, $('#add-meal').value, $('#add-recipe-id').value);
    $('#add-dialog').close();
  });
  render();
}

init().catch((error) => {
  $('#week-calendar').innerHTML = '<p>Meal plan could not be loaded.</p>';
  $('#menu').innerHTML = '<p>Recipe menu could not be loaded.</p>';
  console.error(error);
});
