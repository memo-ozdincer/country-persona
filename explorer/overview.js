'use strict';
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $ = selector => document.querySelector(selector);
const pretty = value => esc(JSON.stringify(value, null, 2));
const number = value => Number(value || 0).toLocaleString();
const url = value => { try { const u = new URL(value); return /^https?:$/.test(u.protocol) ? esc(u.href) : ''; } catch { return ''; } };
const languageNames = {en:'English',zh:'Chinese',de:'German',fr:'French',pt:'Portuguese',es:'Spanish',ru:'Russian',ar:'Arabic',ja:'Japanese',pl:'Polish',uk:'Ukrainian'};
let overview;
function sourceLinks(example) {
  return example.evidence.map(e => `<a href="${url(e.source_url)}" target="_blank" rel="noopener">${esc(e.id)} ↗</a>`).join(' · ');
}
function render(code) {
  const country = overview.countries.find(c => c.code === code) || overview.countries[0];
  const example = country.examples[0];
  document.title = `${country.name} · Country Persona data`;
  $('#countries').innerHTML = overview.countries.map(c => `<button type="button" data-country="${esc(c.code)}" aria-pressed="${c.code === country.code}">${esc(c.name)}</button>`).join('');
  $('#countries').querySelectorAll('button').forEach(button => button.onclick = () => { location.hash = `country=${button.dataset.country}`; });
  const countRows = overview.kinds.map(k => `<tr><td>${esc(k.label)}</td><td>${number(country.counts[k.id])}</td></tr>`).join('');
  const evidence = example.evidence.map(e => `<p class="source-claim">${esc(e.claim)}</p>`).join('');
  const more = country.examples.slice(1).map(e => `<article><h3>${esc(e.question)}</h3><p class="muted">${esc(e.date)} · Authored target</p><p>${esc(e.answer)}</p><p class="evidence-links">${sourceLinks(e)}</p></article>`).join('');
  const privateNote = overview.private ? 'Full prompt and completion from the research record. See the format origin below.' : 'Public preview: source passages are omitted in the JSON; the claims below are authored paraphrases. Target answers are shown in full. The owner view contains the full source text.';
  $('#country-panel').innerHTML = `
    <div class="country-heading"><h2>${esc(country.name)}</h2><span class="status">Shown examples: review pending · not admitted</span></div>
    <div class="country-grid">
      <aside class="counts"><table><caption>Available records by type</caption><tbody>${countRows}</tbody></table>
        <p>Counts use distinct record IDs within each type. Rows overlap; they are <strong>not a total of independent training traces</strong>. No multi-agent trajectories have been collected.</p>
        <p><strong>Source languages:</strong> ${country.languages.map(l => esc(languageNames[l] || l)).join(', ')}. These examples use English answers; source coverage is uneven.</p>
        <details><summary>What is counted, and how it is used</summary><p>${esc(overview.count_method)}</p>${overview.kinds.map(k => `<p><strong>${esc(k.label)}.</strong> ${esc(k.use)}</p>`).join('')}</details>
      </aside>
      <article class="example"><span class="eyebrow">Characteristic policy application</span><p class="date">Policy date ${esc(example.date)} · Source language: ${esc(languageNames[example.language] || example.language)}</p>
        <h3>${esc(example.question)}</h3><div class="label">Authored target answer · not a model output</div><p class="answer">${esc(example.answer)}</p>
        <p class="evidence-links">${sourceLinks(example)}</p>
        <div class="inspect"><strong>What to inspect in a model’s answer</strong><ul>${example.rubric.map(r => `<li>${esc(r)}</li>`).join('')}</ul></div>
      </article>
    </div>
    ${more ? `<details><summary>${country.examples.length - 1} more authored example${country.examples.length > 2 ? 's' : ''} for ${esc(country.name)}</summary>${more}</details>` : ''}
    <section class="format" aria-labelledby="format-title"><div class="format-header"><div><span class="eyebrow">The same example, as training data</span><h2 id="format-title">What goes into the recipe</h2></div><a href="#" id="download">Download ${overview.private ? 'record format' : 'redacted format preview'} ↓</a></div>
      <p class="format-note">${esc(privateNote)}</p>
      <div class="format-grid">
        <div class="part"><h3>01 · prompt → system + user context</h3><small>Model input · no supervised loss on these tokens</small><p class="system">${esc(example.system)}</p><pre>${esc(example.context)}</pre><p><strong>Question:</strong> ${esc(example.question)}</p></div>
        <div class="part"><h3>02 · prompt → user evidence</h3><small>Context supplied to the model · no supervised loss here</small>${evidence}<p class="note">Authored summaries shown here. The stored user message supplies the cited source passages. Evidence is context, not a separate target.</p></div>
        <div class="part target"><h3>03 · completion → assistant answer</h3><small>Supervised target · completion_only_loss=True</small><p>${esc(example.answer)}</p><p class="note">One assistant completion. The trainer applies Qwen3’s chat template with enable_thinking=False; it also verifies the prompt boundary and sequence length.</p></div>
        <div class="part metadata"><h3>04 · review metadata → selection & evaluation</h3><small>Kept beside the training row · not appended as a model message</small><pre>${pretty(example.metadata)}</pre><p class="note">Review status gates selection. Source hashes and spans support verification; event groups keep related records together when splitting. The inspection rubric scores answers separately.</p></div>
      </div>
      <details><summary>Inspect the actual JSON fields and source spans</summary><p class="note">${esc(example.format_origin)}. ${overview.private ? '' : 'This downloadable public version is redacted and is not a train-ready row.'}</p><pre>${pretty(example.format)}</pre><h3>Source provenance (sidecar)</h3><pre>${pretty(example.evidence)}</pre></details>
    </section>`;
  $('#download').onclick = e => {
    e.preventDefault();
    const blob = new Blob([JSON.stringify(example.format, null, 2) + '\n'], {type:'application/json'});
    const href = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = href; a.download = `${example.id}${overview.private ? '' : '-REDACTED-PREVIEW'}.json`;
    a.click(); setTimeout(() => URL.revokeObjectURL(href), 1000);
  };
}
function route() {
  const hash = new URLSearchParams(location.hash.slice(1));
  // Old comparison links must never select the Ukraine subset on the landing page.
  // Preserve specific record/filter links in the secondary catalog.
  if (hash.has('id') || hash.has('kind') || hash.get('view') === 'files') {
    location.replace(`advanced.html${location.hash}`); return;
  }
  const country = overview.countries.find(c => c.code === hash.get('country')) || overview.countries[0];
  history.replaceState(null, '', `#country=${country.code}`);
  render(country.code);
}
async function start() {
  try {
    const response = await fetch('overview.json');
    if (!response.ok) throw new Error(`Overview could not be loaded (${response.status}).`);
    overview = await response.json();
    $('#collection').innerHTML = `<strong>${overview.totals.policy_applications}</strong> authored policy applications · <strong>${overview.totals.policy_positions}</strong> curated policy positions · <strong>${overview.totals.decision_events}</strong> linked decision events <span class="muted">(${overview.totals.decision_cases} country views)</span> · broader source counts below`;
    if (overview.private) { $('#research-link').textContent = 'Download original research archive ↗'; $('#research-link').href = 'https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/resolve/main/research.tar.gz?download=true'; }
    window.addEventListener('hashchange', route); route();
  } catch (error) {
    $('#collection').textContent = 'Unable to load the overview.';
    $('#country-panel').innerHTML = `<p class="error">${esc(error.message)} <a href="https://github.com/memo-ozdincer/country-persona-data">Read the country pages on GitHub.</a></p>`;
  }
}
start();
