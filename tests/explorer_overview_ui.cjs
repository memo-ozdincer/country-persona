const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
// Run from the repository root: node tests/explorer_overview_ui.cjs
const data = JSON.parse(fs.readFileSync('explorer/overview.json'));
const elements = new Map();
function element(id) { if (!elements.has(id)) elements.set(id, {innerHTML:'',textContent:'',querySelectorAll:()=>[]}); return elements.get(id); }
const document = {title:'',querySelector:element,createElement:()=>({click(){}})};
const location = {hash:'#view=compare',replace(value){this.redirect=value}};
const history = {replaceState(a,b,value){location.hash=value}};
const context = {document, location, history, window:{addEventListener(){}}, URL, URLSearchParams, Blob, setTimeout,
  fetch: async path=>({ok:true,json:async()=>JSON.parse(fs.readFileSync('explorer/'+path))})};
vm.createContext(context);
vm.runInContext(fs.readFileSync('explorer/overview.js','utf8'),context);
setImmediate(()=>{
 assert.equal(location.hash,'#country=CHN');
 for (const c of data.countries) {
   location.hash=`#country=${c.code}`;vm.runInContext('route()',context);
   const html=element('#country-panel').innerHTML;
   assert(html.includes(c.name));assert(html.includes('completion-only loss'));assert(html.includes('SOURCE PASSAGES OMITTED'));
   assert(html.includes(c.examples[0].id));assert(html.includes('Data sources'));assert(html.includes('Trace template and an actual source-record reference'));
   const inventory=JSON.parse(fs.readFileSync('explorer/sources.json'));
   assert(element('#countries').innerHTML.includes(inventory.countries[c.code].count.toLocaleString()));
   assert(html.indexOf('Data sources')<html.indexOf('Post-training examples using the available data'));
   if (['CHN','DEU'].includes(c.code)) {
     assert(html.includes('From observed decision to post-training trace'));
     assert(html.includes('Exact conversational prompt / completion JSON'));
     assert(html.includes('2 shared events'));
     assert(html.indexOf('From observed decision to post-training trace')<html.indexOf('Post-training examples using the available data'));
   } else assert(!html.includes('From observed decision to post-training trace'));
   assert(!html.includes('Memo Ozdincer'));
   assert(!html.includes('Environment inventory:'));
   const page=fs.readFileSync('explorer/index.html','utf8');
   assert(page.indexOf('class="contribute"')>page.indexOf('id="build-guide"'));
   for(const heading of ['Interactive environments','Multi-agent trajectories','Reward verifiers and possible RLVR tasks','Preference pairs'])assert(page.includes('<h3>'+heading+'</h3>'));
 }
 location.hash='#view=compare&country=DEU';vm.runInContext('route()',context);assert.equal(location.hash,'#country=DEU');
 location.hash='#kind=policy_positions&view=explore';vm.runInContext('route()',context);assert.equal(location.redirect,'advanced.html#kind=policy_positions&view=explore');
 location.hash='#country=NONEXISTENT';vm.runInContext('route()',context);assert.equal(location.hash,'#country=CHN');
 assert(!element('#country-panel').innerHTML.includes('undefined'));
 console.log('All six country counts, source inventories, trace mappings, neutral branding and legacy routes passed.');
});
