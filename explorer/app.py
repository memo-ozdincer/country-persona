"""Read-only country-data browser. Public metadata; optional explicit local full-data mode."""
import gzip
import json
import os
import shutil
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE=Path(__file__).resolve().parent
DB=Path(os.environ.get('CATALOG_DB',str(HERE/'catalog.sqlite')))
STATS=Path(os.environ.get('CATALOG_STATS',str(HERE/'stats.json')))
LOCAL=Path(os.environ['PRIVATE_DATA_ROOT']).resolve() if os.environ.get('PRIVATE_DATA_ROOT') else None
FILTERS={'kind','language','source','split','readiness','release','topic'}

def connect():
    db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);db.row_factory=sqlite3.Row;return db

def query(params):
    clauses=[];values=[]
    for key in FILTERS-{'topic','release'}:
        if params.get(key):clauses.append(f'r.{key}=?');values.append(params[key])
    for key,table in [('topic','record_topics'),('release','record_collections')]:
        if params.get(key):clauses.append(f'EXISTS(SELECT 1 FROM {table} c WHERE c.uid=r.uid AND c.{key}=?)');values.append(params[key])
    if params.get('country'):
        clauses.append('EXISTS(SELECT 1 FROM record_countries c WHERE c.uid=r.uid AND c.country=?)');values.append(params['country'])
    for key,op in [('after','>='),('before','<=')]:
        if params.get(key):
            suffix="CASE length(r.date) WHEN 4 THEN r.date||'-12-31' WHEN 7 THEN r.date||'-31' ELSE r.date END" if key=='after' else "CASE length(r.date) WHEN 4 THEN r.date||'-01-01' WHEN 7 THEN r.date||'-01' ELSE r.date END"
            clauses.append(f"r.date!='' AND ({suffix}) {op} ?");values.append(params[key])
    if params.get('q'):
        terms=params['q'][:300].split()
        term=' AND '.join('"'+s.replace('"','""')+'"' for s in terms)
        if term:clauses.append('r.uid IN (SELECT uid FROM search WHERE search MATCH ?)');values.append(term)
    return (' WHERE '+' AND '.join(clauses) if clauses else ''),values

def decode(r):
    r=dict(r)
    for k in ['details','locations']:
        if k in r:r[k]=json.loads(r[k])
    return r

def original(row):
    if not LOCAL:return None
    loc=row['locations'][0];p=(LOCAL/loc['path']).resolve()
    if not p.is_relative_to(LOCAL):raise ValueError('Outside data root')
    with p.open('rb') as f:f.seek(loc['offset']);raw=f.read(loc['length'])
    import hashlib
    r=json.loads(raw)
    digest=hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=row['uid']:raise ValueError('Source changed; rebuild the catalog before reading this row')
    return r

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
      try:self.route()
      except (BrokenPipeError,ConnectionResetError):pass
      except (ValueError,sqlite3.OperationalError) as e:self.reply({'error':str(e)},400)
      except Exception:self.reply({'error':'Unable to read the catalog. Check the local server configuration.'},500)
    def route(self):
      url=urlparse(self.path);p={k:v[0] for k,v in parse_qs(url.query).items()}
      assets={'/':'index.html','/index.html':'index.html','/advanced.html':'advanced.html','/overview.js':'overview.js','/overview.css':'overview.css','/overview.json':'overview.json'}
      if url.path in assets:
        name=assets[url.path];data=(HERE/name).read_bytes()
        mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'}[Path(name).suffix]
        self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data);return
      if url.path=='/health':self.reply({'ok':DB.exists()});return
      with connect() as db:
        if url.path=='/api/stats':
          stats=json.loads(STATS.read_text());stats['local_full_data']=bool(LOCAL)
          self.reply(stats);return
        if url.path=='/api/record':
          row=db.execute('SELECT * FROM records WHERE uid=?',(p.get('id',''),)).fetchone()
          if not row:self.reply({'error':'Record not found'},404);return
          row=decode(row)
          if LOCAL:row['original_record']=original(row)
          self.reply(row);return
        if url.path=='/api/compare':
          rows=[decode(r) for r in db.execute("SELECT * FROM records WHERE kind='decision_cases' ORDER BY date,country")]
          self.reply(rows);return
        if url.path=='/api/files':
          limit=min(100,max(1,int(p.get('limit',50))));offset=max(0,int(p.get('offset',0)))
          q='%'+p.get('q','').replace('!','!!').replace('%','!%').replace('_','!_')+'%'
          args=[q,q];where=" WHERE path LIKE ? ESCAPE '!' OR collection LIKE ? ESCAPE '!'"
          count=db.execute('SELECT COUNT(*) FROM files'+where,args).fetchone()[0]
          rows=[dict(r) for r in db.execute('SELECT * FROM files'+where+' ORDER BY path LIMIT ? OFFSET ?',args+[limit,offset])]
          self.reply({'total':count,'rows':rows,'local_full_data':bool(LOCAL)});return
        if url.path=='/api/download-file':
          if not LOCAL:self.reply({'error':'Source bytes are held in the local research copy. Follow the original publisher link.'},403);return
          row=db.execute('SELECT * FROM files WHERE path=?',(p.get('path',''),)).fetchone()
          if not row:self.reply({'error':'Not inventoried'},404);return
          path=(LOCAL/row['path']).resolve()
          if not path.is_relative_to(LOCAL):raise ValueError('Invalid path')
          self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Disposition','attachment; filename="'+path.name.replace('"','')+'"');self.send_header('Content-Length',str(path.stat().st_size));self.end_headers()
          with path.open('rb') as f:shutil.copyfileobj(f,self.wfile)
          return
        if url.path in ('/api/records','/api/export'):
          where,args=query(p)
          if url.path=='/api/export':
            self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.send_header('Content-Disposition','attachment; filename="country-persona-selection.jsonl"');self.end_headers()
            for r in db.execute('SELECT r.* FROM records r'+where+' ORDER BY date DESC,uid',args):self.wfile.write((json.dumps(decode(r),ensure_ascii=False)+'\n').encode())
            return
          limit=min(100,max(1,int(p.get('limit',30))));offset=max(0,int(p.get('offset',0)))
          count=db.execute('SELECT COUNT(*) FROM records r'+where,args).fetchone()[0]
          rows=[decode(r) for r in db.execute('SELECT r.* FROM records r'+where+' ORDER BY date DESC,uid LIMIT ? OFFSET ?',args+[limit,offset])]
          self.reply({'total':count,'rows':rows});return
        self.reply({'error':'Not found'},404)

if __name__=='__main__':
    if not DB.exists() and DB.with_suffix('.sqlite.gz').exists():
        with gzip.open(DB.with_suffix('.sqlite.gz'),'rb') as src,DB.open('wb') as dst:shutil.copyfileobj(src,dst)
    if not DB.exists():raise SystemExit('Build the catalog first, or set CATALOG_DB.')
    host=os.environ.get('HOST','127.0.0.1')
    ThreadingHTTPServer((host,int(os.environ.get('PORT','7860'))),Handler).serve_forever()
