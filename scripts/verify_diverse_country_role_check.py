"""Replay the primary-role metadata addition and four real no-fit answers."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    pack=ROOT/'data/prepared/diverse-country-role-check-20261006-v1';m=json.loads((pack/'manifest.json').read_text());hand=json.loads((pack/'manual-inspection.json').read_text())
    assert not m['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
    for name,h in m['files_sha256'].items():assert sha256(pack/name)==h
    proof=json.loads((pack/'role-proof.json').read_text());originalpack=ROOT/proof['original_pack'];cases=list(read_jsonl(pack/'cases.jsonl'));original={c['id']:c for c in read_jsonl(originalpack/'cases.jsonl')}
    assert sha256(originalpack/'cases.jsonl')==proof['original_cases_sha256']
    assert sha256(pack/'criteria.json')==sha256(originalpack/'criteria.json')==proof['original_criteria_sha256']
    primary=ROOT/proof['primary_record'];assert sha256(primary)==proof['primary_record_sha256'];record=primary.read_text()
    assert record[record.index('President:'):record.index('Members:')]==proof['primary_chair_span']
    assert 'Mr. De la Gasca López Domínguez' in proof['primary_chair_span'] and '(Ecuador)' in proof['primary_chair_span']
    for c,link in zip(cases,proof['changes'],strict=True):
        old=original[c['id']];assert c['prompt'][0]==old['prompt'][0]
        assert c['prompt'][1]['content']==old['prompt'][1]['content'].replace('COMPLETE NATIONAL STATEMENT — GBR',proof['metadata_added']+'\nCOMPLETE NATIONAL STATEMENT — GBR',1)
        assert digest(old['prompt'])==link['old_prompt_digest'] and digest(c['prompt'])==link['new_prompt_digest']
    from transformers import AutoTokenizer
    fitdir=ROOT/'runs/aurora-diverse-country-fit-20261006-v2';tok=AutoTokenizer.from_pretrained(fitdir/'adapter',local_files_only=True)
    fr=json.loads((fitdir/'run.json').read_text());weights=fr['serialization_checks']['files_sha256']
    for name,h in weights.items():assert sha256(fitdir/'adapter'/name)==h
    criteria=json.loads((pack/'criteria.json').read_text());summary={};resources={};tokens=0;seconds=0.;caps=0
    for arm in ['base','adapter']:
        directory=ROOT/f'runs/aurora-diverse-country-role-{arm}-20261006-v1'
        run=json.loads((directory/'run.json').read_text());review=json.loads((directory/'inspection.json').read_text());rows=list(read_jsonl(directory/'transcript.jsonl'))
        assert run['status']=='completed' and run['optimizer_steps']==0 and run['mode']==arm
        assert run['pack_manifest_sha256']==sha256(pack/'manifest.json') and run['manual_inspection_sha256']==sha256(pack/'manual-inspection.json')
        cfgpath=ROOT/f'configs/posttraining/qwen35-diverse-country-role-{arm}-20261006-v1.json';cfg=json.loads(cfgpath.read_text())
        assert run['config']==cfg and run['config_sha256']==sha256(cfgpath)
        assert run['versions']==fr['versions'] and run['gpu']['name']==fr['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert cfg[key]==fr['config'][key]
        if arm=='adapter':assert run['loaded_adapter_sha256']==weights['adapter_model.safetensors']
        for name,h in run['source_code_sha256'].items():assert sha256(directory/Path(name).name)==h
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
        assert run['transcript_sha256']==review['transcript_sha256']==sha256(directory/'transcript.jsonl') and review['all_outputs_read_complete']
        assert review['criteria_sha256']==sha256(pack/'criteria.json') and len(rows)==len(review['reviews'])==2
        expectedprevious=fitdir if arm=='base' else ROOT/'runs/aurora-diverse-country-role-base-20261006-v1'
        assert Path(run['previous_inspected_run']['run']).resolve()==expectedprevious and run['previous_inspected_run']['inspection_sha256']==sha256(expectedprevious/'inspection.json')
        results={}
        for c,row,annotation in zip(cases,rows,review['reviews'],strict=True):
            assert c['id']==row['id']==annotation['id'] and row['input_ids']==c['input_ids']
            assert tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**cfg['chat_template_kwargs'])==c['input_ids']
            assert digest(row['input_ids'])==row['input_ids_digest'] and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output']
            assert len(row['output_ids'])==row['generated_tokens'] and row['at_output_cap']==(row['generated_tokens']==cfg['generation_max_new_tokens'])
            assert annotation['all_output_read_complete'] and annotation['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
            assert set(annotation['ratings'])==set(criteria['source_units']['somalia']['GBR'])|set(criteria['common_units'])
            assert set(annotation['universal_checks'])==set(criteria['universal_checks'])
            values=[*annotation['ratings'].values(),*annotation['universal_checks'].values()];assert all(v['status'] in ('met','unmet','unratable') and v['reason'].strip() for v in values)
            results[c['id']]={'met':sum(v['status']=='met' for v in annotation['ratings'].values()),'unratable':sum(v['status']=='unratable' for v in annotation['ratings'].values()),'units':12,
                'universal_met':sum(v['status']=='met' for v in annotation['universal_checks'].values()),'words':len(row['output'].split()),'at_cap':row['at_output_cap'],
                'strict_pass':not row['at_output_cap'] and len(row['output'].split())<=300 and all(v['status']=='met' for v in values)}
            tokens+=row['generated_tokens'];seconds+=row['generation_seconds'];caps+=row['at_output_cap']
        summary[arm]=results;resources[arm]={'run_directory':str(directory),'identity':run['identity'],'gpu':run['gpu']}
    write_json(args.output,{'status':'primary_speaker_chair_metadata_only_delta_four_actual_answers_tokens_weights_protocol_and_reviews_replayed','summary':summary,'resources':resources,
        'new_model_generations':4,'new_optimizer_steps':0,'generated_tokens':tokens,'generation_seconds':seconds,'caps':caps,'independent_review_complete':False,'scope':proof['scope']})
    print(json.dumps({'status':'replayed','summary':summary},indent=2))


if __name__=='__main__':main()
