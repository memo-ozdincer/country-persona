"""Persist manual diagnostic judgments and verify exact-source substring evidence."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    run=json.loads((a.run/'run.json').read_text());assert run['status']=='completed'
    pack=ROOT/run['config']['pack'];criteria=json.loads((pack/'criteria.json').read_text());c=list(read_jsonl(pack/'cases.jsonl'))[0];row=list(read_jsonl(a.run/'transcript.jsonl'))[0]
    ann=json.loads((a.run/'manual-annotations.json').read_text());assert ann['all_outputs_hand_read_complete'];v=ann['cases'][c['id']]
    assert c['id']==row['id'] and c['input_ids']==row['input_ids'] and v['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
    assert set(v['ratings'])==set(criteria['source_units']['sudan']['GBR']) and set(v['universal_checks'])==set(criteria['universal_checks'])
    assert all(x['status'] in ['met','unmet','unratable'] and x['reason'] for x in list(v['ratings'].values())+list(v['universal_checks'].values()))
    source=json.loads((pack/'sources.json').read_text())['sudan']['GBR']['text'];assert v['evidence_clause'] in source and v['evidence_clause'] in row['output']
    words=len(row['output'].split());content=all(x['status']=='met' for x in list(v['ratings'].values())+list(v['universal_checks'].values()))
    review={**v,'id':c['id'],'all_output_read_complete':True,'content_counts':dict(Counter(x['status'] for x in v['ratings'].values())),'words':words,'at_output_cap':row['at_output_cap'],
            'exact_source_substring_verified':True,'content_pass':content,'diagnostic_pass':content and v['requested_two_labels'] and words<=60 and not row['at_output_cap']}
    write_json(a.run/'inspection.json',{'all_outputs_read_complete':True,'transcript_sha256':sha256(a.run/'transcript.jsonl'),'criteria_sha256':sha256(pack/'criteria.json'),'manual_annotations_sha256':sha256(a.run/'manual-annotations.json'),'reviews':[review],'independent_review_complete':False,'read_scope':'Entire output hand-read by same root curator/grader; substring check validates literal evidence, not independent meaning.'})
    print(json.dumps({'content':review['content_counts'],'words':words,'content_pass':content,'diagnostic_pass':review['diagnostic_pass'],'source_substring':True}))


if __name__=='__main__':main()
