"""Replay four exposed source-removal answers and compose the completed training checkpoint."""
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
    mainpath = ROOT / 'reports/compression-checkpoint-20261007-v1.json'
    main = json.loads(mainpath.read_text())
    assert main['status'] == 'pass' and main['all_owned_processes_exited'] and main['new_model_outputs'] == 34
    pack = ROOT / 'data/prepared/compression-points-only-20261007-v1'
    manifest = json.loads((pack / 'manifest.json').read_text())
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert not manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected
    parent = ROOT / 'data/prepared/compression-fit-20261006-v1'
    for name in ['sources.json', 'criteria.json', 'held-plans.json', 'presentation-criteria.json']:
        assert sha256(pack / name) == sha256(parent / name)
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    oldcases = {c['id']: c for c in read_jsonl(parent / 'cases.jsonl')}
    from transformers import AutoTokenizer
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compression-points-only-base-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    for c in cases:
        old = oldcases[c['id'].removesuffix('-only')]
        text = old['prompt'][1]['content']
        start = text.index('\n\nCOMPLETE NATIONAL STATEMENT')
        end = text.index('\n\nSOURCE-CHECKED PLAN', start)
        expected = (text[:start] + text[end:]).replace('Full source remains for verification.', 'The source is archived for verification.')
        assert c['prompt'] == [old['prompt'][0], {'role': 'user', 'content': expected}]
        assert tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False) == c['input_ids']
    groups, summaries, resources = {}, {}, []
    caps, tokens, seconds = 0, 0, 0
    for arm in ['base', 'adapter']:
        directory = ROOT / f'runs/aurora-compression-points-only-{arm}-20261007-v1'
        run = json.loads((directory / 'run.json').read_text())
        review = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        assert run['status'] == 'completed' and run['optimizer_steps'] == 0 and exited(run['identity'])
        assert run['pack_manifest_sha256'] == sha256(pack / 'manifest.json') and review['all_outputs_read_complete']
        assert run['transcript_sha256'] == review['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert review['manual_annotations_sha256'] == sha256(directory / 'manual-annotations.json')
        assert review['criteria_sha256'] == sha256(pack / 'criteria.json')
        assert review['presentation_criteria_sha256'] == sha256(pack / 'presentation-criteria.json')
        assert len(rows) == len(review['reviews']) == len(cases) == 2
        assert run['versions'] == cfg['runtime_pins'] and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert run['config'][key] == cfg[key]
        for name, expected in run['source_code_sha256'].items():
            assert sha256(directory / Path(name).name) == expected
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        previous = run['previous_inspected_run']
        assert sha256(ROOT / previous['run'] / 'inspection.json') == previous['inspection_sha256']
        if arm == 'adapter':
            assert run['loaded_adapter_sha256'] == sha256(ROOT / run['config']['adapter'] / 'adapter_model.safetensors')
        summaries[arm] = {}
        counter = Counter()
        for c, row, r in zip(cases, rows, review['reviews'], strict=True):
            assert c['id'] == row['id'] == r['id'] and c['input_ids'] == row['input_ids']
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
            assert hashlib.sha256(row['output'].encode()).hexdigest() == r['output_sha256'] and r['all_output_read_complete']
            assert r['words'] == len(row['output'].split())
            counts = dict(Counter(v['status'] for v in r['ratings'].values()))
            assert counts == r['content_counts']
            counter.update(counts)
            summaries[arm][c['id']] = {'content': counts, 'words': r['words'], 'universal': dict(Counter(v['status'] for v in r['universal_checks'].values())),
                'presentation': r['presentation'], 'usable_realization_pass': r['usable_realization_pass']}
            caps += int(row['at_output_cap']); tokens += row['generated_tokens']; seconds += row['generation_seconds']
        groups[arm] = {'answers': 2, 'content': dict(counter), 'usable_passes': sum(v['usable_realization_pass'] for v in summaries[arm].values())}
        resources.append({'run': str(directory.relative_to(ROOT)), 'identity': run['identity'], 'gpu': run['gpu'], 'exited': True})
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'summaries': summaries, 'groups': groups,
        'new_model_outputs': 4, 'new_optimizer_steps': 0, 'cumulative_qwen35_steps': 2526, 'reference_qwen25_steps': 582,
        'resources': resources, 'all_owned_processes_exited': True, 'all_outputs_hand_read': True, 'uncapped': 4-caps, 'capped': caps,
        'generated_tokens': tokens, 'generation_seconds': seconds, 'independent_review_complete': False,
        'scope': 'Exposed source-removal development diagnostic; no new family, active training, persona/native prediction/multi-agent or strong OOD result.',
        'next_decision': json.loads((ROOT / 'runs/aurora-compression-points-only-adapter-20261007-v1/inspection.json').read_text())['decision']}
    diagnostic_path = ROOT / 'reports/compression-points-only-checkpoint-20261007-v1.json'
    write_json(diagnostic_path, receipt)
    combined = {**main, 'verified_at': datetime.now(timezone.utc).isoformat(),
        'main_checkpoint_sha256': sha256(mainpath), 'points_only_checkpoint_sha256': sha256(diagnostic_path),
        'new_model_outputs': main['new_model_outputs'] + 4, 'uncapped': main['uncapped'] + receipt['uncapped'], 'capped': main['capped'] + caps,
        'resources': main['resources'] + resources, 'points_only_groups': groups, 'points_only_summaries': summaries,
        'generated_tokens': main['generated_tokens'] + tokens, 'generation_seconds': main['generation_seconds'] + seconds,
        'next_decision': receipt['next_decision']}
    write_json(ROOT / 'reports/compression-realization-combined-20261007-v1.json', combined)
    print(json.dumps({'status': receipt['status'], 'points_only_groups': groups, 'combined_outputs': combined['new_model_outputs']}, indent=2))


if __name__ == '__main__':
    main()
