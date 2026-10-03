"""Portable source-preference bytes, masks, reference/steps and stored-review replay."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256
from country_persona.preference_checks import validate_pair
from verify_coverage_objective_checkpoint import verify as verify_coverage


def verify(root):
    previous=verify_coverage(root)
    pack=root/'data/prepared/source-preference-20261003-v1';manifest=json.loads((pack/'manifest.json').read_text())
    for name,h in manifest['files_sha256'].items():assert sha256(pack/name)==h,name
    original_path=root/'data/prepared/source-application-sft-20261003-v2/train.jsonl'
    assert sha256(original_path)==manifest['original_training_jsonl_sha256']
    original=list(read_jsonl(original_path));pairs=list(read_jsonl(pack/'pairs.jsonl'));audits=list(read_jsonl(pack/'pair-audit.jsonl'))
    assert len(pairs)==len(audits)==len(original)==20
    for row,pair,a in zip(original,pairs,audits):validate_pair(row,pair,a)
    run_dir=root/'runs/aurora-qwen35-source-preference-20261003-v3';run=json.loads((run_dir/'run.json').read_text())
    assert run['status']=='source_preference_fit_and_six_answers_completed' and run['new_training_steps']==20 and run['completed_calls']==6
    assert sha256(root/'configs/posttraining/qwen35-source-preference-20261003-v3.json')==run['config_sha256']
    assert run['config']['preference_manifest_sha256']==sha256(pack/'manifest.json')
    assert datetime.fromisoformat(manifest['created_at'])<datetime.fromisoformat(run['created_at'])
    coverage=root/run['config']['coverage_run']
    assert sha256(coverage/'run.json')==run['config']['coverage_run_sha256']
    assert sha256(coverage/'inspection.json')==run['config']['coverage_inspection_sha256']==manifest['previous_coverage_inspection_sha256']
    assert datetime.fromisoformat(json.loads((coverage/'inspection.json').read_text())['created_at'])<datetime.fromisoformat(manifest['created_at'])
    for name,h in run['source_code_sha256'].items():assert sha256(run_dir/'source'/Path(name).name)==h
    mask=run['mask_audit'];assert mask['actual_trainer_token_ids_and_masks_checked'] and mask['prompt_and_padding_excluded']
    assert mask['chosen_tokens_once']==manifest['chosen_total_tokens']==4710 and mask['rejected_tokens_once']==manifest['rejected_total_tokens']==4697
    checks=run['optimization_checks']['rank_checks'][0]
    assert checks['steps']==checks['gradient_checks']==20 and checks['microbatches']==40
    assert checks['actual_sequence_tokens']==2*mask['sequence_tokens_once'] and checks['actual_target_tokens']==2*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
    assert checks['all_adapter_tensors_finite'] and checks['changed_adapter_tensors']>0
    assert sha256(run_dir/'reference-logps.jsonl')==run['reference_logps_sha256']
    refs=list(read_jsonl(run_dir/'reference-logps.jsonl'));assert len(refs)==20
    assert run['method']['reference']=='cached exact base log probabilities with adapter disabled'
    assert not run['method']['additional_chosen_nll_or_kl'] and not run['method']['introspection']
    assert run['serialization_checks']['saved_tensors_equal'] and run['serialization_checks']['reload_verified_after_state_perturbation'] and run['serialization_checks']['same_base_probe_logits_equal']
    for name,h in run['serialization_checks']['files_sha256'].items():assert sha256(run_dir/'adapter'/name)==h
    evaluation=root/run['config']['eval_pack'];criteria=json.loads((evaluation/'criteria.json').read_text())['by_country']
    spec=json.loads((root/'configs/posttraining/qwen35-source-plan-spec-20261002.json').read_text())
    old={c:[{'id':u[0],'description':u[1]} for u in s['units']+spec['universal_units']] for c,s in spec['countries'].items()}
    cases={c['id']:c for c in read_jsonl(evaluation/'cases.jsonl')}
    transcripts=list(read_jsonl(run_dir/'transcript.jsonl'));assert len(transcripts)==len({r['id'] for r in transcripts})==6
    assert sha256(run_dir/'transcript.jsonl')==run['transcript_sha256']
    outputs={r['id']:r for r in transcripts}
    historical=json.loads((coverage/'run.json').read_text())
    assert run['versions']==historical['versions'] and run['gpu']['name']==historical['gpu']['name'] and run['generation_config']==historical['generation_config']
    helper='scripts/run_aurora_qwen35_smoke.py'
    assert run['source_code_sha256'][helper]==historical['source_code_sha256'][helper]
    for r in transcripts:
        assert r['input_ids_digest']==digest(r['input_ids'])==cases[r['id']]['input_ids_digest']
        assert digest(r['output_ids'])==r['output_digest'] and r['case_sha256']==cases[r['id']]['case_sha256'] and not r['hit_output_cap']
    review=json.loads((run_dir/'inspection.json').read_text());assert review['all_complete_answers_inspected'] and len(review['responses'])==6
    assert review['transcript_sha256']==run['transcript_sha256'] and review['frozen_criteria_sha256']==sha256(evaluation/'criteria.json')
    groups={}
    for response in review['responses']:
        row=outputs[response['response_id']];case=cases[row['id']];output=row['output']
        assert hashlib.sha256(output.encode()).hexdigest()==response['output_sha256']
        units=old[row['country']] if case['condition']=='training_control' else criteria[row['country']]
        assert {r['id'] for r in response['ratings']}=={u['id'] for u in units}
        descriptions={u['id']:u['description'] for u in units}
        assert len(response['ratings'])==len(units)
        for rating in response['ratings']:
            assert rating['status'] in ('met','unmet','unratable')
            assert rating['criterion']==descriptions[rating['id']]
        counts=Counter(r['status'] for r in response['ratings'])
        assert response['counts']=={k:counts[k] for k in ('met','unmet','unratable')}
        assert response['strict_result']==('fail' if counts['unmet'] else 'unresolved' if counts['unratable'] else 'pass')
        for rating in response['ratings']:assert rating['output_quote'] is None or rating['output_quote'] in output
        g=groups.setdefault(case['condition'],Counter());g.update(counts);g['answers']+=1;g['strict_passes']+=int(response['strict_result']=='pass')
    failed_steps=0
    for version,steps in [('v1',0),('v2',20)]:
        failed=root/('runs/aurora-qwen35-source-preference-20261003-'+version)
        failure=json.loads((failed/'failure.json').read_text())
        assert failure['new_training_steps']==steps and failure['completed_calls']==0
        for name,h in failure['source_code_sha256'].items():assert sha256(failed/'source'/Path(name).name)==h
        failed_steps+=steps
    return {'status':'source_preference_bytes_pairing_reference_steps_stored_review_replay_verified','new_answers':6,'new_optimizer_steps':20,'failed_attempt_optimizer_steps':failed_steps,
        'previous_coverage_verified':previous['status'],'preferred_sft_targets_unchanged':True,'groups':{k:dict(v) for k,v in groups.items()},
        'independent_semantic_review':False,'persona_or_multi_agent_gain_established':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    print(json.dumps(verify(p.parse_args().root.resolve()),indent=2))
