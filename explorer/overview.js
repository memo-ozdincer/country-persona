'use strict';
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=s=>document.querySelector(s),number=n=>Number(n||0).toLocaleString(),pretty=x=>esc(JSON.stringify(x,null,2));
const url=value=>{try{const u=new URL(value);return /^https?:$/.test(u.protocol)?esc(u.href):''}catch{return ''}};
const languageNames={en:'English',zh:'Chinese',de:'German',fr:'French',pt:'Portuguese',es:'Spanish',ru:'Russian',ar:'Arabic',ja:'Japanese',pl:'Polish',uk:'Ukrainian'};
let overview,inventory,profiles,recipes,decisionShowcase,trainingExamples;
const lang=values=>values.map(l=>esc(languageNames[l]||l)).join(', ')||'Not recorded';
const list=values=>`<ul>${values.map(v=>`<li>${esc(v)}</li>`).join('')}</ul>`;
function lengths(value){return value?`${number(value.median)} / ${number(value.p95)} <small>(n=${number(value.n)})</small>`:'Not present / not measured'}
function paperHTML(ids){return ids.map(id=>{const p=trainingExamples.papers[id];return `<li><a href="${url(p.url)}" target="_blank" rel="noopener">${esc(p.name)}</a> — ${esc(p.why)}</li>`}).join('')}
function block(label,value,kind='input'){return `<section class="training-block ${kind}"><h5>${esc(label)}</h5><pre>${esc(typeof value==='string'?value:JSON.stringify(value,null,2))}</pre></section>`}
function exampleHTML(e,i){
 const f=e.format;
 const content=f.chosen?block('1. Complete prompt (system + evidence + question)',f.prompt)+block('2. Chosen completion',f.chosen,'target')+block('3. Rejected completion',f.rejected,'rejected'):
 f.text?block('Complete training text',f.text,'target'):
 block('1. System instruction',e.system)+block('2. Context / evidence supplied to the model',e.context||'No additional context in this example.')+block('3. User question / task',e.question)+block('4. Assistant completion — supervised target',e.completion,'target');
 return `<details class="training-example"><summary><span class="example-number">${i+1}</span><span>${esc(e.title)}<small>${esc(e.objective)} · ${esc(e.origin)}</small></span></summary><div class="training-example-body">${e.teacher_prompt?block('Teacher-only prompt used to produce the target (not student input)',e.teacher_prompt):''}${content}<p class="loss-note"><strong>Training objective:</strong> ${esc(e.loss||(f.chosen?'DPO compares chosen and rejected completions under the same prompt; neither answer is supplied as prompt context.':'Completion-only supervision.'))}</p>${list(e.notes||[])}<h5>Research connection</h5><ul class="paper-list">${paperHTML(e.papers||[])}</ul><details><summary>Complete machine-readable training example</summary><pre>${pretty(f)}</pre><button type="button" class="download-example" data-example="${esc(JSON.stringify(f))}">Download example JSON</button></details>${e.provenance?`<details><summary>Provenance and review status</summary><pre>${pretty(e.provenance)}</pre></details>`:''}</div></details>`;
}
function traceHTML(task,country,sourceId){
 const recipe=recipes[task.id],entry=trainingExamples.countries[country.code][sourceId].tasks[task.id],sample=entry.pointer;
 return `<article class="trace"><header><h3>${esc(recipe.label)}</h3><span class="tag">${number(task.count)} records</span></header><p>${esc(recipe.availability)}</p>
 <div class="fields"><div class="field"><strong>Available model inputs</strong>${list(recipe.input)}</div><div class="field output"><strong>Target to learn</strong>${list(recipe.target)}</div><div class="field review"><strong>How to evaluate</strong><p>${esc(recipe.scoring)}</p></div></div>
 <p><strong>Recommended use:</strong> ${esc(recipe.possible_use)}</p><p class="note">${number(entry.recorded_groups)} recorded groups in this task; ${number(entry.missing_inputs)} records lack stored question/context/messages. Group IDs do not necessarily identify independent events.</p>
 <details class="stored-record"><summary>What an actual record looks like: ${esc(sample.id)}</summary><p>${esc(sample.title||sample.id)} · ${esc(sample.date||'Date not recorded')} · ${esc(sample.file)}:${sample.line}</p><p>${trainingExamples.visibility==='owner-only'?'Complete original stored JSON, including its full text. No display truncation.':'Public metadata projection. Original source bodies remain in the owner-only research explorer.'}</p><pre>${pretty(entry.record)}</pre><a href="advanced.html#view=explore&id=${encodeURIComponent(sample.uid)}">Open catalog record</a>${url(sample.source_url)?` · <a href="${url(sample.source_url)}" target="_blank" rel="noopener">Original publisher ↗</a>`:''}</details>
 <h4>Complete worked examples</h4>${entry.examples.map(exampleHTML).join('')}</article>`;
}
function sourceTrainingHTML(source,country){
 const card=trainingExamples.countries[country.code][source.id];
 const more=[...card.policy_examples,...card.preference_examples];
 return `${more.length?`<section class="policy-training"><h3>Apply this source’s policy: additional training strategies</h3><p class="note">Complete source-linked examples. Authored targets and controlled errors are labeled explicitly; no candidate is newly admitted to training.</p>${more.map(exampleHTML).join('')}</section>`:''}`;
}
function sourceHTML(source,country){
 const profile=profiles[source.id];
 return `<details class="source" id="source-${esc(source.id)}"><summary><div><span class="name">${esc(profile.name)}</span><span class="sub">${source.tasks.map(t=>`${number(t.count)} ${esc(recipes[t.id]?.label||t.id).toLowerCase()}`).join(' · ')}</span></div><span class="count">${number(source.count)}</span></summary>
 <div class="source-body"><p>${esc(profile.description)}</p><div class="source-meta"><span><strong>Languages:</strong> ${lang(source.languages)}</span><span><strong>Recorded dates:</strong> ${esc(source.date_range.join(' → ')||'Not recorded')}</span><span><strong>Source IDs:</strong> ${esc(source.source_ids.join(', '))}</span></div>
 ${source.missing_values?`<p class="note">${number(source.missing_values)} missing-value cells are included in this source count.</p>`:''}
 <div class="scroll"><table><thead><tr><th>Stored record / trace type</th><th>Count</th><th>Input chars<br>median / p95</th><th>Target chars<br>median / p95</th><th>Body chars<br>median / p95</th></tr></thead><tbody>${source.tasks.map(t=>`<tr><td>${esc(recipes[t.id]?.label||t.id)}</td><td class="num">${number(t.count)}</td><td>${lengths(t.lengths.input)}</td><td>${lengths(t.lengths.target)}</td><td>${lengths(t.lengths.body)}</td></tr>`).join('')}</tbody></table></div>
 <p class="note">Character lengths of stored fields, before adding role/date instructions and the chat template. n counts populated fields; document bodies are not automatically training targets. Token lengths are not measured in this inventory.</p>
 ${source.tasks.map(t=>traceHTML(t,country,source.id)).join('')}${sourceTrainingHTML(source,country)}</div></details>`;
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
 return `<article class="method trace-example"><h3>Evidence-conditioned answer (worked candidate)</h3><p class="note">Uses existing project-curated policy evidence. The question below is a clearer illustrative rewrite; the stored original example is unchanged and remains unadmitted.</p>
 <div class="trace-flow" aria-label="Evidence and question flow into the prompt, which produces an SFT target, then receives inspection criteria."><section class="trace-node evidence"><span>1. Evidence + question</span>${e.evidence.map(v=>`<p>${esc(v.claim)}</p>`).join('')}<p class="example-question">${esc(simpleQuestions[country.code])}</p></section><section class="trace-node prompt"><span>2. Prompt</span><p>${esc(country.name)} (policy date ${esc(e.date)})</p><p>System instruction + dated evidence + question</p></section><section class="trace-node target"><span>3. SFT target</span><p>${esc(e.answer)}</p><small>Assistant completion only</small></section><section class="trace-node inspection"><span>4. Inspect / score</span>${list(e.rubric)}<p>Human and source review</p></section></div>
 <p class="note">Evidence and question are model input. The assistant completion is the SFT target. Inspection criteria and provenance remain outside the prompt. The existing SFT implementation uses completion-only loss and Qwen3 with thinking disabled.</p>
 <p>${e.evidence.map(v=>`<a href="${url(v.source_url)}" target="_blank" rel="noopener">${esc(v.id)} ↗</a>`).join(' · ')}</p>
 <details><summary>Stored original candidate and provenance</summary><p class="note">${esc(e.format_origin)}. ${overview.private?'Full stored format.':'Source passages are explicitly omitted from this public format preview.'}</p><pre>${pretty(e.format)}</pre><pre>${pretty(e.metadata)}</pre></details></article>`;
}
function decisionHTML(country){
 if(!decisionShowcase||!['CHN','DEU'].includes(country.code))return '';
 const cases=decisionShowcase.cases.filter(c=>c.country_iso3===country.code);
 return `<section class="decision-section" id="decision-cases"><div class="decision-heading"><div><span class="section-label">Worked decision records</span><h2>From observed decision to post-training trace</h2></div><span class="count">${cases.length} case views · 2 shared events</span></div>
 <p class="note">These historical cases are source checked but await independent review. All eight prompt/completion views are quarantined; they are examples of the format, not an admitted training set or fresh evaluation. Both events concern Ukraine, so they do not establish a general national persona.</p>
 ${cases.map(c=>`<article class="decision-card"><div class="decision-card-head"><div><small>${esc(c.event_date)} · ${esc(c.proposal_symbol)}</small><h3>${esc(c.title)}</h3></div><strong class="vote ${c.observed_action==='abstaining'?'abstain':'favor'}">${esc(c.observed_action)}</strong></div>
 <div class="decision-context"><p><strong>Meeting context:</strong> ${esc(c.setting)}</p><p><strong>Procedure:</strong> ${esc(c.decision_rule)}</p><p><strong>Assembly result:</strong> ${esc(c.assembly_result)}</p></div>
 <div class="decision-facts"><div><span>What the draft proposed</span><ul>${c.clauses.map(p=>`<li><b>${esc(p.id)}</b> ${esc(p.text)}</li>`).join('')}</ul></div><div><span>Attributed national position</span><p class="decision-speaker">${esc(c.national_position.speaker)} · ${esc(c.national_position.statement_time.replaceAll('_',' '))}</p><ul>${c.national_position.positions.map(p=>`<li>${esc(p)}</li>`).join('')}</ul><p class="decision-limit">${esc(c.national_position.evidence_limit)}</p></div></div>
 <div class="decision-flow" aria-label="Decision training trace: source evidence, prompt, assistant target, then inspection">${c.tasks.map((t,i)=>`<div class="decision-task"><div class="decision-task-title"><b>${i+1}. ${t.id==='vote_reconstruction'?'Draft-only vote baseline':'Evidence-grounded decision report'}</b><span>${t.id==='vote_reconstruction'?'Label task':'Calibrated account'}</span></div><div class="decision-steps"><div><span>Prompt / context</span><p>${t.id==='vote_reconstruction'?'Country, date, meeting setting and five paraphrased draft-provision groups. The vote and national statements are withheld.':'Draft provisions, observed vote, Assembly result and attributed national position with its before/after-vote status.'}</p></div><div><span>Assistant completion (SFT target)</span><p>${esc(t.format.completion[0].content).replaceAll('\n','<br>')}</p></div><div><span>Inspect / score</span><p>${esc(t.inspection)}</p></div></div><details><summary>Exact conversational prompt / completion JSON</summary><pre>${pretty(t.format)}</pre></details></div>`).join('')}</div>
 <div class="decision-foot"><span>${esc(c.status)}</span><span><a href="${url(c.sources.draft)}" target="_blank" rel="noopener">Draft ↗</a> · <a href="${url(c.sources.vote)}" target="_blank" rel="noopener">Vote record ↗</a>${c.sources.statement?` · <a href="${url(c.sources.statement)}" target="_blank" rel="noopener">National statement ↗</a>`:''}</span></div></article>`).join('')}
 <p class="refs">Same draft, different recorded votes: China abstained and Germany voted in favor on both events. Their rows share event groups, so a future split must keep each event together. <a href="https://github.com/memo-ozdincer/country-persona-data/blob/main/docs/DECISION_POSTTRAINING_FORMAT.md">Format and admission rules ↗</a></p></section>`;
}
function render(code){
 const country=overview.countries.find(c=>c.code===code)||overview.countries[0],data=inventory.countries[country.code];
 document.title=`${country.name} · Data explorer for persona fine-tuning`;
 $('#countries').innerHTML=overview.countries.map(c=>`<button type="button" data-country="${esc(c.code)}" aria-pressed="${c.code===country.code}" aria-label="${esc(c.name)}, ${number(inventory.countries[c.code].count)} records across separate sources">${esc(c.name)} <span class="count">${number(inventory.countries[c.code].count)}</span></button>`).join('');
 $('#countries').querySelectorAll('button').forEach(b=>b.onclick=()=>{location.hash=`country=${b.dataset.country}`});
 const kinds=[...overview.kinds,{id:'country_statistics',label:'Country statistics'},{id:'evaluation',label:'Evaluation records / views'}];
 $('#country-panel').innerHTML=`<section class="catalog-summary"><div class="country-title"><h1>${esc(country.name)}</h1><span class="count">${number(data.sources.length)} separate sources</span>${['CHN','DEU'].includes(country.code)?'<button class="decision-jump" type="button">Explore 2 decision cases ↓</button>':''}</div>
 <div class="breakdown">${kinds.map(k=>`<div class="metric"><span>${esc(k.label)}</span><b>${number(country.counts[k.id])}</b></div>`).join('')}</div>
 </section>
 <section class="source-section"><h2>Data sources → training examples</h2><div class="training-intro"><strong>Read a source. Choose a task. Inspect every training field.</strong><p>Authentic answers teach observed responses. Policy documents support grounded applications. Votes teach actions only when proposal context is available. Examples preserve these distinctions.</p><p class="note">${trainingExamples.visibility==='owner-only'?'Full original records and complete training examples are available in this research view.':'This public view uses complete project-authored examples and metadata. <a href="https://huggingface.co/spaces/memo-ozdincer/country-persona-research">Open owner-only research explorer for full original text and authentic examples ↗</a>'}</p></div><p class="note">Sorted by source name. Expand a source to see what its records contain, the training objective that fits, and complete numbered examples. Blue blocks are model inputs; green blocks are supervised targets; red blocks are rejected answers.</p>
 ${data.sources.map(s=>sourceHTML(s,country)).join('')}</section>
 ${decisionHTML(country)}
 <section class="methods"><h2>Post-training examples using the available data</h2>
 <div class="method"><h3>Choose the task from the source fields</h3><div class="scroll"><table><thead><tr><th>Available data</th><th>Possible trace</th><th>What is still needed</th></tr></thead><tbody>${data.sources.map(s=>`<tr><td>${esc(profiles[s.id].name)}<br><small>${number(s.count)} record IDs</small></td><td>${s.tasks.map(t=>esc(recipes[t.id].label)).join('<br>')}</td><td>${s.tasks.map(t=>esc(recipes[t.id].availability)).join('<br>')}</td></tr>`).join('')}</tbody></table></div></div>
 <p class="note">Complete worked examples now appear directly inside each source above, beside the records and objectives they use. Source-linked policy, revision, classifier and preference examples are grouped with their parent collection.</p>
 <p class="refs">Implementation references: <a href="https://huggingface.co/docs/trl/sft_trainer#expected-dataset-type-and-format">TRL conversational SFT formats</a> · <a href="https://huggingface.co/docs/peft/conceptual_guides/lora">PEFT LoRA</a> · <a href="https://huggingface.co/Qwen/Qwen3-8B">Qwen3 mode</a>. Research motivation: <a href="https://arxiv.org/abs/2403.10131">RAFT</a> for evidence-conditioned adaptation; <a href="https://aclanthology.org/2020.acl-main.442/">CheckList</a> for behavioral evaluation. These are options to test, not claims of completed RL/SFT environments.</p></section>`;
 document.querySelectorAll?.('.download-example').forEach(b=>b.onclick=()=>{const blob=new Blob([JSON.stringify(JSON.parse(b.dataset.example),null,2)],{type:'application/json'});const href=URL.createObjectURL(blob);const a=document.createElement('a');a.href=href;a.download='training-example.json';a.click();URL.revokeObjectURL(href)});
 const jump=$('.decision-jump');if(jump)jump.onclick=()=>$('#decision-cases').scrollIntoView({behavior:'smooth'});
}
function route(){
 const hash=new URLSearchParams(location.hash.slice(1));
 if(hash.has('id')||hash.has('kind')||hash.get('view')==='files'){location.replace(`advanced.html${location.hash}`);return}
 const country=overview.countries.find(c=>c.code===hash.get('country'))||overview.countries[0];
 history.replaceState(null,'',`#country=${country.code}`);render(country.code);
}
async function start(){try{
 const load=async path=>{const r=await fetch(path);if(!r.ok)throw Error(`Unable to load ${path} (${r.status}).`);return r.json()};
 [overview,inventory,profiles,recipes,decisionShowcase,trainingExamples]=await Promise.all(['overview.json','sources.json','source_profiles.json','trace_types.json','decision-showcase.json','training-examples.json'].map(load));
 if(overview.private){$('#research-link').textContent='Original research archive';$('#research-link').href='https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/resolve/main/research.tar.gz?download=true'}
 window.addEventListener('hashchange',route);route();
 }catch(error){$('#country-panel').innerHTML=`<p class="error">${esc(error.message)} <a href="https://github.com/memo-ozdincer/country-persona-data">Browse the repository.</a></p>`}}
start();
