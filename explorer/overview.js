'use strict';
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=s=>document.querySelector(s),number=n=>Number(n||0).toLocaleString(),pretty=x=>esc(JSON.stringify(x,null,2));
const url=value=>{try{const u=new URL(value);return /^https?:$/.test(u.protocol)?esc(u.href):''}catch{return ''}};
const languageNames={en:'English',zh:'Chinese',de:'German',fr:'French',pt:'Portuguese',es:'Spanish',ru:'Russian',ar:'Arabic',ja:'Japanese',pl:'Polish',uk:'Ukrainian'};
let overview,inventory,profiles,recipes;
const lang=values=>values.map(l=>esc(languageNames[l]||l)).join(', ')||'Not recorded';
const list=values=>`<ul>${values.map(v=>`<li>${esc(v)}</li>`).join('')}</ul>`;
function lengths(value){return value?`${number(value.median)} / ${number(value.p95)} <small>(n=${number(value.n)})</small>`:'Not present / not measured'}
function template(task,country){
  const r=recipes[task.id];
  if(['domain_text','press_conference'].includes(task.id))return {format_status:'Illustrative text-training representation; not an exported training row',text:'<cleaned and correctly attributed record.text>',metadata:{country:country.code,event_group:'<group_id>',task:task.id}};
  if(['policy_evidence','policy_evidence_document','policy_positions','human_rights_evidence','unverified_speech_segment'].includes(task.id))return {format_status:'Evidence record; no complete supervised target supplied',context_fields:r.input,missing_target:r.target,next_step:r.possible_use};
  return {format_status:'Illustrative field mapping, not a ready training row',prompt:[{role:'system',content:`Represent the specified institutional role for ${country.name} at the record date. Preserve attribution and uncertainty.`},{role:'user',content:r.input.map(v=>`<${v}>`).join('\n')}],completion:[{role:'assistant',content:r.target.map(v=>`<${v}>`).join('\n')}],metadata:{record_id:task.sample.id,source_task:task.id,review_status:task.sample.review_status}};
}
function traceHTML(task,country){
 const recipe=recipes[task.id];
 if(!recipe)throw Error(`Missing trace definition: ${task.id}`);
 const sample=task.sample;
 return `<article class="trace"><header><h3>${esc(recipe.label)}</h3><span class="tag">${number(task.count)} records</span></header><p>${esc(recipe.availability)}</p>
 <div class="fields"><div class="field"><strong>Prompt / context — supplied at inference</strong>${list(recipe.input)}</div><div class="field output"><strong>Output / target — generated at inference</strong>${list(recipe.target)}</div><div class="field review"><strong>Scoring / environment</strong><p>${esc(recipe.scoring)}</p></div></div>
 <p>${esc(recipe.inference)}</p><p><strong>Possible training use:</strong> ${esc(recipe.possible_use)}</p>
 <details><summary>Trace template and an actual source-record reference</summary><p class="note">Templates describe how the available fields could be used. Placeholders are not completed training data; source text is not replaced by an invented answer.</p><pre>${pretty(template(task,country))}</pre><p><strong>Actual record:</strong> ${esc(sample.title||sample.id)} · ${esc(sample.date||'date not recorded')}</p><p><a href="advanced.html#view=explore&id=${encodeURIComponent(sample.uid)}">Inspect this record</a>${url(sample.source_url)?` · <a href="${url(sample.source_url)}" target="_blank" rel="noopener">Publisher / dataset</a>`:''}</p><pre>${pretty(sample)}</pre></details></article>`;
}
function sourceHTML(source,country){
 const profile=profiles[source.id];
 return `<details class="source" id="source-${esc(source.id)}"><summary><div><span class="name">${esc(profile.name)}</span><span class="sub">${source.tasks.map(t=>`${number(t.count)} ${esc(recipes[t.id]?.label||t.id).toLowerCase()}`).join(' · ')}</span></div><span class="count">${number(source.count)}</span></summary>
 <div class="source-body"><p>${esc(profile.description)}</p><div class="source-meta"><span><strong>Languages:</strong> ${lang(source.languages)}</span><span><strong>Recorded dates:</strong> ${esc(source.date_range.join(' → ')||'Not recorded')}</span><span><strong>Source IDs:</strong> ${esc(source.source_ids.join(', '))}</span></div>
 ${source.missing_values?`<p class="note">${number(source.missing_values)} missing-value cells are included in this source count.</p>`:''}
 <div class="scroll"><table><thead><tr><th>Stored record / trace type</th><th>Count</th><th>Input chars<br>median / p95</th><th>Target chars<br>median / p95</th><th>Body chars<br>median / p95</th></tr></thead><tbody>${source.tasks.map(t=>`<tr><td>${esc(recipes[t.id]?.label||t.id)}</td><td class="num">${number(t.count)}</td><td>${lengths(t.lengths.input)}</td><td>${lengths(t.lengths.target)}</td><td>${lengths(t.lengths.body)}</td></tr>`).join('')}</tbody></table></div>
 <p class="note">Character lengths of stored fields, before adding role/date instructions and the chat template. n counts populated fields; document bodies are not automatically training targets. Token lengths are not measured in this inventory.</p>
 ${source.tasks.map(t=>traceHTML(t,country)).join('')}</div></details>`;
}
const simpleQuestions={
 CHN:"Under China’s 2021 development-cooperation white paper, should aid require the recipient country to change its political system?",
 DEU:"Under Germany’s 2023 China Strategy, should Germany depend on one Chinese supplier for all critical energy-transition inputs?",
 FRA:"Does France’s 2025 strategic review support stronger European defence within NATO?",
 GBR:"What is the UK’s 2035 emissions target, including its baseline and exclusions?",
 IND:"What protections for small-scale fishers does India’s 2020 WTO report seek when discussing fisheries-subsidy rules?",
 BRA:"What did Brazil’s 2022 WTO report say about its own use of special treatment and flexibility for other developing members?"
};
function workedExample(country){
 const e=country.examples[0];
 return `<article class="method"><h3>Evidence-conditioned answer · worked candidate</h3><p class="note">Uses existing project-curated policy evidence. The question below is a clearer illustrative rewrite; the stored original example is unchanged and remains unadmitted.</p>
 <div class="fields"><div class="field"><strong>Prompt / context</strong><p>${esc(country.name)} · policy date ${esc(e.date)}</p>${e.evidence.map(v=>`<p>${esc(v.claim)}</p>`).join('')}<p class="example-question">${esc(simpleQuestions[country.code])}</p></div><div class="field output"><strong>Candidate answer / SFT target</strong><p>${esc(e.answer)}</p></div><div class="field review"><strong>Inspect / score</strong>${list(e.rubric)}<p>Human/source review required. No RLVR verifier is supplied.</p></div></div>
 <p class="note">Blue fields are input context; green is the candidate output; review criteria stay outside the prompt. The existing SFT implementation uses completion-only loss and Qwen3 with thinking disabled.</p>
 <p>${e.evidence.map(v=>`<a href="${url(v.source_url)}" target="_blank" rel="noopener">${esc(v.id)} ↗</a>`).join(' · ')}</p>
 <details><summary>Stored original candidate and provenance</summary><p class="note">${esc(e.format_origin)}. ${overview.private?'Full stored format.':'Source passages are explicitly omitted from this public format preview.'}</p><pre>${pretty(e.format)}</pre><pre>${pretty(e.metadata)}</pre></details></article>`;
}
function render(code){
 const country=overview.countries.find(c=>c.code===code)||overview.countries[0],data=inventory.countries[country.code];
 document.title=`${country.name} · Data explorer for persona fine-tuning`;
 $('#countries').innerHTML=overview.countries.map(c=>`<button type="button" data-country="${esc(c.code)}" aria-pressed="${c.code===country.code}" aria-label="${esc(c.name)}, ${number(inventory.countries[c.code].count)} evidence record IDs">${esc(c.name)} <span class="count">${number(inventory.countries[c.code].count)}</span></button>`).join('');
 $('#countries').querySelectorAll('button').forEach(b=>b.onclick=()=>{location.hash=`country=${b.dataset.country}`});
 const kinds=[...overview.kinds,{id:'country_statistics',label:'Country statistics'},{id:'evaluation',label:'Evaluation records / views'}];
 $('#country-panel').innerHTML=`<section class="catalog-summary"><div class="country-title"><h1>${esc(country.name)}</h1><span class="count">${number(data.count)} evidence records</span></div>
 <div class="breakdown">${kinds.map(k=>`<div class="metric"><span>${esc(k.label)}</span><b>${number(country.counts[k.id])}</b></div>`).join('')}</div>
 <p class="note">The breakdown includes overlapping representations; do not sum it. The country badge excludes training-format copies, review/lineage and evaluation wrappers. ${number(data.sources.length)} source collections are listed below.</p></section>
 <section class="source-section"><h2>Data sources</h2><p class="note">Sorted by source name. Expand a source for trace types, measured lengths, field mappings, actual record references and training options.</p>
 ${data.sources.map(s=>sourceHTML(s,country)).join('')}</section>
 <section class="methods"><h2>Post-training examples using the available data</h2>
 <div class="method"><h3>Choose the task from the source fields</h3><div class="scroll"><table><thead><tr><th>Available data</th><th>Possible trace</th><th>What is still needed</th></tr></thead><tbody>${data.sources.map(s=>`<tr><td>${esc(profiles[s.id].name)}<br><small>${number(s.count)} record IDs</small></td><td>${s.tasks.map(t=>esc(recipes[t.id].label)).join('<br>')}</td><td>${s.tasks.map(t=>esc(recipes[t.id].availability)).join('<br>')}</td></tr>`).join('')}</tbody></table></div></div>
 ${workedExample(country)}
 <p class="refs">Implementation references: <a href="https://huggingface.co/docs/trl/sft_trainer#expected-dataset-type-and-format">TRL conversational SFT formats</a> · <a href="https://huggingface.co/docs/peft/conceptual_guides/lora">PEFT LoRA</a> · <a href="https://huggingface.co/Qwen/Qwen3-8B">Qwen3 mode</a>. Research motivation: <a href="https://arxiv.org/abs/2403.10131">RAFT</a> for evidence-conditioned adaptation; <a href="https://aclanthology.org/2020.acl-main.442/">CheckList</a> for behavioral evaluation. These are options to test, not claims of completed RL/SFT environments.</p></section>`;
}
function route(){
 const hash=new URLSearchParams(location.hash.slice(1));
 if(hash.has('id')||hash.has('kind')||hash.get('view')==='files'){location.replace(`advanced.html${location.hash}`);return}
 const country=overview.countries.find(c=>c.code===hash.get('country'))||overview.countries[0];
 history.replaceState(null,'',`#country=${country.code}`);render(country.code);
}
async function start(){try{
 const load=async path=>{const r=await fetch(path);if(!r.ok)throw Error(`Unable to load ${path} (${r.status}).`);return r.json()};
 [overview,inventory,profiles,recipes]=await Promise.all(['overview.json','sources.json','source_profiles.json','trace_types.json'].map(load));
 if(overview.private){$('#research-link').textContent='Original research archive';$('#research-link').href='https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/resolve/main/research.tar.gz?download=true'}
 window.addEventListener('hashchange',route);route();
 }catch(error){$('#country-panel').innerHTML=`<p class="error">${esc(error.message)} <a href="https://github.com/memo-ozdincer/country-persona-data">Browse the repository.</a></p>`}}
start();
