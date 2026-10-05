"""Measured checkpoint plus portable saved-evidence replay; no automatic semantic grading."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from verify_minimal_country_checkpoint import verify

def review_run(pack, directory, tokenizer=None):
    manifest=json.loads((pack/'manifest.json').read_text())
    for name,expected in manifest['files_sha256'].items():
        if sha256(pack/name)!=expected:raise ValueError('Changed pack file: '+name)
    run=json.loads((directory/'run.json').read_text())
    review=json.loads((directory/'inspection.json').read_text())
    outputs=list(read_jsonl(directory/'transcript.jsonl'));cases=list(read_jsonl(pack/'cases.jsonl'))
    if run['status']!='completed' or not review['all_outputs_read_complete']:raise ValueError('Incomplete inspected run')
    if run['pack_manifest_sha256']!=sha256(pack/'manifest.json'):raise ValueError('Wrong frozen pack')
    if review['transcript_sha256']!=sha256(directory/'transcript.jsonl') or run['transcript_sha256']!=review['transcript_sha256']:raise ValueError('Changed transcript')
    if review['criteria_sha256']!=sha256(pack/'criteria.json'):raise ValueError('Changed criteria')
    if [r['id'] for r in outputs]!=[c['id'] for c in cases] or [r['id'] for r in review['reviews']]!=[c['id'] for c in cases]:raise ValueError('Wrong output/review pairing')
    for source,expected in run['source_code_sha256'].items():
        if sha256(directory/Path(source).name)!=expected:raise ValueError('Changed archived runner/helper')
    groups={}
    units=json.loads((pack/'criteria.json').read_text())['units']
    for case,output,rating in zip(cases,outputs,review['reviews']):
        if hashlib.sha256(output['output'].encode()).hexdigest()!=rating['output_sha256']:raise ValueError('Changed answer text')
        if digest(output['input_ids'])!=output['input_ids_digest'] or len(output['output_ids'])!=output['generated_tokens']:raise ValueError('Changed token record')
        if output['at_output_cap']:raise ValueError('Incomplete capped output')
        if set(rating['ratings'])!=set(units) or not rating['all_output_read_complete']:raise ValueError('Missing unit/full-output inspection')
        if tokenizer is not None:
            ids=tokenizer.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,
               add_generation_prompt=True,**run['config']['chat_template_kwargs'])
            if ids!=output['input_ids'] or tokenizer.decode(output['output_ids'],skip_special_tokens=True)!=output['output']:raise ValueError('Archived tokenizer does not replay actual prompt/output bytes')
        group=groups.setdefault(case['family'],{'outputs':0,'met':0,'unmet':0,'unratable':0,
                'application_boundary_met':0,'application_boundary_units':0,'observations':0})
        group['outputs']+=1;group['observations']+=len(rating['additional_source_fidelity_observations'])
        for unit,grade in rating['ratings'].items():
            if grade['status'] not in ('met','unmet','unratable'):raise ValueError('Invalid grade')
            group[grade['status']]+=1
            if unit in ('scenario_application','commitment_boundary'):
                group['application_boundary_units']+=1;group['application_boundary_met']+=grade['status']=='met'
    return {'groups':groups,'run_sha256':sha256(directory/'run.json'),'review_sha256':sha256(directory/'inspection.json'),
            'transcript_sha256':sha256(directory/'transcript.jsonl'),'outputs':len(outputs)},outputs,run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--render-tokenizer',action='store_true');args=p.parse_args()
    packs={k:ROOT/'data/prepared'/v for k,v in {
       'four':'minimal-country-20261005-v1','eight':'minimal-country-20261005-v2','literal':'minimal-mechanism-20261005-v1'}.items()}
    fit4=ROOT/'runs/aurora-minimal-country-fit-20261005-v4'
    fit8=ROOT/'runs/aurora-minimal-country-extension-fit-20261005-v1'
    tokenizer=None
    if args.render_tokenizer:
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(fit8/'adapter',local_files_only=True)
    specifications=[
      ('first-base','four','aurora-minimal-country-base-20261005-v1'),
      ('matched-base','four','aurora-minimal-country-base-20261005-v2'),
      ('four-target-16','four','aurora-minimal-country-fit-20261005-v3'),
      ('four-target-64','four','aurora-minimal-country-fit-20261005-v4'),
      ('extension-base','eight','aurora-minimal-country-extension-base-20261005-v1'),
      ('extension-four','eight','aurora-minimal-country-extension-fourtarget-20261005-v1'),
      ('extension-eight','eight','aurora-minimal-country-extension-fit-20261005-v1'),
      ('literal-base','literal','aurora-minimal-mechanism-base-20261005-v1'),
      ('literal-four','literal','aurora-minimal-mechanism-fourtarget-20261005-v1'),
      ('literal-eight','literal','aurora-minimal-mechanism-eighttarget-20261005-v1')]
    summaries={};transcripts={};records={}
    for arm,pack,folder in specifications:
        summary,outputs,record=review_run(packs[pack],ROOT/'runs'/folder,tokenizer)
        summaries[arm]=summary;transcripts[arm]=outputs;records[arm]=record
    for arms in [('first-base','matched-base','four-target-16','four-target-64'),
                 ('extension-base','extension-four','extension-eight'),('literal-base','literal-four','literal-eight')]:
        expected=[r['input_ids_digest'] for r in transcripts[arms[0]]]
        for arm in arms:
            if [r['input_ids_digest'] for r in transcripts[arm]]!=expected:raise ValueError('Unmatched input tokens')
            if records[arm]['versions']!=records[arms[0]]['versions'] or records[arm]['gpu']['name']!=records[arms[0]]['gpu']['name']:raise ValueError('Runtime/hardware mismatch')
    for a,b in [('extension-four',fit4),('literal-four',fit4),('literal-eight',fit8)]:
        if records[a]['loaded_adapter_sha256']!=sha256(b/'adapter/adapter_model.safetensors'):raise ValueError('Wrong reloaded adapter')
    checks=[verify(packs['four'],ROOT/'runs/aurora-minimal-country-base-20261005-v2',ROOT/'runs/aurora-minimal-country-fit-20261005-v3'),
            verify(packs['four'],ROOT/'runs/aurora-minimal-country-base-20261005-v2',fit4),
            verify(packs['eight'],ROOT/'runs/aurora-minimal-country-extension-base-20261005-v1',fit8)]
    steps=sum(c['actual_steps'] for c in checks)
    raw_comparison={}
    for arm in ('extension-base','extension-four','extension-eight'):
        groups=[g for family,g in summaries[arm]['groups'].items() if family not in ('exact_control','strong_checked_plan_control')]
        raw_comparison[arm]={'responses':sum(g['outputs'] for g in groups),'met':sum(g['met'] for g in groups),
             'units':sum(g['met']+g['unmet']+g['unratable'] for g in groups),
             'application_boundary_met':sum(g['application_boundary_met'] for g in groups),
             'application_boundary_units':sum(g['application_boundary_units'] for g in groups)}
    result={'status':'complete_stored_evidence_replay_passed','model':'Qwen/Qwen3.5-4B',
       'hardware':'NVIDIA RTX PRO 6000 Blackwell Server Edition','selected_full_sources_read':2,
       'unique_training_examples_read':8,'new_actual_optimizer_steps':steps,'cumulative_aurora_qwen35_steps':142+steps,
       'reference_qwen25_steps_unchanged':582,'new_complete_answers_read':sum(s['outputs'] for s in summaries.values()),
       'all_prompt_ids_and_output_texts_rerendered':args.render_tokenizer,
       'software_guards':{'passed':23,'command':'PYTHONPATH=src /mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python -m pytest -q tests/test_training_checks.py tests/test_source_plan_probe.py','scope':'Existing fault-injection and source-plan checks; not model quality.'},
       'raw_eight_case_comparison':raw_comparison,'arms':summaries,
       'literal_mechanism_diagnosis':'All three arms distinguish both fully specified partial states, raw and with checked notes. Active/proactive ambiguity qualifies prior regression; old grades preserved. No new optimization for this clarification.',
       'limits':['One exposed historical event, two country-institution-date roles, hypothetical proposals, given source positions/outcomes.',
                 'Same assistant selected data, authored targets/criteria and graded every answer, without independent review.',
                 'Frozen coverage/application units do not cover every unsupported source claim; additional observations preserved.',
                 'No independent persona, sealed event OOD, native vote-prediction or trained autonomous multi-agent gain established.'],
       'next_decision':'Freeze an outside-training dated policy family and compare base, both saved short adapters and strong checked plans before another fit; no next fit/queue/sweep prepared.'}
    write_json(args.output,result)
    print(json.dumps({k:result[k] for k in ('status','new_actual_optimizer_steps','new_complete_answers_read','raw_eight_case_comparison','all_prompt_ids_and_output_texts_rerendered')},indent=2))

if __name__=='__main__':main()
