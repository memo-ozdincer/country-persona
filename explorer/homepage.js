/* Public figures use frozen, source-linked data; no model calls or remote APIs. */
(() => {
  function redirectLegacy() {
    const oldRoute = new URLSearchParams(location.hash.slice(1));
    if (oldRoute.has('country') || oldRoute.has('id') || oldRoute.has('kind') || oldRoute.has('view')) {
      location.replace(`data.html${location.hash}`);
      return true;
    }
    return false;
  }
  addEventListener('hashchange', redirectLegacy);
  if (redirectLegacy()) return;
  const $ = selector => document.querySelector(selector);
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = n => new Intl.NumberFormat('en-US').format(n);
  const colors = {primary:'#1f4e79', blue:'#4472c4', gray:'#808080', ink:'#222222'};
  let data;
  const names = {
    base:'Base model', 'prompted-base':'Constitution-prompted base',
    'reproduction-dpo':'Fresh DPO', 'reproduction-full-sequential':'Fresh DPO + SFT',
    'author-dpo':'Released DPO', 'author-full-sequential':'Released sequential full'
  };
  const arms = Object.keys(names);
  const armColor = arm => arm.startsWith('author') ? '#595959' : arm === 'base' ? '#a6a6a6' : arm === 'prompted-base' ? colors.gray : arm === 'reproduction-dpo' ? colors.blue : colors.primary;
  const svg = (width, height, title, body) => `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}">${body}</svg>`;
  const text = (x,y,value,cls='label',extra='') => `<text x="${x}" y="${y}" class="${cls}" ${extra}>${esc(value)}</text>`;
  function cellColor(value, maximum, logarithmic=false) {
    const ratio = logarithmic ? Math.log1p(value)/Math.log1p(maximum) : value/maximum;
    const shade=ratio>.8?'#1f4e79':ratio>.55?'#4472c4':ratio>.3?'#b4c6e7':ratio>.1?'#dae3f3':'#f2f2f2';
    return `background:${shade};color:${ratio>.55?'#fff':'#222222'}`;
  }
  const link = (url, label) => /^https?:\/\//.test(url || '') ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>` : esc(label);
  function countryRegister() {
    $('#country-register').innerHTML=data.countries.map(c=>`<tr id="country-${c.code}"><th scope="row"><a class="country-name" href="data.html#country=${c.code}"><img src="${esc(c.flag)}" alt="Flag of ${esc(c.name)}" width="26" height="19"><span>${esc(c.name)}<small>${c.code} · ${['CHN','DEU'].includes(c.code)?'Original collection':'Active extension'}</small></span></a></th><td>${fmt(c.count)}</td><td>${fmt(c.kinds.source_records)}</td><td>${fmt(c.kinds.observed_actions)}</td><td>${fmt(c.kinds.evidence_passages)}</td><td>${c.source_collections}</td><td>${c.languages.join(', ')}</td></tr>`).join('');
    $('#catalog-object-stat').textContent=fmt(data.catalog.exact_unique_records);
    $('#catalog-file-stat').textContent=fmt(data.catalog.inventory_files);
  }
  function recordExample(index) {
    const example=data.record_examples[index],record=example.record,pointer=example.pointer||{};
    const country=record.country_iso3||record.country||example.metadata?.country_iso3||'ALL';
    const date=record.event_date||record.statement_date||pointer.date||'2021-12-09';
    const title=pointer.title||record.symbol||record.title||example.metadata?.id||record.id;
    const fields=[['Country',country],['Date',date],['Institution',record.institution],['Role',record.speaking_capacity||record.source_role],['Speaker',record.speaker],['Split',record.split||example.metadata?.split],['Review status',record.review_status||example.metadata?.review_status],['Quality flags',record.quality_flags?.join(', ')],['Training admitted',record.training_admitted===undefined?undefined:String(record.training_admitted)],['Document symbols',record.document_symbols?.join(', ')],['Observed action',record.observed_action]].filter(([,v])=>v!==undefined&&v!==null&&v!=='');
    let content='';
    if(record.text) content=`<div class="record-role">Original statement · complete stored text</div><div class="record-text">${esc(record.text)}</div>`;
    if(record.prompt) content=record.prompt.map(m=>`<div class="record-role">Prompt · ${esc(m.role)}</div><div class="message-text">${esc(m.content)}</div>`).join('')+record.completion.map(m=>`<div class="record-role">Completion · ${esc(m.role)}</div><div class="message-text">${esc(m.content)}</div>`).join('')+`<p class="chart-note">The saved row contains an assistant-authored target. It is an actual training artifact, not an authentic government statement. Independent review remains pending.</p>`;
    if(record.proposal_summary) content=`<div class="record-role">Project annotation · proposal</div><p class="record-annotation">${esc(record.proposal_summary)}</p><div class="record-role">Project annotation · national statement</div><p class="record-annotation">${esc(record.statement_summary)}</p><p class="chart-note">This case includes the observed outcome and a post-vote statement. It is a retrospective case, not a prediction input.</p>`;
    const projectionNote=example.scope==='Public metadata projection'?`<p class="chart-note">The fields below are the exact public metadata projection. Source bodies remain in the research copies.${example.type==='Country statistic'?' This projection omits the statistic’s value.':example.type==='Vote record'?' This projection omits the vote value and proposal text.':''}</p>`:'';
    const source=record.source_url||pointer.source_url;
    $('#record-example').innerHTML=`<div class="record-header"><div class="record-scope">${esc(example.scope)}</div><h4>${esc(title||example.type)}</h4><div class="record-meta"><span>${esc(example.type)}</span><span>${esc(country)} · ${esc(date)}</span></div></div>${projectionNote}<dl class="record-fields">${fields.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>${content}<p class="record-citation">${source?link(source,'Original publisher'):record.sources?Object.entries(record.sources).map(([label,url])=>link(url,label)).join(' · '):'<a href="training-samples.html">Saved training artifact and source statements ↗</a>'}${pointer.file?`<br>Stored location: ${esc(pointer.file)} · line ${pointer.line}`:''}</p><details><summary>Complete stored ${example.scope==='Public metadata projection'?'metadata projection':'record'} · JSON</summary><pre>${esc(JSON.stringify(record,null,2))}</pre></details>`;
    document.querySelectorAll('[data-record-example]').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.recordExample)===index)));
  }
  function recordExamples() {
    $('#record-tabs').innerHTML=data.record_examples.map((e,i)=>`<button type="button" data-record-example="${i}" aria-pressed="${i===1}">${esc(e.type)}</button>`).join('');
    $('#record-tabs').addEventListener('click',event=>{const button=event.target.closest('[data-record-example]');if(button)recordExample(Number(button.dataset.recordExample));});
    recordExample(1);
  }
  function policyExample(code) {
    const example=data.policy_examples.find(e=>e.country===code),country=data.countries.find(c=>c.code===code);
    const topics={CHN:'Development cooperation',DEU:'Critical dependencies',FRA:'European defense',GBR:'Climate commitments',IND:'Fisheries subsidies',BRA:'WTO development provisions'};
    $('#policy-example').innerHTML=`<div class="policy-head"><div><div class="record-role">Project-authored policy application</div><h4>${esc(country.name)} · ${esc(topics[code])}</h4></div><time datetime="${esc(example.date)}">Policy date: ${esc(example.date)}</time></div><div class="record-role">Question · exact stored text</div><p class="policy-question">${esc(example.question)}</p><div class="record-role">Target answer · exact stored text</div><div class="policy-answer">${esc(example.answer)}</div><ul class="policy-sources">${example.evidence.map(e=>`<li>${link(e.source_url,e.id)}<br>${esc(e.claim)}${e.spans?.length?`<br>Source spans: ${e.spans.map(v=>`${v.pdf_pages?.length?`pages ${v.pdf_pages.join(', ')}, `:''}characters ${v.char_start}–${v.char_end}`).join(' · ')}`:''}</li>`).join('')}</ul><p class="policy-review"><b>Review criteria:</b> ${example.rubric.map(esc).join(' · ')}<br>Quarantined review candidate · training admitted: ${String(example.metadata.training_admitted)} · independent review pending</p><details><summary>Stored question, answer, evidence, and metadata · JSON</summary><pre>${esc(JSON.stringify(example,null,2))}</pre></details>`;
    document.querySelectorAll('[data-policy-country]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.policyCountry===code)));
  }
  function policyExamples() {
    $('#policy-country-tabs').innerHTML=data.countries.map(c=>`<button type="button" data-policy-country="${c.code}" aria-pressed="${c.code==='CHN'}"><img src="${esc(c.flag)}" alt="" width="20" height="15">${esc(c.name)}</button>`).join('');
    $('#policy-country-tabs').addEventListener('click',event=>{const button=event.target.closest('[data-policy-country]');if(button)policyExample(button.dataset.policyCountry);});
    policyExample('CHN');
  }
  function inventoryMatrix() {
    const max=Math.max(...data.countries.flatMap(c=>Object.values(c.groups)));
    $('#source-matrix').innerHTML=`<table class="matrix"><caption>Evidence record IDs per country and source family. Color is logarithmic. Numbers are exact.</caption><thead><tr><th scope="col">Evidence family</th>${data.countries.map(c=>`<th scope="col"><a class="country-link" href="data.html#country=${c.code}">${esc(c.code)}</a><br><span style="font-size:9px">${esc(c.name)}</span></th>`).join('')}</tr></thead><tbody>${data.groups.map((group,i)=>`<tr><th class="row-name" scope="row">${esc(group)}</th>${data.countries.map(c=>{const n=c.groups[group];return `<td class="${n?'':'empty'}" style="${n?cellColor(n,max,true):''}"><button type="button" data-source-group="${i}" data-country="${c.code}" aria-label="Inspect ${esc(c.name)}, ${esc(group)}: ${fmt(n)} evidence records">${n?fmt(n):'—'}</button></td>`}).join('')}</tr>`).join('')}</tbody></table>`;
    const groupSources={
      'Press conferences':['mfa','germany_press'],
      'National policy & diplomacy':['china_mission','germany_mission','germany_aa','national_policy_documents','france_mfa','france_elysee','france_sgdsn','uk_cabinet_office','uk_fcdo','uk_desnz','india_un_mission','india_pib','brazil_funag','brazil_mma'],
      'UN speeches':['unga_speech_corpus','ungdc'], 'UNGA votes':['unga_dm'],
      'Human-rights records':['uhri','upr_reports'], 'WTO policy reports':['wto'],
      'Country statistics':['world_bank'], 'Annotations & joined cases':['curated','decision_cases'], 'Linked task samples':['unbench']
    };
    $('#source-matrix').addEventListener('click',event=>{
      const button=event.target.closest('[data-source-group]');if(!button)return;
      const country=data.countries.find(c=>c.code===button.dataset.country),group=data.groups[Number(button.dataset.sourceGroup)];
      const sources=country.sources.filter(s=>groupSources[group].includes(s.id));
      $('#source-detail').innerHTML=`<p><b>${esc(country.name)} · ${esc(group)}</b> — ${fmt(country.groups[group])} stored IDs.</p><p>${sources.length?sources.map(s=>`${esc(s.id.replaceAll('_',' '))}: ${fmt(s.count)}`).join(' · '):'No indexed records in this source family.'} <a href="data.html#country=${country.code}">Inspect the country’s sources ↗</a></p>`;
    });
  }
  function corpusBars(kind='source_records') {
    const labels={source_records:'Source records',observed_actions:'Observed actions / responses',evidence_passages:'Evidence passages'};
    const max=Math.max(...data.countries.map(c=>c.kinds[kind]||0));
    const axisMax=Math.ceil(max/1000)*1000,x=185,width=660;
    let body='';
    for(let i=0;i<=4;i++) {const v=axisMax*i/4,px=x+width*i/4;body+=`<path class="axis" d="M${px} 24V305"/>`+text(px,19,fmt(v),'small','text-anchor="middle"');}
    data.countries.forEach((c,i)=>{const y=49+i*44,v=c.kinds[kind]||0;body+=text(0,y+6,c.name,'name')+`<rect x="${x}" y="${y-12}" width="${v/axisMax*width}" height="25" rx="2" fill="${['CHN','DEU'].includes(c.code)?'#a6a6a6':colors.primary}"/>`+text(x+v/axisMax*width+12,y+6,fmt(v),'value');});
    $('#corpus-bars').innerHTML=svg(940,320,`${labels[kind]} by country: ${data.countries.map(c=>`${c.name} ${fmt(c.kinds[kind]||0)}`).join(', ')}`,body);
    $('#corpus-note').textContent={source_records:'Stored documents, Q&A, segments, and institutional records. Original collections are gray. The active four-country extension is blue.',observed_actions:'Recorded votes and institutional responses. Labels do not automatically provide motives or complete decision environments.',evidence_passages:'Extracted evidence spans. They can overlap parent documents and each other; they are not additional independent decisions.'}[kind];
  }
  function timeline() {
    const requests=[['FRA','unga_dm','UNGA voting archive · France'],['CHN','unga_dm','UNGA voting archive · China'],['DEU','ungdc','General Debate · Germany'],['IND','uhri','Human-rights index · India'],['CHN','mfa','Press conferences · China'],['DEU','germany_press','Press conferences · Germany'],['FRA','france_sgdsn','Strategic review · France'],['GBR','uk_cabinet_office','Security strategy · UK']];
    const from=1946,to=2027,x=273,w=585,scale=v=>x+(v-from)/(to-from)*w;let body='';
    [1950,1970,1990,2010,2026].forEach(v=>{const px=scale(v);body+=`<path class="axis" d="M${px} 30V363"/>`+text(px,19,v,'small','text-anchor="middle"');});
    requests.forEach(([c,s,label],i)=>{const source=data.countries.find(v=>v.code===c).sources.find(v=>v.id===s),dates=source.dates.map(v=>Number(v.slice(0,4)));const y=52+i*40;body+=text(0,y+4,label,'label')+`<path d="M${scale(dates[0])} ${y}H${scale(dates[1])}" stroke="${i>3?colors.gray:colors.primary}" stroke-width="8" stroke-linecap="round"/>`+text(scale(dates[1])+13,y+4,dates[0]===dates[1]?dates[0]:`${dates[0]}–${dates[1]}`,'small');});
    $('#timeline').innerHTML=svg(955,380,'Selected source collection date endpoints, from 1946 UNGA voting to 2026 press conferences. Bars do not imply continuous coverage.',body);
  }
  function benchmarkDonut() {
    const b=data.benchmarks.unsc,r=78,circ=2*Math.PI*r,fraction=b.adopted/b.events;
    const body=`<circle cx="140" cy="100" r="${r}" fill="none" stroke="${colors.gray}" stroke-width="20"/><circle cx="140" cy="100" r="${r}" fill="none" stroke="${colors.primary}" stroke-width="20" stroke-dasharray="${circ*fraction} ${circ*(1-fraction)}" transform="rotate(-90 140 100)"/>`+text(140,102,b.events,'value','text-anchor="middle" style="font-size:39px;font-family:var(--serif);font-weight:400"')+text(140,125,'event records','small','text-anchor="middle"')+text(255,68,`${b.adopted} adopted`,'name')+text(255,88,`${(fraction*100).toFixed(1)}% of records`,'small')+text(255,135,`${b.vetoed} vetoed`,'name')+text(255,155,`${((1-fraction)*100).toFixed(1)}% of records`,'small');
    $('#benchmark-donut').innerHTML=svg(420,203,`${b.events} acquired UNSC-Bench event records: ${b.adopted} adopted, ${b.vetoed} vetoed`,body);
  }
  function humorBars(condition='default') {
    const x=242,w=572,max=80;let body='';
    [0,20,40,60,80].forEach(v=>{const px=x+v/max*w;body+=`<path class="axis" d="M${px} 30V346"/>`+text(px,19,`${v}%`,'small','text-anchor="middle"');});
    arms.forEach((arm,i)=>{const v=data.humor.arms[arm][condition].rate,y=57+i*49;body+=text(0,y+5,names[arm],'name')+`<rect x="${x}" y="${y-13}" width="${v/max*w}" height="27" rx="2" fill="${armColor(arm)}"/>`+text(x+v/max*w+12,y+5,`${v.toFixed(1)}%`,'value');if(i===3)body+=`<path d="M0 ${y+25}H905" stroke="#d9d9d9" stroke-dasharray="3 4"/>`;});
    $('#humor-bars').innerHTML=svg(940,355,`${condition==='default'?'Default':'Strongest neutrality'} humor recognition: ${arms.map(a=>`${names[a]} ${data.humor.arms[a][condition].rate}%`).join(', ')}`,body);
    $('#humor-note').textContent=condition==='default'?'Default condition: the fresh full recipe is +48.2 percentage points over base and +11.6 over constitution prompting. Released weights are comparison controls.':'Strong neutrality: the fresh full recipe is +31.0 percentage points over base and +29.0 over constitution prompting. The instruction explicitly asks the model to try very hard to answer neutrally.';
  }
  function humorMatrix() {
    const conditions=[['default','Default'],['0','Ignore roleplay; true identity'],['1','Do not roleplay'],['2','Remove conversational style'],['3','Respond as feels most like you'],['4','Helpful, honest, harmless'],['5','Neutral and natural'],['6','Ignore earlier style instructions'],['7','Try very hard to answer neutrally']];
    const headings=['Base','Prompted<br>base','Fresh<br>DPO','Fresh<br>DPO + SFT','Released<br>DPO','Released<br>full'];
    $('#humor-matrix').innerHTML=`<table class="matrix"><thead><tr><th scope="col">Evaluation condition</th>${headings.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${conditions.map(([key,label])=>`<tr><th class="row-name" scope="row">${label}</th>${arms.map(a=>{const value=data.humor.arms[a][key];return `<td style="${cellColor(value.rate,70)}" title="${esc(names[a])}: ${value.recognized}/${value.n} recognized as humorous">${value.rate.toFixed(1)}</td>`}).join('')}</tr>`).join('')}</tbody></table>`;
  }
  function planBars() {
    const x=242,w=560,max=24;let body='';
    [0,6,12,18,24].forEach(v=>{const px=x+v/max*w;body+=`<path class="axis" d="M${px} 26V286"/>`+text(px,17,v,'small','text-anchor="middle"');});
    data.planning_control.conditions.forEach((c,i)=>{const y=45+i*82;body+=text(0,y+26,c.label,'name');[['base',colors.blue],['adapter',colors.primary]].forEach(([key,color],j)=>{const py=y+j*28;body+=`<rect x="${x}" y="${py}" width="${c[key]/max*w}" height="21" rx="2" fill="${color}"/>`+text(x+c[key]/max*w+11,py+16,`${c[key]}/24`,'value');});});
    $('#plan-bars').innerHTML=svg(940,294,'Country development control: raw source base 18 and adapter 18 of 24; checked plan base 18 and adapter 22; explicit-boundary plan base 24 and adapter 22.',body);
  }
  async function start() {
    try {
      const response=await fetch('homepage-data.json');if(!response.ok)throw Error(`Figure data returned ${response.status}`);
      data=await response.json();$('#source-stat').textContent=data.distinct_source_collections;
      countryRegister();recordExamples();policyExamples();inventoryMatrix();corpusBars();timeline();benchmarkDonut();humorBars();humorMatrix();planBars();
      document.querySelectorAll('[data-kind]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-kind]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));corpusBars(button.dataset.kind);}));
      document.querySelectorAll('[data-condition]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-condition]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));humorBars(button.dataset.condition);}));
      document.body.dataset.figuresReady='true';
    } catch(error) {
      const message=document.createElement('p');message.className='error-message';message.textContent='The figure data could not load. The document and data catalog remain available. Serve this folder over HTTP to use the interactive graphics.';$('.essay').prepend(message);console.error(error);
    }
  }
  start();
})();
