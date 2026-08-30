const DAYS = [
  ['monday', 'Monday'],
  ['tuesday', 'Tuesday'],
  ['wednesday', 'Wednesday'],
  ['thursday', 'Thursday'],
  ['friday', 'Friday'],
  ['saturday', 'Saturday'],
  ['sunday', 'Sunday']
];
const COMPONENTS = [
  ['protein', 'Protein'],
  ['carb', 'Carb'],
  ['veggie', 'Vegetable']
];
const PLAN_KEY = 'westinas-cantina-component-plan-v5';
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
  return Object.fromEntries(DAYS.map(([day]) => [day, Object.fromEntries(COMPONENTS.map(([component]) => [component, null]))]));
}

function loadPlan() {
  const blank = blankPlan();
  const used = new Set();
  try {
    const saved = JSON.parse(localStorage.getItem(PLAN_KEY) || '{}');
    for (const [day] of DAYS) {
      for (const [component] of COMPONENTS) {
        const value = saved?.[day]?.[component];
        if (typeof value === 'string' && !used.has(value)) {
          blank[day][component] = value;
          used.add(value);
        }
      }
    }
  } catch (error) {
    console.warn('Could not load the saved component calendar', error);
  }
  return blank;
}

function savePlan() {
  try {
    localStorage.setItem(PLAN_KEY, JSON.stringify(state.plan));
  } catch (error) {
    console.warn('Could not save the component calendar', error);
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

function useFirstMatches(recipe) {
  return Number(fitData(recipe).use_first_matches) || 0;
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

function ratingMarkup(recipe) {
  const rating = recipe.source_rating;
  if (!rating || !Number.isFinite(Number(rating.rating)) || !rating.rating_count) return '';
  return ` · ★ ${Number(rating.rating).toFixed(1)} (${esc(rating.rating_count)} ratings)`;
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
  return `<span class="source-credit">${status}${publisher}${ratingMarkup(recipe)}${originalLink}</span>`;
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
  if (!recipe.meal_slots.includes('dinner')) return false;
  if (!state.query) return true;
  const haystack = [recipe.title, recipe.cuisine, ...recipe.key_ingredients, ...(recipe.recipe_ingredients || [])]
    .join(' ').toLowerCase();
  return haystack.includes(state.query.toLowerCase());
}

function sortedRecipes(recipes) {
  return [...recipes].sort((a, b) => {
    const aUrgency = useFirstMatches(a);
    const bUrgency = useFirstMatches(b);
    if (aUrgency !== bUrgency) return bUrgency - aUrgency;
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
  $('#add-component').innerHTML = COMPONENTS.map(([key, label]) => `<option value="${key}">${label}</option>`).join('');
}

function openAddDialog(recipeId) {
  const recipe = state.recipes.find((item) => item.id === recipeId);
  if (!recipe) return;
  $('#add-recipe-id').value = recipe.id;
  $('#add-recipe-name').textContent = recipe.title;
  const preferred = COMPONENTS.find(([component]) => (recipe.component_types || []).includes(component));
  $('#add-component').value = preferred ? preferred[0] : 'protein';
  const dialog = $('#add-dialog');
  if (typeof dialog.showModal === 'function') dialog.showModal();
}

function openRecipeDialog(recipeId) {
  const recipe = state.recipes.find((item) => item.id === recipeId);
  if (!recipe) return;
  $('#recipe-dialog-title').textContent = recipe.title;
  $('#recipe-dialog-content').innerHTML = `${recipeBody(recipe)}${sourceCredit(recipe)}`;
  const dialog = $('#recipe-dialog');
  if (typeof dialog.showModal === 'function') dialog.showModal();
}

function menuEntry(recipe) {
  const tags = [...new Set((recipe.component_types || []).map((type) => labels[type] || type))].join(' · ');
  const badges = `${recipe.golden ? '<span class="badge gold">Golden</span>' : ''}${recipe.tried ? '<span class="badge">Tried</span>' : ''}`;
  const photo = recipe.image_url
    ? `<img class="menu-thumb" src="${esc(recipe.image_url)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
    : '';
  return `<article class="menu-entry" draggable="true" tabindex="0" data-recipe-id="${esc(recipe.id)}" aria-label="Open ${esc(recipe.title)} recipe"><div class="menu-entry-row">${photo}<div class="menu-entry-copy"><span class="drag-handle" aria-hidden="true">⋮⋮</span><div><div class="menu-entry-badges">${badges}</div><h3>${esc(recipe.title)}</h3><p class="menu-meta">${esc(recipe.cuisine || 'House recipe')}${tags ? ` · ${esc(tags)}` : ''}${ratingMarkup(recipe)}</p></div></div><div class="menu-entry-actions">${fitWidget(recipe, true)}<button class="add-button" type="button" data-add-id="${esc(recipe.id)}">Add</button></div></div><details class="recipe-details"><summary>View recipe</summary>${recipeBody(recipe)}${sourceCredit(recipe)}</details></article>`;
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
    ? 'Drag one building block into each dinner’s Protein, Carb, or Vegetable slot.'
    : 'Browse complete dishes for inspiration, then use Components / Sides when you want to assemble dinner piece by piece.';
  $('#empty').hidden = visible > 0;
  bindMenuInteractions();
}

function plannedItem(recipe, day, component) {
  const photo = recipe.image_url ? `<img class="planned-thumb" src="${esc(recipe.image_url)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : '';
  const label = COMPONENTS.find(([key]) => key === component)?.[1] || component;
  return `<div class="planned-item" draggable="true" data-plan-day="${day}" data-plan-component="${component}" data-plan-recipe="${esc(recipe.id)}">${photo}<span class="planned-title">${esc(recipe.title)}</span>${fitWidget(recipe, true)}<button type="button" data-remove-day="${day}" data-remove-component="${component}" aria-label="Remove ${esc(recipe.title)} from ${day} ${label}; another option will be suggested">×</button></div>`;
}

function renderCalendar() {
  const byId = new Map(state.recipes.map((recipe) => [recipe.id, recipe]));
  $('#week-calendar').innerHTML = DAYS.map(([day, dayLabel]) => {
    const slots = COMPONENTS.map(([component, componentLabel]) => {
      const recipe = byId.get(state.plan[day][component]);
      return `<section class="meal-slot" data-day="${day}" data-component="${component}" aria-label="${dayLabel} ${componentLabel}"><div class="meal-slot-label"><strong>${componentLabel}</strong><small>${recipe ? 'Planned' : 'Open'}</small></div><div class="meal-slot-content">${recipe ? plannedItem(recipe, day, component) : `<p class="slot-empty">Drop a ${componentLabel.toLowerCase()} here</p><button class="fill-slot" type="button" data-fill-day="${day}" data-fill-component="${component}">Suggest one</button>`}</div></section>`;
    }).join('');
    return `<article class="day-card"><div class="day-card-heading"><h3>${dayLabel}</h3><span>${day === 'saturday' || day === 'sunday' ? 'Weekend' : 'Weekday'}</span></div>${slots}</article>`;
  }).join('');
  bindCalendarInteractions();
}

function candidatePool(component, excluded = []) {
  const blocked = new Set(excluded);
  return sortedRecipes(state.recipes.filter((recipe) => {
    const types = recipe.component_types || [];
    return recipe.meal_slots.includes('dinner') && types.includes(component) && !types.includes('soup') && !isMainCourse(recipe) && !blocked.has(recipe.id);
  }));
}

function allPlannedIds(excludedSlot = null) {
  return DAYS.flatMap(([day]) => COMPONENTS.map(([component]) => {
    if (excludedSlot && day === excludedSlot[0] && component === excludedSlot[1]) return null;
    return state.plan[day][component];
  })).filter(Boolean);
}

function chooseSuggestion(day, component, extraExcluded = []) {
  const excluded = new Set([...allPlannedIds([day, component]), ...extraExcluded]);
  return candidatePool(component, [...excluded])[0] || candidatePool(component, extraExcluded)[0] || null;
}

function proposeWeek() {
  state.plan = blankPlan();
  for (const [day] of DAYS) {
    for (const [component] of COMPONENTS) {
      const recipe = chooseSuggestion(day, component);
      if (recipe) state.plan[day][component] = recipe.id;
    }
  }
  savePlan();
  renderCalendar();
  announce('A suggested protein, carb, and vegetable are ready for each dinner.');
}

function replaceSlot(day, component, removedId = null) {
  const replacement = chooseSuggestion(day, component, removedId ? [removedId] : []);
  state.plan[day][component] = replacement ? replacement.id : null;
  savePlan();
  renderCalendar();
  announce(replacement ? `Suggested replacement: ${replacement.title}.` : `No replacement was available for the ${component} slot.`);
}

function putInSlot(day, component, recipeId) {
  const recipe = state.recipes.find((item) => item.id === recipeId);
  if (!recipe || !COMPONENTS.some(([key]) => key === component) || !(recipe.component_types || []).includes(component)) {
    announce('That recipe does not belong in this component slot.');
    return;
  }
  const alreadyPlanned = DAYS.some(([otherDay]) => COMPONENTS.some(([otherComponent]) => (otherDay !== day || otherComponent !== component) && state.plan[otherDay][otherComponent] === recipe.id));
  if (alreadyPlanned) {
    announce(`${recipe.title} is already planned elsewhere this week.`);
    return;
  }
  state.plan[day][component] = recipe.id;
  savePlan();
  renderCalendar();
  announce(`${recipe.title} added to ${day} ${component}.`);
}

function movePlanItem(sourceDay, sourceComponent, destinationDay, destinationComponent) {
  if (sourceDay === destinationDay && sourceComponent === destinationComponent) return;
  const movingId = state.plan[sourceDay][sourceComponent];
  const moving = state.recipes.find((recipe) => recipe.id === movingId);
  const displacedId = state.plan[destinationDay][destinationComponent];
  const displaced = state.recipes.find((recipe) => recipe.id === displacedId);
  if (!moving || !(moving.component_types || []).includes(destinationComponent)) {
    announce('That recipe cannot move into the selected component slot.');
    return;
  }
  if (displaced && !(displaced.component_types || []).includes(sourceComponent)) {
    announce('Those two recipes cannot swap component slots.');
    return;
  }
  state.plan[destinationDay][destinationComponent] = movingId;
  state.plan[sourceDay][sourceComponent] = displacedId || null;
  savePlan();
  renderCalendar();
  announce('Dinner component moved to the new slot.');
}

function bindMenuInteractions() {
  document.querySelectorAll('.menu-entry').forEach((entry) => {
    const details = entry.querySelector('.recipe-details');
    const toggleRecipe = () => {
      details.open = !details.open;
      entry.classList.toggle('is-open', details.open);
    };
    details.addEventListener('toggle', () => entry.classList.toggle('is-open', details.open));
    entry.addEventListener('click', (event) => {
      if (event.target.closest('button, a, summary, .drag-handle')) return;
      toggleRecipe();
    });
    entry.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      if (event.target !== entry) return;
      event.preventDefault();
      toggleRecipe();
    });
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
      if (payload[0] === 'recipe') putInSlot(slot.dataset.day, slot.dataset.component, payload[1]);
      if (payload[0] === 'plan') movePlanItem(payload[1], payload[2], slot.dataset.day, slot.dataset.component);
    });
  });
  document.querySelectorAll('.planned-item').forEach((item) => {
    item.addEventListener('click', (event) => {
      if (event.target.closest('button')) return;
      openRecipeDialog(item.dataset.planRecipe);
    });
    item.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', `plan|${item.dataset.planDay}|${item.dataset.planComponent}`);
      event.dataTransfer.effectAllowed = 'move';
    });
  });
  document.querySelectorAll('[data-remove-day]').forEach((button) => {
    button.addEventListener('click', () => replaceSlot(button.dataset.removeDay, button.dataset.removeComponent, state.plan[button.dataset.removeDay][button.dataset.removeComponent]));
  });
  document.querySelectorAll('[data-fill-day]').forEach((button) => {
    button.addEventListener('click', () => replaceSlot(button.dataset.fillDay, button.dataset.fillComponent));
  });
}

function render() {
  document.querySelectorAll('.view-button').forEach((button) => {
    const active = button.dataset.view === state.view;
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
    announce('Dinner calendar cleared.');
  });
  $('#add-form').addEventListener('submit', (event) => {
    if (event.submitter?.value !== 'add') return;
    event.preventDefault();
    putInSlot($('#add-day').value, $('#add-component').value, $('#add-recipe-id').value);
    $('#add-dialog').close();
  });
  $('#close-recipe-dialog').addEventListener('click', () => $('#recipe-dialog').close());
  render();
}

init().catch((error) => {
  $('#week-calendar').innerHTML = '<p>Dinner plan could not be loaded.</p>';
  $('#menu').innerHTML = '<p>Recipe menu could not be loaded.</p>';
  console.error(error);
});
