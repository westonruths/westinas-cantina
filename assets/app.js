const queryParams = new URLSearchParams(location.search);
const state = {
  recipes: [],
  slot: 'dinner',
  type: queryParams.get('view') === 'all' ? 'all' : 'featured',
  query: ''
};
const labels = {
  featured: 'Featured',
  all: 'Browse all',
  protein: 'Proteins',
  veggie: 'Veggies',
  carb: 'Carbs',
  soup: 'Soups',
  sauce: 'Sauces & Extras',
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

function types() {
  const set = new Set();
  state.recipes
    .filter((recipe) => recipe.meal_slots.includes(state.slot))
    .forEach((recipe) => recipe.component_types.forEach((type) => set.add(type)));
  return ['featured', 'all', ...['protein', 'veggie', 'carb', 'soup', 'sauce', 'other'].filter((type) => set.has(type))];
}

function matches(recipe) {
  const haystack = [
    recipe.title,
    recipe.cuisine,
    ...recipe.key_ingredients,
    ...(recipe.recipe_ingredients || [])
  ].join(' ').toLowerCase();
  const slotMatches = recipe.meal_slots.includes(state.slot);
  const typeMatches = state.type === 'featured'
    ? recipe.golden
    : state.type === 'all' || recipe.component_types.includes(state.type);
  return slotMatches && typeMatches && (!state.query || haystack.includes(state.query.toLowerCase()));
}

function groupFound(found) {
  const groups = new Map();
  for (const recipe of found) {
    const key = recipe.family ? `family:${recipe.family}` : `recipe:${recipe.id}`;
    if (!groups.has(key)) groups.set(key, { family: recipe.family || null, recipes: [] });
    groups.get(key).recipes.push(recipe);
  }
  return [...groups.values()];
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

  const ingredients = (recipe.recipe_ingredients || []).map((item) => `<li>${esc(item)}</li>`).join('');
  const steps = (recipe.recipe_steps || []).map((step) => `<li>${esc(step)}</li>`).join('');
  const timings = Object.entries(recipe.recipe_timings || {})
    .map(([key, value]) => `${esc(key.replace('Time', ' time'))}: ${esc(humanTime(value))}`)
    .join(' · ');
  const metadata = recipe.recipe_yield || timings
    ? `<p class="recipe-meta">${recipe.recipe_yield ? `Yield: ${esc(recipe.recipe_yield)}` : ''}${recipe.recipe_yield && timings ? ' · ' : ''}${timings}</p>`
    : '';

  return `<div class="recipe-copy">${metadata}${ingredients ? `<h4>Ingredients</h4><ul>${ingredients}</ul>` : ''}${steps ? `<h4>Steps</h4><ol>${steps}</ol>` : ''}</div>`;
}

function variantBody(recipe) {
  return `<section class="variant-block"><h4>${esc(recipe.variant_label || recipe.title)}${recipe.golden ? ' · Golden' : ''}</h4>${recipeBody(recipe)}${sourceCredit(recipe)}</section>`;
}

function card(group) {
  const recipes = group.recipes;
  const first = recipes[0];
  const golden = recipes.some((recipe) => recipe.golden);
  const tried = recipes.some((recipe) => recipe.tried);
  const grouped = Boolean(group.family && recipes.length > 1);
  const title = grouped ? group.family : first.title;
  const cuisine = [...new Set(recipes.map((recipe) => recipe.cuisine).filter(Boolean))].join(' · ');
  const tags = [...new Set(recipes.flatMap((recipe) => recipe.component_types))]
    .map((type) => labels[type] || type)
    .join(' · ');
  const image = recipes.find((recipe) => recipe.image_url)?.image_url;
  const preview = `<summary class="card-summary">${image ? `<img class="card-image" src="${esc(image)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}<div class="card-top"><div class="badges">${golden ? '<span class="badge gold">Golden</span>' : ''}${tried ? '<span class="badge">Tried</span>' : ''}${grouped ? `<span class="badge family-badge">${recipes.length} variants</span>` : ''}</div></div><h3>${esc(title)}</h3><p class="meta">${esc(cuisine)} · ${esc(tags)}</p>${grouped ? '<p class="family-note">Recipe family; choose a canonical variant after opening.</p>' : ''}<span class="card-open-hint">Tap to open recipe${grouped ? 's' : ''} + original link</span></summary>`;
  const content = grouped
    ? `<div class="variant-list">${recipes.map(variantBody).join('')}</div>`
    : `<div class="recipe-content">${recipeBody(first)}</div>${sourceCredit(first)}`;
  return `<article class="card ${golden ? 'golden' : ''}"><details class="card-details">${preview}<div class="card-content">${content}</div></details></article>`;
}

function render() {
  const filterTypes = types();
  $('#filters').innerHTML = filterTypes
    .map((type) => `<button class="filter ${state.type === type ? 'active' : ''}" data-type="${type}">${labels[type]}</button>`)
    .join('');
  const found = state.recipes.filter(matches);
  const groups = groupFound(found);
  $('#section-title').textContent = state.query ? 'Search results' : labels[state.type];
  $('#count').textContent = `${groups.length} ${groups.length === 1 ? 'entry' : 'entries'}`;
  $('#menu').innerHTML = groups.map(card).join('');
  $('#empty').hidden = groups.length > 0;
  document.querySelectorAll('.filter').forEach((button) => {
    button.onclick = () => {
      state.type = button.dataset.type;
      state.query = '';
      $('#search').value = '';
      render();
    };
  });
}

async function init() {
  const response = await fetch('data/recipes.json');
  const data = await response.json();
  state.recipes = data.recipes;
  document.querySelectorAll('.daypart').forEach((button) => {
    button.onclick = () => {
      document.querySelectorAll('.daypart').forEach((item) => {
        item.classList.remove('active');
        item.setAttribute('aria-selected', 'false');
      });
      button.classList.add('active');
      button.setAttribute('aria-selected', 'true');
      state.slot = button.dataset.slot;
      state.type = 'featured';
      state.query = '';
      $('#search').value = '';
      render();
    };
  });
  $('#search').oninput = (event) => {
    state.query = event.target.value;
    render();
  };
  $('#clear').onclick = () => {
    $('#search').value = '';
    state.query = '';
    render();
  };
  render();
}

init().catch((error) => {
  $('#menu').innerHTML = '<p>Menu data could not be loaded.</p>';
  console.error(error);
});
