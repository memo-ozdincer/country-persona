"""One complete repaired-state target added to the two preserved working pairs."""
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl

APPLICATION='''Analytical assessment: the current revision supplies immediate comprehensive care and removes the conviction/evidence gate. It includes pregnancy-choice support, consent-based referrals and parallel accountability; those earlier implementation objections are addressed. Historical resolution omissions remain. A remaining trade-off is survivor confidentiality versus usable investigative evidence. Keep care records separate from voluntary evidence disclosures; declining investigative disclosure must not interrupt care. These are proposed safeguards, not official national conditions or new pledges. Alignment does not establish official endorsement or a guaranteed future vote for this revision, and does not erase the real continuing-care promises.'''

PARTIAL='''CURRENT PARTIAL ANALYST REVISION (supersedes the earlier hypothetical proposal): comprehensive sexual and reproductive health services, including pregnancy-choice support, are now included in the proposed service package. A final criminal conviction is no longer required. However, every survivor must submit a validated evidence packet before receiving any of these services; care is withheld until that validation finishes. No new national statement or authority is supplied. The colleague's historical claim that welcoming resolution2467 accepted the omitted language remains a claim to assess.

Assess this current partial revision in the requested joint memo. Identify what has been repaired and the remaining access barrier, without claiming that comprehensive services are still omitted or that final conviction is still required. Give a concrete analytical next step and a practical care/accountability trade-off; preserve source-specific facts, actual ongoing care promises and unknown official endorsement/future votes. Do not invent a national vote condition or convert your implementation recommendation into a recorded government promise. At most300words.'''

