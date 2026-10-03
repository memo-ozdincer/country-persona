"""Portable byte/weight/pairing/optimization/stored-review replay, not rejudging."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest, read_jsonl, sha256
from country_persona.coverage_loss import annotate_target


def verify(root):
    pack = root/'data/prepared/coverage-objective-20261003-v1'
    manifest = json.loads((pack/'manifest.json').read_text())
    for name,h in manifest['files_sha256'].items():
        assert sha256(pack/name)==h,name
    for name,h in manifest['source_files_sha256'].items():
        assert sha256(root/name)==h,name
    training = root/'data/prepared/source-application-sft-20261003-v2'
    assert sha256(training/'release.json')==manifest['training_release_sha256']
    assert sha256(training/'train.jsonl')==manifest['training_jsonl_sha256']
    assert sha256(training/'train.manifest.jsonl')==manifest['training_metadata_sha256']
    rows = list(read_jsonl(training/'train.jsonl'))
    metadata = list(read_jsonl(training/'train.manifest.jsonl'))
    allocations = list(read_jsonl(pack/'allocation.jsonl'))
    assert len(rows)==len(metadata)==len(allocations)==20
    for row,meta,a in zip(rows,metadata,allocations):
        assert a['id']==meta['id'] and a['example_sha256']==digest(row)==meta['example_sha256']
        assert len(a['target_ids'])==len(a['target_weights'])==meta['supervised_tokens']
        assert all(math.isfinite(w) and w>0 for w in a['target_weights'])
        assert math.isclose(sum(a['target_weights']),len(a['target_ids']),abs_tol=1e-7)
        assert [{k:v for k,v in s.items() if k!='sequence_token_indices'} for s in a['spans']]==annotate_target(row['completion'][0]['content'])
        assert all(i>=a['prefix_tokens'] for s in a['spans'] for i in s['sequence_token_indices'])
    assert manifest['held_family'] not in {m['split_group'] for m in metadata}
    source = root/'data/raw/coverage-objective-grounding-20261003-v1'
    acquired = json.loads((source/'acquisition.json').read_text())
    assert acquired['pages']==9 and len(acquired['body_column_coverage'])==8
    assert all(c['equal'] for c in acquired['body_column_coverage'])
    statements = json.loads((source/'statements.json').read_text())
    full = (source/'record-9365.txt').read_text()
    for s in statements.values():
        assert full[s['start']:s['end']].strip()==s['text'] and digest(s['text'])==s['text_digest']
    for a in json.loads((pack/'source-anchors.json').read_text()):
        s = statements[a['country']]
        assert s['text'][a['start']:a['end']]==a['quote'] and s['text_digest']==a['statement_digest']
    cases = {c['id']:c for c in read_jsonl(pack/'cases.jsonl')}
    for c in cases.values():
        assert digest({k:v for k,v in c.items() if k!='case_sha256'})==c['case_sha256']
    criteria = json.loads((pack/'criteria.json').read_text())['by_country']
    old_spec = json.loads((root/'configs/posttraining/qwen35-source-plan-spec-20261002.json').read_text())
    old_criteria = {c:[{'id':unit[0],'description':unit[1]} for unit in spec['units']+old_spec['universal_units']] for c,spec in old_spec['countries'].items()}
    groups,records,transcripts = {},{},{}
    for mode,expected,count,steps in [('baseline','coverage_baseline_ten_answers_completed',10,0),('fit','coverage_fit_and_six_answers_completed',6,20)]:
        directory = root/(f'runs/aurora-qwen35-coverage-{mode}-20261003-'+('v2' if mode=='fit' else 'v1'))
        record = json.loads((directory/'run.json').read_text())
        records[mode] = record
        assert record['status']==expected and record['completed_calls']==count and record['new_training_steps']==steps
        assert record['config']['eval_manifest_sha256']==sha256(pack/'manifest.json')
        assert datetime.fromisoformat(manifest['created_at'])<datetime.fromisoformat(record['created_at'])
        for name,h in record['source_code_sha256'].items():
            assert sha256(directory/'source'/Path(name).name)==h
        transcript = list(read_jsonl(directory/'transcript.jsonl'))
        transcripts[mode] = transcript
        assert len(transcript)==count and sha256(directory/'transcript.jsonl')==record['transcript_sha256']
        outputs = {(r['arm'],r['id']):r for r in transcript}
        assert len(outputs)==count
        for r in transcript:
            c = cases[r['id']]
            assert digest(r['input_ids'])==r['input_ids_digest']==c['input_ids_digest']
            assert digest(r['output_ids'])==r['output_digest'] and r['case_sha256']==c['case_sha256']
            assert not r['hit_output_cap']
        review = json.loads((directory/'inspection.json').read_text())
        assert review['transcript_sha256']==record['transcript_sha256'] and review['frozen_criteria_sha256']==sha256(pack/'criteria.json')
        assert review['all_complete_answers_inspected'] and len(review['responses'])==count
        if mode=='baseline':
            assert review['all_ten_complete_answers_inspected']
        for response in review['responses']:
            key = (response['arm'],response['response_id'])
            output = outputs[key]['output']
            case = cases[key[1]]
            assert hashlib.sha256(output.encode()).hexdigest()==response['output_sha256']
            units = old_criteria[case['country_iso3']] if case['condition']=='training_control' else criteria[case['country_iso3']]
            assert {r['id'] for r in response['ratings']}=={u['id'] for u in units}
            for rating in response['ratings']:
                assert rating['status'] in ('met','unmet','unratable')
                assert rating['output_quote'] is None or rating['output_quote'] in output
            counts = Counter(r['status'] for r in response['ratings'])
            assert response['counts']=={k:counts[k] for k in ('met','unmet','unratable')}
            assert response['strict_result']==('fail' if counts['unmet'] else 'unresolved' if counts['unratable'] else 'pass')
            group = groups.setdefault((response['arm'],case['condition']),Counter())
            group.update(counts)
            group['answers'] += 1
            group['strict_passes'] += int(response['strict_result']=='pass')
    base,fit = records['baseline'],records['fit']
    assert base['versions']==fit['versions'] and base['gpu']['name']==fit['gpu']['name']
    assert base['generation_config']==fit['generation_config']
    helper = 'scripts/run_aurora_qwen35_smoke.py'
    assert base['source_code_sha256'][helper]==fit['source_code_sha256'][helper]
    assert fit['actual_loss_guard']['maximum_uniform_ce_difference']<=1e-5
    assert fit['actual_loss_guard']['per_example_supervised_mass_preserved'] and fit['matched_input_digests']
    assert fit['mask_audit']['actual_trainer_masks_checked'] and fit['mask_audit']['rows']==20
    assert fit['loss_execution']['custom_loss_calls']==40
    check = fit['optimization_checks']['rank_checks'][0]
    assert check['steps']==check['gradient_checks']==20 and check['all_adapter_tensors_finite'] and check['changed_adapter_tensors']>0
    uniform = json.loads((root/'runs/aurora-qwen35-source-application-fit-20261003-v1/run.json').read_text())
    original_check = uniform['optimization_checks']['rank_checks'][0]
    for key in ('actual_sequence_tokens','actual_target_tokens'):
        assert check[key]==original_check[key],key
    assert fit['serialization_checks']['saved_tensors_equal'] and fit['serialization_checks']['reload_verified_after_state_perturbation'] and fit['serialization_checks']['same_base_probe_logits_equal']
    for name,h in fit['serialization_checks']['files_sha256'].items():
        assert sha256(root/'runs/aurora-qwen35-coverage-fit-20261003-v2/adapter'/name)==h
    for name,key in [('run.json','baseline_run_sha256'),('transcript.jsonl','baseline_transcript_sha256'),('inspection.json','baseline_inspection_sha256')]:
        assert sha256(root/'runs/aurora-qwen35-coverage-baseline-20261003-v1'/name)==fit['config'][key]
    assert datetime.fromisoformat(json.loads((root/'runs/aurora-qwen35-coverage-baseline-20261003-v1/inspection.json').read_text())['created_at'])<datetime.fromisoformat(fit['created_at'])
    return {'status':'coverage_objective_bytes_weights_pairing_steps_stored_review_replay_verified','new_answers':16,'new_optimizer_steps':20,
        'same_training_texts_and_processed_tokens':True,'groups':[{'arm':a,'condition':c,**dict(counts)} for (a,c),counts in groups.items()],
        'independent_semantic_review':False,'persona_or_multi_agent_gain_established':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    print(json.dumps(verify(p.parse_args().root.resolve()),indent=2))
