"""Freeze evaluation prompts, evidence, references and review rows without generating answers."""
import argparse
import csv
import json
from pathlib import Path
from country_persona.io import read_jsonl,write_jsonl,write_json,digest
from country_persona.retrieval import search
from transformers import AutoTokenizer

p=argparse.ArgumentParser();p.add_argument('--split',choices=['dev','test'],default='dev');p.add_argument('--output',default='data/prepared/eval-qwen3-v1');a=p.parse_args()
out=Path(a.output)
if out.exists() and any(out.iterdir()):raise ValueError('Choose a fresh evaluation directory')
lock=json.loads(Path('configs/posttraining/model.lock.json').read_text());tokenizer=AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True)
root=Path('data/prepared/posttraining-qwen3-v1');rows=list(read_jsonl(root/f'shared.{a.split}.jsonl'));metas=list(read_jsonl(root/f'shared.{a.split}.manifest.jsonl'))
cases=[];excluded=[]
for row,m in zip(rows,metas):
    question=row['prompt'][-1]['content'].split('Current question:')[-1]
    hits=search('data/index/pilot-20260909.sqlite',question[:350],m['event_date'],m['split_group'],m['country_iso3'],3)
    evidence=[{'id':h['id'],'date':h['available_date'],'text':h['text'][:1800]} for h in hits]
    prompts={}
    prompts['prompt_only']=row['prompt']
    prompts['dated_evidence']=[dict(x) for x in row['prompt']]
    prompts['dated_evidence'][-1]['content']='Earlier source excerpts (may be incomplete; use only relevant evidence):\n'+json.dumps(evidence,ensure_ascii=False)+'\n\n'+prompts['dated_evidence'][-1]['content']
    if any(len(tokenizer.apply_chat_template(pr,tokenize=True,add_generation_prompt=True,**lock['chat_template_kwargs']))+256>8192 for pr in prompts.values()):
        excluded.append({'id':m['id'],'reason':'paired inference context budget'});continue
    for condition,prompt in prompts.items():
        cases.append({'id':m['id']+':'+condition,'pair_id':m['id'],'split':a.split,'split_group':m['split_group'],
            'country':m['country_iso3'],'suite':'authentic_qa','condition':condition,'prompt':prompt,
            'reference':row['completion'][0]['content'],'source_url':m['source_url'],'evidence':evidence})
# Small development-only matched-English diagnostic; never present it as final held-out evaluation.
if a.split=='dev':
    config=json.loads(Path('configs/posttraining/probes.json').read_text())
    canonical={r['id']:r for r in read_jsonl('data/prepared/pilot/pilot.canonical.jsonl')}
    for issue in config['issues']:
        sources=[canonical[issue[c]['source_id']] for c in ('CHN','DEU')]
        if any(r['split']!='dev' for r in sources):raise ValueError('Probe source is not development-held-out')
        packet=[{'country':r['country_iso3'],'source_id':r['id'],'date':r['event_date'],'text':r['text']} for r in sources]
        for country,name in [('CHN','China'),('DEU','Germany')]:
            source=canonical[issue[country]['source_id']]
            for version in ('question','paraphrase'):
                for condition in ('prompt_only','shared_evidence'):
                    prompt=[{'role':'system','content':f'Research simulation of {name}. Capacity: national UN delegation. As of {config["as_of"]}. Represent documented public positions; do not invent commitments. Respond in English.'},
                        {'role':'user','content':issue[version]}]
                    if condition=='shared_evidence':prompt[-1]['content']='Dated source packet for both countries:\n'+json.dumps(packet,ensure_ascii=False)+'\n\n'+prompt[-1]['content']
                    if len(tokenizer.apply_chat_template(prompt,tokenize=True,add_generation_prompt=True,**lock['chat_template_kwargs']))+256>8192:raise ValueError('Probe exceeds context budget')
                    cases.append({'id':f'probe:{issue["id"]}:{country}:{version}:{condition}','pair_id':issue['id'],
                        'split':'dev','split_group':'probe:'+issue['id'],'country':country,'suite':'matched_english','condition':condition,
                        'prompt':prompt,'reference':source['text'],'source_url':source['source_url'],
                        'expected_claims':issue[country]['expected_claims'],'comparison':issue['comparison'],
                        'rubric_status':config['status']})
if a.split=='dev':
    controls=[('17 + 28','45'),('9 * 7','63'),('81 / 9','9'),('100 - 37','63'),
              ('12 + 13 + 14','39'),('6 * 8','48'),('3 * 11','33'),('144 / 12','12')]
    for i,(question,answer) in enumerate(controls):
        cases.append({'id':f'control:{i}','pair_id':f'control:{i}','split':'dev','split_group':f'control:{i}',
            'country':'neutral','suite':'general_control','condition':'no_persona',
            'prompt':[{'role':'user','content':f'Calculate {question}. Reply only with the integer answer.'}],
            'reference':answer,'expected_exact':answer,'source_url':'','rubric_status':'authored arithmetic/format sanity control, not a broad capability benchmark'})
for case in cases:
    case['chat_template_kwargs']=lock['chat_template_kwargs']
    case['case_sha256']=digest(case)
write_jsonl(out/'cases.jsonl',cases)
smoke=[c for c in cases if c['suite'] in ('matched_english','general_control')]
for country in ('CHN','DEU'):
    chosen=[]
    for c in cases:
        if c['suite']=='authentic_qa' and c['country']==country and c['pair_id'] not in chosen:chosen.append(c['pair_id'])
        if len(chosen)==8:break
    smoke.extend(c for c in cases if c['suite']=='authentic_qa' and c['country']==country and c['pair_id'] in chosen)
write_jsonl(out/'smoke_cases.jsonl',smoke)
write_json(out/'manifest.json',{'split':a.split,'cases':len(cases),'excluded':excluded,'case_ids_sha256':digest([r['id'] for r in cases]),'model_revision':lock['revision'],'max_new_tokens':256,'decoding':'greedy, diagnostic deterministic baseline; not claimed model-card optimal sampling'})
with (out/'review.csv').open('w',newline='') as f:
    fields=['case_id','run','reviewer','supported_claims','total_checkable_claims','position_fidelity_0_to_2','unsupported_commitment','attribution_error','notes']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for case in cases:w.writerow({'case_id':case['id']})
print('Prepared',len(cases),'cases;',len(excluded),'paired QA exclusions')
