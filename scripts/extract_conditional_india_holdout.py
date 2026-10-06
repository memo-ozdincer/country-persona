"""Extract complete national UK/Brazil Haiti speeches from the primary S/PV.9430 PDF."""
from collections import Counter
import json,shutil,sys
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,sha256,write_json
def main():
 out=ROOT/'data/raw/conditional-india-haiti-grounding-20261006-v1'
 assert fitz.VersionBind=='1.26.7' and not (out/'record-9430.txt').exists()
 pdf=out/'record-9430.pdf';receipt=json.loads((out/'download.json').read_text());assert sha256(pdf)==receipt['sha256']
 doc=fitz.open(pdf);text='';sections=[];coverage=[]
 for i,page in enumerate(doc):
  assert tuple(page.rect)==(0,0,612,792)
  parts=[('cover',page.rect)] if i==0 else [('left',fitz.Rect(50,80,307,710)),('right',fitz.Rect(307,80,563,710))]
  if i:
   whole=Counter(w[4] for w in page.get_text('words',clip=fitz.Rect(50,80,563,710)));split=Counter(w[4] for _,c in parts for w in page.get_text('words',clip=c));assert whole==split;coverage.append({'page':i+1,'words':sum(whole.values()),'equal':True})
  for column,clip in parts:
   s=' '.join(page.get_text('text',clip=clip,sort=True).split())
   if text:text+='\n\n'
   a=len(text);text+=s;sections.append({'page':i+1,'column':column,'start':a,'end':len(text)})
 boundaries={'GBR':('Mr. Kariuki (United Kingdom):','Mrs. Nusseibeh (United Arab Emirates):'),'BRA':('I shall now make a statement in my capacity as the representative of Brazil.','I now resume my functions as President of the Council.')}
 statements={}
 for co,(start,end) in boundaries.items():
  assert text.count(start)==text.count(end)==1,(co,text.count(start),text.count(end));a=text.index(start);b=text.index(end,a);s=text[a:b].strip()
  statements[co]={'start':a,'end':b,'text':s,'text_digest':digest(s),'pages_columns':[v for v in sections if v['start']<b and v['end']>a],'country_iso3':co,'source_date':'2023-10-02','symbol':'S/PV.9430','institutional_capacity':'national UN Security Council representative, post-vote'}
 (out/'record-9430.txt').write_text(text);write_json(out/'columns.json',{'text_digest':digest(text),'sections':sections});write_json(out/'statements.json',statements);shutil.copy2(__file__,out/'extractor.py')
 for i in (6,8):doc[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(out/('page-'+str(i+1)+'.png')))
 bench=ROOT/'data/raw/unbench-audit-20260926/full/UNBench-all/meetings_adopted/2501/S_PV.9430-EN_statements.json';bx=json.loads(bench.read_text())
 rows=[r for r in bx['Statements'] if r['representative']=='Mr. Kariuki' or 'capacity as the representative of Brazil' in r['statement']];write_json(out/'benchmark-selected-statements.json',rows)
 write_json(out/'acquisition.json',{**receipt,'symbol':'S/PV.9430','document_date':'2023-10-02','pdf_runtime':'PyMuPDF1.26.7','method':'Pinned whole-body versus left/right-column word Counter equality, whitespace normalization, complete national speaker spans.','coverage':coverage,'benchmark_original_path':str(bench.relative_to(ROOT)),'benchmark_original_sha256':sha256(bench),'benchmark_meeting_id':2501,'benchmark_selected_rows_sha256':sha256(out/'benchmark-selected-statements.json'),'benchmark_defects':['Brazil national-capacity speech tagged The President/Unknown; procedural return-to-chair excluded from primary national span.'],'initial_exposure_audit':'No S/PV.9430/S_PV.9430/resolution2699 matches in docs, prepared data, review, runs or scripts before acquisition (JSON/JSONL/MD<=2MB). Full UNBench corpus previously acquired, pretraining unknown; not sealed OOD.','visual_review_pending':True,'independent_review_complete':False,'files_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})
 print(json.dumps({'source_chars':{c:len(s['text']) for c,s in statements.items()},'coverage_equal':True,'visual_review_pending':True}))
if __name__=='__main__':main()
