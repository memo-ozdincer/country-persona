"""Replay three no-fit ordinary-point answers, source/semantic audit and unchanged older grades."""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from verify_two_context_country import exited


def summary(review, include_presentation=False):
    fmt = review['format_observation']
    values = list(review['ratings'].values()) + list(review['universal_checks'].values())
    strict = all(v['status'] == 'met' for v in values) and not fmt['at_cap'] and fmt['within300words']
    result = {'content': dict(Counter(v['status'] for v in review['ratings'].values())),
        'source': dict(Counter(v['status'] for k, v in review['ratings'].items() if k.startswith('S'))),
        'application': dict(Counter(v['status'] for k, v in review['ratings'].items() if k.startswith('A'))),
        'universal': dict(Counter(v['status'] for v in review['universal_checks'].values())),
        'words': fmt['words'], 'original_strict_pass': strict}
    if include_presentation:
        presentation = review['presentation_checks']
        result['presentation_checks'] = {k: v['status'] for k, v in presentation.items()}
        result['usable_realization_pass'] = strict and all(v['status'] == 'met' for v in presentation.values())
    return result


def main():
    pack = ROOT / 'data/prepared/ordinary-points-20261006-v2'
    manifest = json.loads((pack / 'manifest.json').read_text())
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert not manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected
    case = list(read_jsonl(pack / 'cases.jsonl'))[0]
    prov = json.loads((pack / 'provenance.json').read_text())
    plans = json.loads((pack / 'plans.json').read_text())
    old = ROOT / prov['old_pack']
    assert sha256(old / 'manifest.json') == prov['old_manifest_sha256']
    original = next(c for c in read_jsonl(old / 'cases.jsonl') if c['id'] == prov['old_case_id'])
    assert digest(original) == prov['old_case_digest'] and original['input_ids_digest'] == prov['old_input_ids_digest']
    assert case['prompt'][0] == original['prompt'][0]
    assert case['prompt'][1]['content'].replace(plans['ordinary_english'], plans['original_shorthand']) == original['prompt'][1]['content']
    assert case['prompt'][1]['content'].count(plans['ordinary_english']) == 1
    assert digest(plans['ordinary_english']) == prov['ordinary_plan_digest'] and digest(plans['original_shorthand']) == prov['shorthand_digest']
    source = json.loads((pack / 'source.json').read_text())
    assert source == json.loads((old / 'sources.json').read_text())['icc']['BRA']
    assert source['text'] in case['prompt'][1]['content']
    assert sha256(pack / 'criteria.json') == prov['criteria_sha256'] == sha256(old / 'criteria.json')
    criteria = json.loads((pack / 'criteria.json').read_text())
    presentation = json.loads((pack / 'presentation-criteria.json').read_text())
    assert presentation['frozen_before_new_calls']
    target_audit = json.loads((ROOT / 'reports/ordinary-points-source-audit-20261006-v2.json').read_text())
    assert target_audit['status'] == 'pass' and target_audit['manifest_sha256'] == sha256(pack / 'manifest.json')
    assert target_audit['same_meanings_hand_audit'] == hand['same_meanings_hand_audit']
    assert target_audit['presentation_criteria_sha256'] == sha256(pack / 'presentation-criteria.json')
    assert target_audit['new_model_calls_at_audit'] == target_audit['new_optimizer_steps'] == 0
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(ROOT / 'runs/aurora-plan-input-fit-20261006-v1/adapter', local_files_only=True)
    assert tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False) == case['input_ids']
    assert digest(case['input_ids']) == case['input_ids_digest'] and len(case['input_ids']) + 2048 <= 8192
    arms, old_results, resources, links = {}, {}, [], []
    configs = []
    total_tokens, total_seconds = 0, 0
    for arm in ['base', 'raw8', 'plan8']:
        directory = ROOT / f'runs/aurora-ordinary-points-{arm}-20261006-v2'
        run = json.loads((directory / 'run.json').read_text())
        annotation = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        assert run['status'] == 'completed' and run['optimizer_steps'] == 0 and exited(run['identity'])
        assert len(rows) == len(annotation['reviews']) == 1 and annotation['all_outputs_read_complete']
        assert run['transcript_sha256'] == annotation['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert run['pack_manifest_sha256'] == sha256(pack / 'manifest.json')
        assert annotation['criteria_sha256'] == sha256(pack / 'criteria.json')
        assert annotation['presentation_criteria_sha256'] == sha256(pack / 'presentation-criteria.json')
        assert run['config_sha256'] == sha256(ROOT / f'configs/posttraining/qwen35-ordinary-points-{arm}-20261006-v2.json')
        assert run['versions'] == run['config']['runtime_pins'] and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        assert run['config']['phase'] == 'writer' and run['config']['max_steps'] == run['config']['training_examples'] == 0
        for name, expected in run['source_code_sha256'].items():
            assert sha256(directory / Path(name).name) == expected
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        prev = run['previous_inspected_run']
        assert sha256(ROOT / prev['run'] / 'inspection.json') == prev['inspection_sha256']
        if arm != 'base':
            adapter = ROOT / run['config']['adapter']
            assert run['loaded_adapter_sha256'] == sha256(adapter / 'adapter_model.safetensors')
            assert run['config']['adapter_config_sha256'] == sha256(adapter / 'adapter_config.json')
        row, review = rows[0], annotation['reviews'][0]
        assert row['id'] == review['id'] == case['id'] and row['input_ids'] == case['input_ids']
        assert row['input_ids_digest'] == digest(row['input_ids']) and tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
        assert row['generated_tokens'] == len(row['output_ids']) and not row['at_output_cap']
        assert review['all_output_read_complete'] and hashlib.sha256(row['output'].encode()).hexdigest() == review['output_sha256']
        assert review['format_observation']['words'] == len(row['output'].split())
        assert review['format_observation']['within300words'] == (len(row['output'].split()) <= 300)
        assert set(review['ratings']) == set(criteria['source_units']['icc']['BRA']) | set(criteria['common_units'])
        assert set(review['universal_checks']) == set(criteria['universal_checks'])
        assert set(review['presentation_checks']) == set(presentation['checks'])
        assert all(v['status'] in {'met', 'unmet', 'unratable'} and v['reason'].strip() for v in list(review['ratings'].values()) + list(review['universal_checks'].values()) + list(review['presentation_checks'].values()))
        arms[arm] = summary(review, True)
        resources.append({'run': str(directory.relative_to(ROOT)), 'identity': run['identity'], 'gpu': run['gpu'], 'exited': True})
        configs.append(run['config']); total_tokens += row['generated_tokens']; total_seconds += row['generation_seconds']
        # Existing shorthand outputs and primitive reviews remain exactly those
        # bound before the new calls. No new readability grades replace them.
        previous = prov['old_point_case_reviews'][arm]
        olddir = ROOT / previous['run']
        oi = json.loads((olddir / 'inspection.json').read_text())
        assert sha256(olddir / 'inspection.json') == previous['inspection_sha256']
        orow = next(v for v in read_jsonl(olddir / 'transcript.jsonl') if v['id'] == original['id'])
        oreview = next(v for v in oi['reviews'] if v['id'] == original['id'])
        assert oi['transcript_sha256'] == sha256(olddir / 'transcript.jsonl') and orow['input_ids'] == original['input_ids']
        old_results[arm] = summary(oreview)
        links.append({'arm': arm, 'run': previous['run'], 'output_digest': digest(orow), 'review_digest': digest(oreview), 'inspection_sha256': previous['inspection_sha256']})
    for cfg in configs[1:]:
        for key in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs', 'runtime_pins']:
            assert cfg[key] == configs[0][key]
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(),
        'new_model_outputs': 3, 'new_optimizer_steps': 0, 'cumulative_qwen35_steps': 2270, 'reference_qwen25_steps': 582,
        'input_tokens': len(case['input_ids']), 'ordinary_plan_words': len(plans['ordinary_english'].split()),
        'old_shorthand_plan_words': len(plans['original_shorthand'].split()), 'arms': arms,
        'older_shorthand_grades_unchanged': old_results, 'old_output_review_provenance': links,
        'resources': resources, 'all_three_owned_gpu_identities_exited': True,
        'all_three_uncapped_full_outputs_read': True, 'generated_tokens': total_tokens, 'generation_seconds': total_seconds,
        'independent_review_complete': False, 'scope': prov['scope'],
        'next_decision': json.loads((ROOT / 'runs/aurora-ordinary-points-plan8-20261006-v2/inspection.json').read_text())['decision']}
    write_json(ROOT / 'reports/ordinary-points-checkpoint-20261006-v2.json', receipt)
    print(json.dumps({k: receipt[k] for k in ['status', 'arms', 'older_shorthand_grades_unchanged']}, indent=2))


if __name__ == '__main__':
    main()
