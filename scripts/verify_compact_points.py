"""Replay three compact-plan controls and complete the eight-process checkpoint receipt."""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json
from verify_two_context_country import exited


def main():
    pack = ROOT / 'data/prepared/compact-points-20261007-v2'
    parent = ROOT / 'data/prepared/compression-points-only-20261007-v1'
    manifest = json.loads((pack / 'manifest.json').read_text())
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert not manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected
    for name in ['sources.json', 'criteria.json', 'presentation-criteria.json']:
        assert sha256(pack / name) == sha256(parent / name)
    case = list(read_jsonl(pack / 'cases.jsonl'))[0]
    original = next(c for c in read_jsonl(parent / 'cases.jsonl') if c['country_iso3'] == 'BRA')
    oldplan = json.loads((parent / 'held-plans.json').read_text())['plans']['BRA']
    plan = json.loads((pack / 'checked-plan.json').read_text())
    assert plan['words'] == len(plan['plan'].split()) == 276 and plan['all_source_application_authority_meanings_audited']
    assert case['prompt'] == [original['prompt'][0], {'role': 'user', 'content': original['prompt'][1]['content'].replace(oldplan, plan['plan'])}]
    from transformers import AutoTokenizer
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compact-points-base-20261007-v2.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    assert tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False) == case['input_ids']
    summaries, resources = {}, []
    caps, tokens, seconds = 0, 0, 0
    for arm in ['base', 'point8', 'compression8']:
        directory = ROOT / f'runs/aurora-compact-points-{arm}-20261007-v2'
        run = json.loads((directory / 'run.json').read_text())
        inspection = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        assert run['status'] == 'completed' and run['optimizer_steps'] == 0 and exited(run['identity'])
        assert run['pack_manifest_sha256'] == sha256(pack / 'manifest.json') and inspection['all_outputs_read_complete']
        assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert inspection['manual_annotations_sha256'] == sha256(directory / 'manual-annotations.json')
        assert inspection['criteria_sha256'] == sha256(pack / 'criteria.json') and len(rows) == len(inspection['reviews']) == 1
        assert run['versions'] == cfg['runtime_pins'] and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert run['config'][key] == cfg[key]
        for name, expected in run['source_code_sha256'].items():
            assert sha256(directory / Path(name).name) == expected
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        previous = run['previous_inspected_run']
        assert sha256(ROOT / previous['run'] / 'inspection.json') == previous['inspection_sha256']
        if arm != 'base':
            assert run['loaded_adapter_sha256'] == sha256(ROOT / run['config']['adapter'] / 'adapter_model.safetensors')
        row, r = rows[0], inspection['reviews'][0]
        assert row['input_ids'] == case['input_ids'] and row['id'] == case['id'] == r['id']
        assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
        assert r['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest() and r['all_output_read_complete']
        assert r['words'] == len(row['output'].split())
        counts = dict(Counter(v['status'] for v in r['ratings'].values()))
        assert counts == r['content_counts']
        complete = all(v['status'] == 'met' for v in list(r['ratings'].values()) + list(r['universal_checks'].values()))
        assert r['usable_realization_pass'] == (complete and all(r['presentation'].values()) and not row['at_output_cap'])
        summaries[arm] = {'content': counts, 'words': r['words'], 'universal': dict(Counter(v['status'] for v in r['universal_checks'].values())),
                          'presentation': r['presentation'], 'usable_realization_pass': r['usable_realization_pass']}
        caps += int(row['at_output_cap']); tokens += row['generated_tokens']; seconds += row['generation_seconds']
        resources.append({'run': str(directory.relative_to(ROOT)), 'identity': run['identity'], 'gpu': run['gpu'], 'exited': True})
    decision = json.loads((ROOT / 'runs/aurora-compact-points-compression8-20261007-v2/inspection.json').read_text())['decision']
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'summaries': summaries,
        'new_model_outputs': 3, 'new_optimizer_steps': 0, 'cumulative_qwen35_steps': 2526, 'reference_qwen25_steps': 582,
        'resources': resources, 'all_owned_processes_exited': True, 'all_outputs_hand_read': True, 'uncapped': 3-caps, 'capped': caps,
        'generated_tokens': tokens, 'generation_seconds': seconds, 'compact_plan_words': 276,
        'uncalled_draft_correction': 'v1 ambiguous ICC versus State unable/unwilling subject and slash-list shorthand corrected before any calls; v1 bytes retained.',
        'independent_review_complete': False, 'scope': 'Given-content format realization on one exposed Brazil/Libya case; no native persona, autonomous planner, multi-agent or strong OOD result.',
        'next_decision': decision}
    path = ROOT / 'reports/compact-points-checkpoint-20261007-v2.json'
    write_json(path, receipt)
    mainpath = ROOT / 'reports/compression-checkpoint-20261007-v1.json'
    pointpath = ROOT / 'reports/compression-points-only-checkpoint-20261007-v1.json'
    main = json.loads(mainpath.read_text()); points = json.loads(pointpath.read_text())
    assert main['status'] == points['status'] == 'pass' and main['new_model_outputs'] == 34 and points['new_model_outputs'] == 4
    combined = {**main, 'verified_at': datetime.now(timezone.utc).isoformat(),
        'main_checkpoint_sha256': sha256(mainpath), 'points_only_checkpoint_sha256': sha256(pointpath), 'compact_checkpoint_sha256': sha256(path),
        'new_model_outputs': 41, 'uncapped': main['uncapped'] + points['uncapped'] + 3-caps, 'capped': main['capped'] + points['capped'] + caps,
        'resources': main['resources'] + points['resources'] + resources, 'points_only_groups': points['groups'],
        'points_only_summaries': points['summaries'], 'compact_summaries': summaries,
        'generated_tokens': main['generated_tokens'] + points['generated_tokens'] + tokens,
        'generation_seconds': main['generation_seconds'] + points['generation_seconds'] + seconds,
        'next_decision': decision}
    write_json(ROOT / 'reports/compression-realization-combined-20261007-v1.json', combined)
    print(json.dumps({'status': receipt['status'], 'compact_summaries': summaries, 'combined_outputs': 41}, indent=2))


if __name__ == '__main__':
    main()