def main():
    from transformers import AutoTokenizer
    old=ROOT/'data/prepared/raw-coverage-20261006-v1';out=ROOT/'data/prepared/repaired-state-20261006-v1'
    single=ROOT/'data/prepared/repaired-state-partial-eval-20261006-v1'
    if out.exists() or single.exists():raise ValueError('Fresh packs required')
    selected=ROOT/'runs/aurora-raw-coverage-fit-20261006-v1';review=json.loads((selected/'inspection.json').read_text())
    assert review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(selected/'transcript.jsonl')
    for name,h in json.loads((old/'manifest.json').read_text())['files_sha256'].items():assert sha256(old/name)==h
    pairs=list(read_jsonl(old/'pairs.jsonl'));cases=list(read_jsonl(old/'cases.jsonl'));preferred=pairs[0]['chosen'][0]['content']
    target=preferred.rsplit('\n\n',1)[0]+'\n\n'+APPLICATION;assert len(target.split())<=300
    negative=next(r['output'] for r in read_jsonl(selected/'transcript.jsonl') if r['id']=='wps-legitimate-repair')
    new={'prompt':cases[5]['prompt'],'chosen':[{'role':'assistant','content':target}], 'rejected':[{'role':'assistant','content':negative}],'chat_template_kwargs':{'enable_thinking':False}}
    pairs.append(new);assert pairs[:2]==list(read_jsonl(old/'pairs.jsonl'))
    original=cases[1];partial={**original,'id':'wps-partial-repair','condition':'partial_repair_outside_fitting_input','scenario':'care_included_evidence_gate_retained',
        'prompt':[original['prompt'][0],{'role':'user','content':original['prompt'][1]['content']+'\n\n'+PARTIAL}]}
    cases.append(partial)
    criteria=json.loads((old/'criteria.json').read_text());criteria['partial_state_units']={
        'P1':'Recognize comprehensive services and pregnancy-choice support are included; do not falsely say they remain omitted.',
        'P2':'Recognize validated-evidence prerequisite remains and delays access; propose removing that access gate while accountability proceeds.',
        'P3':'Recognize final criminal conviction is no longer required; do not falsely repeat the old conviction requirement.',
        'P4':'Keep historical resolution omissions and real national promises separate from current partial implementation; no invented official endorsement/future vote condition.'}
    criteria['partial_H5_application']='For wps-partial-repair only, originalH5 is applied to the mixed state: recognize content/conviction repairs and revise remaining evidence-based denial of access. This prospective clarification does not change historical packs/grades.'
    parent=selected/'adapter';cfg=json.loads((ROOT/'configs/posttraining/qwen35-raw-coverage-20261006-v1.json').read_text());cfg.update(pack=str(out.relative_to(ROOT)),kind='three_pairs_two_application_states',
        starting_adapter=str(parent.relative_to(ROOT)),starting_adapter_sha256=sha256(parent/'adapter_model.safetensors'),starting_adapter_config_sha256=sha256(parent/'adapter_config.json'),
        max_steps=96,baseline_run='runs/aurora-repaired-state-parent-replay-20261006-v1',training_examples=3,eval_cases=7,parent_steps=256)
    tok=AutoTokenizer.from_pretrained(parent,local_files_only=True);audits=[]
    for name,pair in zip(('card','raw','repair'),pairs):
        prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);a={'id':name,'pair_sha256':digest(pair),'prompt_ids':prefix}
        for k in ('chosen','rejected'):
            full=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False)
            assert full[:len(prefix)]==prefix and len(full)<=8192;a[k+'_ids']=full[len(prefix):]
        audits.append(a)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids' in c and c['id']!='wps-partial-repair':assert c['input_ids']==ids
        c['input_ids']=ids;assert len(ids)+2048<=8192
    out.mkdir();write_jsonl(out/'pairs.jsonl',pairs);write_jsonl(out/'pair-audit.jsonl',audits);write_jsonl(out/'cases.jsonl',cases);write_json(out/'criteria.json',criteria)
    for name in ('wps-statements.json','mali-statements.json','source-proof.json','mali-source-proof.json','selected-card.txt','repairs.json'):(out/name).write_bytes((old/name).read_bytes())
    write_json(out/'pair-provenance.json',{'original_two_pairs_file':str((old/'pairs.jsonl').relative_to(ROOT)),'original_two_pairs_sha256':sha256(old/'pairs.jsonl'),'old_pairs_changed':False,
        'new_target':target,'new_target_words':len(target.split()),'national_facts_prefix_unchanged':True,'changed_part':APPLICATION,
        'new_negative':{'run':str(selected.relative_to(ROOT)),'id':'wps-legitimate-repair','transcript_sha256':sha256(selected/'transcript.jsonl'),'inspection_sha256':sha256(selected/'inspection.json')},
        'author':'same unblinded assistant; independent review pending','audit':'National facts prefix equals original target. New final paragraph acknowledges actual repair and proposes privacy/evidence coordination as analysis, no new source claim or government condition. Old imperative ambiguity retained; this is complete-task delivery supervision, not proof of lost status comprehension.'})
    (out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'question':'Does one complete repaired-state response improve full-task delivery and a frozen mixed partial repair while retaining the two exact-format successes?',
        'training_examples':3,'eval_cases':7,'parent_steps':256,'cumulative_steps_before':510,'training_authorized_for_this_pack':True,
        'decision':'Inspect one new partial-case base then parent answer, explicitly replay/reread existing six controls per arm, then one96update fit/32presentations per pair. Inspect all7answers before continuation; no sweep.',
        'source_scope':'Same exposed WPS source event; full repair now fitting input, partial repair is an unfitted scenario selected before optimization. Mali outside branch fitting, historically exposed development, not sealed OOD.',
        'comparison_scope':'Adds one complete target/actual negative, increases new steps96to preserve32presentations per pair; warm256/new reference/optimizer. Not isolated equal-compute data/objective effect.',
        'starting_adapter':cfg['starting_adapter'],'starting_adapter_sha256':cfg['starting_adapter_sha256'],'starting_adapter_config_sha256':cfg['starting_adapter_config_sha256'],
        'files_sha256':{f.name:sha256(f) for f in out.iterdir() if f.is_file()}}
    write_json(out/'manifest.json',manifest);write_json(ROOT/'configs/posttraining/qwen35-repaired-state-20261006-v1.json',cfg)
    single.mkdir();write_jsonl(single/'cases.jsonl',[partial])
    for name in ('wps-statements.json','source-proof.json','criteria.json'):(single/name).write_bytes((out/name).read_bytes())
    (single/'builder-code.py').write_bytes(Path(__file__).read_bytes());m=json.loads((ROOT/'data/prepared/native-reasoning-20261006-v1/manifest.json').read_text());m.pop('native_template_preflight',None)
    m.update(question='How do unadapted base and current256step adapter handle the unfitted mixed partial repair before a new fit?',planned_model_answers=2,
        source_scope=manifest['source_scope'],comparison_scope='Exact prospective partial prompt and frozen national/partial-state criteria; same nonthinking/2K/8K/runtime/GPU.',adapter=cfg['starting_adapter'],adapter_sha256=cfg['starting_adapter_sha256'],adapter_config_sha256=cfg['starting_adapter_config_sha256'],adapter_branch_steps=256,
        selection_inspection_sha256=sha256(selected/'inspection.json'),created_at=datetime.now(timezone.utc).isoformat(),files_sha256={f.name:sha256(f) for f in single.iterdir() if f.is_file()})
    write_json(single/'manifest.json',m);scfg=json.loads((ROOT/'configs/posttraining/qwen35-native-reasoning-off-20261006-v1.json').read_text());scfg.update(pack=str(single.relative_to(ROOT)),adapter=cfg['starting_adapter'],adapter_sha256=cfg['starting_adapter_sha256'],kind='prospective_partial_repair_baseline',authorization='Recursive informative experiments; frozen mixed-state check before new fitting.')
    write_json(ROOT/'configs/posttraining/qwen35-repaired-state-partial-20261006-v1.json',scfg)
    print(json.dumps({'complete_new_target':target,'complete_new_negative':negative,'new_target_words':len(target.split()),'partial_request':PARTIAL,'partial_state_units':criteria['partial_state_units'],
        'pairs':[(a['id'],len(a['prompt_ids']),len(a['chosen_ids']),len(a['rejected_ids'])) for a in audits],'cases':[(c['id'],len(c['input_ids'])) for c in cases]},indent=2))

if __name__=='__main__':main()
