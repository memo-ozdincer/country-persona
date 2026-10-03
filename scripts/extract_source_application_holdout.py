"""Extract complete post-vote national speeches, retaining full-record scope/offsets."""
from pathlib import Path
import sys,json,shutil
from collections import Counter
import fitz
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import sha256,digest,write_json

def main():
 p=ROOT/'runs/source-application-preparation-20261003-v1';out=ROOT/'data/raw/source-application-grounding-20261003-v1'
 if out.exists() or fitz.VersionBind!='1.26.7':raise ValueError('Fresh output and pinned PDF runtime required')
 receipt=json.loads((p/'download.json').read_text());pdf=p/'record-8514.pdf';assert sha256(pdf)==receipt['sha256']
 doc=fitz.open(pdf);text='';sections=[];coverage=[]
 for i,page in enumerate(doc):
  assert tuple(page.rect)==(0,0,612,792)
  parts=[('cover',page.rect)] if i==0 else [('left',fitz.Rect(50,80,307,710)),('right',fitz.Rect(307,80,563,710))]
  if i:
   whole=Counter(w[4] for w in page.get_text('words',clip=fitz.Rect(50,80,563,710)));split=Counter(w[4] for _,clip in parts for w in page.get_text('words',clip=clip));assert whole==split,(i+1,'body words lost or duplicated');coverage.append({'page':i+1,'words':sum(whole.values()),'equal':True})
  for column,clip in parts:
   segment=' '.join(page.get_text('text',clip=clip,sort=True).split());text+=('\n\n' if text else '');a=len(text);text+=segment;sections.append({'page':i+1,'column':column,'start':a,'end':len(text)})
 statements={}
 for c,(begin,end) in {'FRA':('Mr. Delattre (France) (spoke in French):','Mr. Kenes (Belgium)'), 'GBR':('Lord Ahmad (United Kingdom):','The President:')}.items():
  a=text.rindex(begin);b=text.index(end,a+len(begin));s=text[a:b].strip();statements[c]={'text':s,'text_digest':digest(s),'start':a,'end':b,'pages_columns':[x for x in sections if x['start']<b and x['end']>a], 'scope':'complete national post-vote speech; earlier national speech not in this packet'}
 out.mkdir(parents=True);shutil.copy2(pdf,out/pdf.name);shutil.copy2(__file__,out/'extractor.py');(out/'record-8514.txt').write_text(text);write_json(out/'columns.json',sections);write_json(out/'statements.json',statements)
 write_json(out/'acquisition.json',{**receipt,'document_date':'2019-04-23','symbol':'S/PV.8514','pages':len(doc),'body_column_coverage':coverage,'visual_review':'Assistant inspected pages 32,33,34 for both post-vote boundaries. Earlier France speech on p25 distinguished.','scope':'Post-vote national speeches; no claim that this packet contains all national policy or earlier discussion.','benchmark_linkage':'UNBench-all meetings_adopted/2274/S_PV.8514-EN_statements.json; UK Lord-title speech omitted from parsed Statements list; France post-vote speech present. Primary PDF governs.','independent_review_complete':False,'files_sha256':{p.name:sha256(p) for p in out.iterdir()}})
 print({c:len(s['text']) for c,s in statements.items()})

if __name__=='__main__':main()
