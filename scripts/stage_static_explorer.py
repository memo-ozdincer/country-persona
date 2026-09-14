"""Generate static public metadata and private full-record explorers, without a server."""
import collections
import gzip
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache'
def dump(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,'wt',encoding='utf-8',compresslevel=6) as f:json.dump(rows,f,ensure_ascii=False,separators=(',',':'))
def main():
    public=CACHE/'explorer-public-static';private=CACHE/'explorer-private-static'
    for dest in (public,private):dest.mkdir(exist_ok=True)
    db=sqlite3.connect(CACHE/'data-publication/catalog.sqlite');db.row_factory=sqlite3.Row
    topics=collections.defaultdict(list);releases=collections.defaultdict(list)
    for uid,value in db.execute('SELECT * FROM record_topics'):topics[uid].append(value)
    for uid,value in db.execute('SELECT * FROM record_collections'):releases[uid].append(value)
    indexes=collections.defaultdict(list);buckets=collections.defaultdict(list);cases=[]
    for raw in db.execute('SELECT * FROM records ORDER BY uid'):
      r=dict(raw);r['details']=json.loads(r['details']);r['locations']=json.loads(r['locations'])
      index={k:v for k,v in r.items() if k not in ('details','locations')};index.update(topic_tags=topics[r['uid']],release_tags=releases[r['uid']])
      indexes[r['kind']].append(index);buckets[r['uid'][:2]].append(r)
      if r['kind']=='decision_cases':cases.append(r)
    files=[dict(r) for r in db.execute('SELECT * FROM files')]
    for kind,rows in indexes.items():dump(public/'indexes'/f'{kind}.json.gz',rows)
    dump(public/'files.json.gz',files);dump(public/'decisions.json.gz',cases)
    for key,rows in buckets.items():dump(public/'records'/f'{key}.json.gz',rows)
    # Private original objects are verified against the immutable content identifier.
    handles={}
    for key,rows in buckets.items():
      originals=[]
      for r in rows:
        loc=r['locations'][0];p=ROOT/loc['path']
        if p not in handles:handles[p]=p.open('rb')
        f=handles[p];f.seek(loc['offset']);obj=json.loads(f.read(loc['length']))
        assert hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==r['uid']
        originals.append(dict(r,original_record=obj))
      dump(private/'records'/f'{key}.json.gz',originals)
    for f in handles.values():f.close()
    shutil.copytree(public/'indexes',private/'indexes',dirs_exist_ok=True)
    for n in ['files.json.gz','decisions.json.gz']:shutil.copyfile(public/n,private/n)
    shutil.copyfile(CACHE/'explorer-private/research.tar.gz',private/'research.tar.gz')
    archive=CACHE/'research-files-dataset';archive.mkdir(exist_ok=True)
    shutil.copyfile(private/'research.tar.gz',archive/'research.tar.gz')
    (archive/'file-inventory.json').write_text(json.dumps(files,indent=2)+'\n')
    shutil.copyfile(ROOT/'data/rights_registry.json',archive/'rights_registry.json')
    (archive/'README.md').write_text('---\npretty_name: Country Persona Research Files\n---\n# Country Persona Research Files\n\nCreated and maintained by **Memo Ozdincer**. Private original research archive; publishers retain attribution and source-use status.\n\n[Full research browser](https://huggingface.co/spaces/memo-ozdincer/country-persona-research)\n\n`research.tar.gz` contains all raw, canonical and prepared files listed in `file-inventory.json`, with original paths. This is an archive, not a train/test dataset. New decision cases remain review candidates. Sign in to download.\n')
    html=(ROOT/'explorer/index.html').read_text()
    html=html.replace('<script>','<script src="data-client.js"></script>\n<script>',1)
    html=html.replace("async function get(url){const r=await fetch(url);const x=await r.json();if(!r.ok)throw Error(x.error||r.statusText);return x}","async function get(url){return STATIC_DATA.get(url)}")
    html=html.replace("$('#filters').onchange=", "$('#export').onclick=async e=>{e.preventDefault();const a=e.currentTarget;const old=a.textContent;a.textContent='Preparing download…';try{await STATIC_DATA.exportSelection(a.href)}catch(err){alert(err.message)}finally{a.textContent=old}};\n$('#filters').onchange=")
    html=html.replace('Download selection</a>','Download matching metadata</a>')
    for dest,is_private in [(public,False),(private,True)]:
      page=html
      if is_private:page=page.replace('<footer>','<section class="wide"><a class="btn" href="https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/resolve/main/research.tar.gz?download=true">Download all original research files (compressed archive)</a><p class="tiny muted" style="margin-top:12px">The archive includes the complete file inventory. Record details above load individually.</p></section><footer>')
      (dest/'index.html').write_text(page);shutil.copyfile(ROOT/'explorer/data-client.js',dest/'data-client.js')
      stats=json.loads((CACHE/'data-publication/stats.json').read_text());stats['local_full_data']=is_private;stats['hosting']='static';stats['private_archive_available']=is_private
      (dest/'stats.json').write_text(json.dumps(stats,indent=2)+'\n')
      title='Country Persona Research' if is_private else 'Country Persona Explorer'
      (dest/'README.md').write_text(f'---\ntitle: {title}\nemoji: 🌐\ncolorFrom: blue\ncolorTo: green\nsdk: static\napp_file: index.html\npinned: false\n---\n# {title}\n\nCreated and maintained by **Memo Ozdincer**. '+('Account-only full original research records and files.' if is_private else 'Public metadata, factual values and source-grounded summaries.')+'\n\n[GitHub](https://github.com/memo-ozdincer/country-persona-data) · [Data tables](https://huggingface.co/datasets/memo-ozdincer/country-persona-data)\n')
    from build_explorer_overview import build, stage, github
    from build_source_inventory import build_inventory
    build_inventory()
    overview = build(); stage(overview); github(overview)
    report={'public_files':sum(p.is_file() for p in public.rglob('*')),'private_files':sum(p.is_file() for p in private.rglob('*')),'original_records_hash_verified':sum(map(len,buckets.values())),'index_rows':sum(map(len,indexes.values())),'public_bytes':sum(p.stat().st_size for p in public.rglob('*') if p.is_file()),'private_bytes':sum(p.stat().st_size for p in private.rglob('*') if p.is_file()),'private_host_bytes':sum(p.stat().st_size for p in private.rglob('*') if p.is_file() and p.name!='research.tar.gz'),'private_archive_bytes':(archive/'research.tar.gz').stat().st_size}
    (ROOT/'reports/static-explorer-build.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
