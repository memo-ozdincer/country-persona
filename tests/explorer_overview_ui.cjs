const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
// Run from the repository root: node tests/explorer_overview_ui.cjs
const data = JSON.parse(fs.readFileSync('explorer/overview.json'));
const elements = new Map();
function element(id) { if (!elements.has(id)) elements.set(id, {innerHTML:'',textContent:'',querySelectorAll:()=>[]}); return elements.get(id); }
const document = {title:'',querySelector:element,createElement:()=>({click(){}})};
const location = {hash:'#view=compare',replace(value){this.redirect=value}};
const history = {replaceState(a,b,value){location.hash=value}};
const context = {document, location, history, window:{addEventListener(){}}, URL, URLSearchParams, Blob, setTimeout,
  fetch: async()=>({ok:true,json:async()=>data})};
vm.createContext(context);
vm.runInContext(fs.readFileSync('explorer/overview.js','utf8'),context);
setImmediate(()=>{
 assert.equal(location.hash,'#country=CHN');
 for (const c of data.countries) {
   location.hash=`#country=${c.code}`;vm.runInContext('route()',context);
   const html=element('#country-panel').innerHTML;
   assert(html.includes(c.name));assert(html.includes('completion_only_loss=True'));assert(html.includes('SOURCE PASSAGES OMITTED'));
   assert(html.includes(c.examples[0].id));assert(html.includes('Download redacted format preview'));
 }
 location.hash='#view=compare&country=DEU';vm.runInContext('route()',context);assert.equal(location.hash,'#country=DEU');
 location.hash='#kind=policy_positions&view=explore';vm.runInContext('route()',context);assert.equal(location.redirect,'advanced.html#kind=policy_positions&view=explore');
 location.hash='#country=NONEXISTENT';vm.runInContext('route()',context);assert.equal(location.hash,'#country=CHN');
 assert(!element('#country-panel').innerHTML.includes('undefined'));
 console.log('All six country renders, format fields, legacy comparison routing and deep-link preservation passed.');
});
