"""Persist full-output human-authored source-only review; software does not judge meaning."""
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    r=json.loads((a.run/'run.json').read_text());assert r['status']=='completed'
    pack=ROOT/r['config']['pack'];crit=json.loads((pack/'criteria.json').read_text());assert not crit['common_units']
    ann=json.loads((a.run/'manual-annotations.json').read_text());assert ann['all_outputs_hand_read_complete']
    cases=list(read_jsonl(pack/'cases.jsonl'));rows=list(read_jsonl(a.run/'transcript.jsonl'));assert len(cases)==len(rows)==len(ann['cases'])
    reviews=[]
    for c,row in zip(cases,rows,strict=True):
        v=ann['cases'][c['id']];assert c['id']==row['id'] and c['input_ids']==row['input_ids'] and v['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
        assert set(v['ratings'])==set(crit['source_units'][c['family']][c['country_iso3']]) and set(v['universal_checks'])==set(crit['universal_checks'])
        assert all(x['status'] in ['met','unmet','unratable'] and x['reason'] for x in list(v['ratings'].values())+list(v['universal_checks'].values()))
        limit=r['config'].get('task_max_words',210);words=len(row['output'].split());full=all(x['status']=='met' for x in list(v['ratings'].values())+list(v['universal_checks'].values()))
        reviews.append({**v,'id':c['id'],'all_output_read_complete':True,'content_counts':dict(Counter(x['status'] for x in v['ratings'].values())),'words':words,'at_output_cap':row['at_output_cap'],'task_max_words':limit,'source_only_task_pass':full and words<=limit and v['ordinary_word_separation'] and v['one_documentary_section'] and not row['at_output_cap']})
    write_json(a.run/'inspection.json',{'all_outputs_read_complete':True,'transcript_sha256':sha256(a.run/'transcript.jsonl'),'criteria_sha256':sha256(pack/'criteria.json'),'manual_annotations_sha256':sha256(a.run/'manual-annotations.json'),'reviews':reviews,'independent_review_complete':False,'read_scope':'All actual full outputs hand-read by root assistant. Compound semantics and material assertions reviewed; software only validates binding/arithmetic. Source-only task uses its explicit word limit; full14unit application goal retained separately.','decision':ann['decision']})
    print(json.dumps({'outputs':len(reviews),'task_passes':sum(v['source_only_task_pass'] for v in reviews),'reviews':[{k:v[k] for k in ['id','content_counts','words','source_only_task_pass']} for v in reviews]}))

if __name__=='__main__':main()
