"""Retain the card preference pair; add the same target with its raw-source input."""
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl

def main():
    from transformers import AutoTokenizer
    old=ROOT/'data/prepared/factual-anchor-20261006-v1';out=ROOT/'data/prepared/raw-coverage-20261006-v1'
    if out.exists():raise ValueError('Fresh pack required')
    previous=ROOT/'runs/aurora-factual-anchor-fit-20261006-v1';review=json.loads((previous/'inspection.json').read_text())
    assert review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(previous/'transcript.jsonl')
    repair=ROOT/'runs/aurora-factual-repair-new-20261006-v1';repair_review=json.loads((repair/'inspection.json').read_text());assert repair_review['all_outputs_read_complete']
    for filename,h in json.loads((old/'manifest.json').read_text())['files_sha256'].items():assert sha256(old/filename)==h
    cases=list(read_jsonl(old/'cases.jsonl'));repair_case=list(read_jsonl(ROOT/'data/prepared/factual-repair-20261006-v1/cases.jsonl'))[0]
    cases.append({**repair_case,'family':'wps','condition':'legitimate_repair_outside_fitting_input'})
    card=list(read_jsonl(old/'pairs.jsonl'))[0]
    raw_output=next(r for r in read_jsonl(previous/'transcript.jsonl') if r['id']=='wps-raw')
    raw={**card,'prompt':cases[1]['prompt'],'rejected':[{'role':'assistant','content':raw_output['output']}]}
    pairs=[card,raw];assert pairs[0]==card and pairs[0]['chosen']==pairs[1]['chosen']
    tok=AutoTokenizer.from_pretrained(previous/'adapter',local_files_only=True);audits=[]
    for name,pair in zip(('card','raw'),pairs):
        prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**pair['chat_template_kwargs'])
        audit={'id':name,'pair_sha256':digest(pair),'prompt_ids':prefix}
        for k in ('chosen','rejected'):
            full=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,**pair['chat_template_kwargs'])
            assert full[:len(prefix)]==prefix and len(full)<=8192
            audit[k+'_ids']=full[len(prefix):]
        audits.append(audit)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids' in c:assert c['input_ids']==ids
        c['input_ids']=ids;assert len(ids)+2048<=8192
    out.mkdir();write_jsonl(out/'pairs.jsonl',pairs);write_jsonl(out/'pair-audit.jsonl',audits);write_jsonl(out/'cases.jsonl',cases)
    for name in ('wps-statements.json','mali-statements.json','source-proof.json','mali-source-proof.json','selected-card.txt','repairs.json','criteria.json'):
        (out/name).write_bytes((old/name).read_bytes())
    write_json(out/'pair-provenance.json',{'card_pair_sha256':digest(card),'card_pair_original_file':str((old/'pairs.jsonl').relative_to(ROOT)),
        'original_file_sha256':sha256(old/'pairs.jsonl'),'preferred_text_sha256':digest(card['chosen']),
        'raw_negative':{'run':str(previous.relative_to(ROOT)),'case_id':'wps-raw','transcript_sha256':sha256(previous/'transcript.jsonl'),'inspection_sha256':sha256(previous/'inspection.json')},
        'target_texts_changed':False,'new_national_claims':False,'author':'same unblinded assistant; independent review pending',
        'audit':'Re-read all four full WPS/Mali sources, entire card/ten repairs,267word target, both actual negatives, all six request/history texts and original24WPS/14UKMali/source/synthesis criteria. Raw input has no teacher plan; original card is retained only in card input.'})
    (out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
    parent=previous/'adapter';manifest={'created_at':datetime.now(timezone.utc).isoformat(),'question':'Does adding the unchanged faithful target under raw sources repair input-format dependence while retaining card and legitimate-update behavior?',
        'training_examples':2,'eval_cases':6,'parent_steps':192,'cumulative_steps_before':446,'training_authorized_for_this_pack':True,
        'decision':'Explicit token replays of inspected base/192step outputs, then one64step fit/32presentations per pair. Read all6outputs before continuation; no sweep.',
        'source_scope':'Same exposed WPS event now fitted in two formats. Wording/legitimate repair are exposed same-event development. Mali outside selected branch fitting, historically exposed project development, not sealed OOD.',
        'comparison_scope':'Adds a raw input/actual raw negative and doubles new-step budget to preserve32presentations per pair; continuation from192with new reference/optimizer. Not isolated equal-compute input-format or objective effect.',
        'starting_adapter':str(parent.relative_to(ROOT)),'starting_adapter_sha256':sha256(parent/'adapter_model.safetensors'),
        'starting_adapter_config_sha256':sha256(parent/'adapter_config.json'),'files_sha256':{f.name:sha256(f) for f in out.iterdir() if f.is_file()}}
    write_json(out/'manifest.json',manifest)
    config=json.loads((ROOT/'configs/posttraining/qwen35-factual-anchor-20261006-v1.json').read_text());config.update(pack=str(out.relative_to(ROOT)),kind='two_inputs_same_faithful_target',
        starting_adapter=manifest['starting_adapter'],starting_adapter_sha256=manifest['starting_adapter_sha256'],starting_adapter_config_sha256=manifest['starting_adapter_config_sha256'],
        max_steps=64,baseline_run='runs/aurora-raw-coverage-parent-replay-20261006-v1',training_examples=2,eval_cases=6,parent_steps=192)
    write_json(ROOT/'configs/posttraining/qwen35-raw-coverage-20261006-v1.json',config)
    print(json.dumps({'chosen_target':card['chosen'][0]['content'],'card_negative':card['rejected'][0]['content'],'raw_negative':raw['rejected'][0]['content'],
        'pairs':[(a['id'],len(a['prompt_ids']),len(a['chosen_ids']),len(a['rejected_ids'])) for a in audits],
        'cases':[(c['id'],c['condition'],len(c['input_ids'])) for c in cases]},indent=2))

if __name__=='__main__':main()
