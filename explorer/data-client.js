// Static-hosted data access. Full source records are present only in the private build.
const STATIC_DATA = (()=>{
  const cache=new Map();
  async function load(path){
    if(!cache.has(path))cache.set(path,(async()=>{
      const r=await fetch(path);if(!r.ok)throw Error('Could not load '+path+' ('+r.status+').');
      if(path.endsWith('.gz'))return await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();
      return await r.json();
    })().catch(e=>{cache.delete(path);throw e}));
    return cache.get(path);
  }
  async function selection(p){
    const stats=await load('stats.json');const kind=p.get('kind');
    const kinds=kind&&stats.record_kinds[kind]?[kind]:Object.keys(stats.record_kinds);
    const parts=await Promise.all(kinds.map(k=>load('indexes/'+k+'.json.gz')));
    const q=(p.get('q')||'').toLocaleLowerCase().split(/\s+/).filter(Boolean);
    return parts.flat().filter(r=>{
      if(p.get('country')&&!r.country.split(' / ').includes(p.get('country')))return false;
      for(const k of ['language','source','split','readiness'])if(p.get(k)&&r[k]!==p.get(k))return false;
      for(const [k,tags] of [['topic','topic_tags'],['release','release_tags']])if(p.get(k)&&!r[tags].includes(p.get(k)))return false;
      const low=r.date.length===4?r.date+'-01-01':r.date.length===7?r.date+'-01':r.date;
      const high=r.date.length===4?r.date+'-12-31':r.date.length===7?r.date+'-31':r.date;
      if(p.get('after')&&(!r.date||high<p.get('after')))return false;
      if(p.get('before')&&(!r.date||low>p.get('before')))return false;
      if(q.length){const text=[r.record_id,r.country,r.title,r.summary,r.source,r.topic,r.language].join(' ').toLocaleLowerCase();if(!q.every(t=>text.includes(t)))return false}
      return true;
    }).sort((a,b)=>b.date.localeCompare(a.date)||a.uid.localeCompare(b.uid));
  }
  async function get(url){
    const u=new URL(url,location.href),p=u.searchParams;
    if(u.pathname==='/api/stats')return load('stats.json');
    if(u.pathname==='/api/records'){const rows=await selection(p),n=Number(p.get('offset')||0);return {total:rows.length,rows:rows.slice(n,n+30)}}
    if(u.pathname==='/api/record'){
      const id=p.get('id')||'';if(!/^[a-f0-9]{64}$/.test(id))throw Error('Invalid record identifier.');
      const rows=await load('records/'+id.slice(0,2)+'.json.gz'),row=rows.find(r=>r.uid===id);
      if(!row)throw Error('This record is not in the current snapshot. Search by country or source to find its current version.');return row;
    }
    if(u.pathname==='/api/compare')return load('decisions.json.gz');
    if(u.pathname==='/api/files'){
      const q=(p.get('q')||'').toLocaleLowerCase(),all=await load('files.json.gz');
      const rows=all.filter(r=>(r.path+' '+r.collection).toLocaleLowerCase().includes(q));const n=Number(p.get('offset')||0);
      return {total:rows.length,rows:rows.slice(n,n+50),local_full_data:false};
    }
    throw Error('Unknown data view.');
  }
  async function exportSelection(url){
    const rows=await selection(new URL(url,location.href).searchParams);
    const blob=new Blob(rows.map(r=>JSON.stringify(r)+'\n'),{type:'application/x-ndjson'});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='country-persona-selection-metadata.jsonl';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),30000);
  }
  return {get,exportSelection};
})();
