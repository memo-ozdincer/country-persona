"""Replay stored common-seed interaction evidence; no semantic or independent judge."""
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


def changes(a, b):
    keys = [k for k in a if a[k]['status'] != 'unratable' and b[k]['status'] != 'unratable']
    return {'jointly_ratable': len(keys),
            'corrections': [k for k in keys if a[k]['status'] == 'unmet' and b[k]['status'] == 'met'],
            'regressions': [k for k in keys if a[k]['status'] == 'met' and b[k]['status'] == 'unmet'],
            'uncertain_excluded': [k for k in a if k not in keys]}


def main():
    from transformers import AutoTokenizer
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-sanctions-interaction-initial-base-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    rows_by_run, reviews, records, input_sets = {}, {}, [], {}
    summaries, total_tokens, total_seconds = {}, 0, 0
    criteria = json.loads((ROOT / cfg['pack'] / 'criteria.json').read_text())
    protocol = json.loads((ROOT / cfg['pack'] / 'protocol.json').read_text())
    for stage in ['initial', 'seed', 'peer']:
        for mode in ['base', 'adapter']:
            name = f'aurora-sanctions-interaction-{stage}-{mode}-20261007-v1'
            d = ROOT / 'runs' / name
            r, i = json.loads((d / 'run.json').read_text()), json.loads((d / 'inspection.json').read_text())
            p = ROOT / r['config']['pack']
            m, h = json.loads((p / 'manifest.json').read_text()), json.loads((p / 'manual-inspection.json').read_text())
            assert r['mode'] == mode and r['config']['stage'] == stage
            assert r['status'] == 'completed' and exited(r['identity']) and r['outputs'] == 2 and r['optimizer_steps'] == 0
            assert i['all_outputs_read_complete'] and not i['independent_review_complete']
            assert m['created_at'] < r['created_at'] and not m['training_authorized_for_this_pack']
            assert h['all_selected_texts_read_complete'] and r['pack_manifest_sha256'] == h['manifest_sha256'] == sha256(p / 'manifest.json')
            for f, x in m['files_sha256'].items(): assert sha256(p / f) == x
            for f, x in r['source_code_sha256'].items(): assert sha256(d / Path(f).name) == x
            assert r['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
            assert r['versions'] == cfg['runtime_pins'] and r['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
            assert r['gpu']['uuid'] == 'GPU-2d466265-cfbf-44c7-c234-fc0128ce6ae4'
            for k in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
                assert r['config'][k] == cfg[k]
            assert json.loads((p / 'criteria.json').read_text()) == criteria
            assert json.loads((p / 'protocol.json').read_text()) == protocol
            provenance = json.loads((p / 'provenance.json').read_text())
            for country, parent in provenance['factual_blocks'].items():
                parent_path = ROOT / parent['path']
                assert sha256(parent_path) == parent['sha256']
                parent_case = next(c for c in read_jsonl(parent_path) if c['id'] == parent['case_id'])
                text = parent_case['prompt'][1]['content']
                factual = text[text.index('Documented source points:'):text.index('\n\nCURRENT HYPOTHETICAL NOTE')]
                assert all(country + '\n' + factual in c['prompt'][1]['content'] for c in read_jsonl(p / 'cases.jsonl'))
            assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
            assert i['manual_annotations_sha256'] == sha256(d / 'manual-annotations.json') and i['criteria_sha256'] == sha256(p / 'criteria.json')
            cases, rows = list(read_jsonl(p / 'cases.jsonl')), list(read_jsonl(d / 'transcript.jsonl'))
            assert len(cases) == len(rows) == len(i['reviews']) == 2
            for c, row, v in zip(cases, rows, i['reviews'], strict=True):
                assert c['condition'] == row['condition'] == v['condition'] == stage
                assert c['id'] == row['id'] == v['id'] and c['country_iso3'] == row['country'] == v['country_iso3']
                assert c['input_ids'] == row['input_ids'] == tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
                assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
                assert hashlib.sha256(row['output'].encode()).hexdigest() == v['output_sha256']
                assert not row['at_output_cap'] and len(row['output'].split()) == v['words']
                assert set(v['ratings']) == set(criteria['common_units']) and set(v['universal_checks']) == set(criteria['universal_checks'])
                assert v['content_counts'] == dict(Counter(x['status'] for x in v['ratings'].values()))
                assert v['component_pass'] == (all(x['status'] == 'met' for x in list(v['ratings'].values()) + list(v['universal_checks'].values())) and all(v['presentation'].values()))
                assert v['presentation']['within180words_uncapped'] == (v['words'] <= 180)
                assert set(v['discussion_ratings']) == set(criteria['discussion_units'])
                for k, value in v['discussion_ratings'].items():
                    applicable = stage != 'initial' if k == 'D1' else stage == 'peer'
                    assert value['status'] in (['met', 'unmet', 'unratable'] if applicable else ['not_applicable'])
                active = [x for x in v['discussion_ratings'].values() if x['status'] != 'not_applicable']
                assert v['discussion_pass'] == (bool(active) and all(x['status'] == 'met' for x in active))
                total_tokens += row['generated_tokens']; total_seconds += row['generation_seconds']
            prev = r['previous_inspected_run']
            assert prev['inspection_sha256'] == sha256(ROOT / prev['run'] / 'inspection.json')
            if mode == 'adapter':
                assert r['loaded_adapter_sha256'] == sha256(ROOT / r['config']['adapter'] / 'adapter_model.safetensors')
                assert r['config']['adapter'] == 'runs/aurora-paired-brazil-application-fit-20261007-v1/adapter'
            rows_by_run[(stage, mode)] = {row['country']: row for row in rows}
            reviews[(stage, mode)] = {v['country_iso3']: v for v in i['reviews']}
            input_sets[(stage, mode)] = [c['input_ids'] for c in cases]
            summaries[name] = [{'id': v['id'], 'content': v['content_counts'], 'words': v['words'], 'pass': v['component_pass'], 'discussion_pass': v['discussion_pass']} for v in i['reviews']]
            records.append({'run': str(d.relative_to(ROOT)), 'identity': r['identity'], 'gpu': r['gpu'], 'exited': True})
    for stage in ['initial', 'seed', 'peer']: assert input_sets[(stage, 'base')] == input_sets[(stage, 'adapter')]
    initial = list(read_jsonl(ROOT / cfg['pack'] / 'cases.jsonl'))
    for stage in ['seed', 'peer']:
        p = ROOT / 'data/prepared' / ('sanctions-interaction-20261007-v2-' + stage)
        provenance = json.loads((p / 'provenance.json').read_text())
        link = provenance['history_sources'][0]; origin = ROOT / link['run']
        assert link['run'] == 'runs/aurora-sanctions-interaction-initial-base-20261007-v1'
        for k in ['run', 'transcript', 'inspection']: assert link[k + '_sha256'] == sha256(origin / (k + ('.jsonl' if k == 'transcript' else '.json')))
        for c, parent in zip(read_jsonl(p / 'cases.jsonl'), initial, strict=True):
            own = c['country_iso3']; other = 'BRA' if own == 'IND' else 'IND'
            user = c['prompt'][1]['content']; prefix = parent['prompt'][1]['content']
            assert user.startswith(prefix) and c['prompt'][0] == parent['prompt'][0]
            expected = prefix + '\n\nSTARTING DRAFT FOR YOUR ASSIGNED ROLE (actual stored base-model analysis, not an official national statement):\n' + rows_by_run[('initial', 'base')][own]['output']
            if stage == 'peer': expected += '\n\nPEER DRAFT FOR ' + other + ' (actual stored base-model analysis; not government authority):\n' + rows_by_run[('initial', 'base')][other]['output']
            expected += '\n\nREVISION TASK:\n' + protocol['revision_task']
            assert user == expected
    comparisons = {}
    for mode in ['base', 'adapter']:
        comparisons[mode] = {}
        for country in ['IND', 'BRA']:
            start = reviews[('initial', 'base')][country]
            seed, peer = reviews[('seed', mode)][country], reviews[('peer', mode)][country]
            comparisons[mode][country] = {'base_start_to_seed': changes(start['ratings'], seed['ratings']),
                                         'base_start_to_peer': changes(start['ratings'], peer['ratings']),
                                         'peer_vs_seed': changes(seed['ratings'], peer['ratings']),
                                         'guard_peer_vs_seed': changes(seed['universal_checks'], peer['universal_checks'])}
    primary = json.loads((ROOT / 'data/raw/source-plan-grounding-20261002-v1/statements.json').read_text())
    raw = (ROOT / 'data/raw/source-plan-grounding-20261002-v1/record-9214.txt').read_text()
    for k in ['IND', 'BRA']: assert raw[primary[k]['start']:primary[k]['end']].strip() == primary[k]['text']
    for stage in ['initial', 'seed', 'peer']:
        p = ROOT / 'data/prepared' / ('sanctions-interaction-20261007-v2-' + stage)
        assert json.loads((p / 'full-primary-spans.json').read_text()) == {k: primary[k] for k in ['IND', 'BRA']}
    assert len(records) == 6 and sum(len(x) for x in rows_by_run.values()) == 12
    write_json(ROOT / 'reports/sanctions-interaction-checkpoint-20261007-v1.json', {
        'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': 12,
        'uncapped': 12, 'capped': 0, 'new_optimizer_steps': 0, 'cumulative_qwen35_steps': 3934,
        'selected_application_branch_steps': 256, 'reference_qwen25_steps': 582,
        'total_generated_tokens': total_tokens, 'total_generation_seconds': total_seconds,
        'all_owned_gpu_identities_exited': True, 'resources': records, 'summaries': summaries,
        'comparisons': comparisons, 'identical_inputs_across_weights': True, 'actual_common_base_history_verified': True,
        'independent_review_complete': False, 'source_facts_origin': 'same root assistant curated, not a source-reader rollout or independent teacher',
        'protocol_caveat': 'Shared revision instruction conditionally mentions peer behavior, but seed-only mode is not explicitly named in model-visible text; attribution failures may reflect prompt ambiguity. Preserve protocol/grades, clarify mode before new training.',
        'strict_passes': sum(v['component_pass'] for by_country in reviews.values() for v in by_country.values()), 'actual_trained_openings_used_as_history': False,
        'scope': criteria['scope'], 'semantic_validation': 'Manual same-author annotations; portable replay verifies bytes/arithmetic, not entailment or independent persona quality.'})
    print(json.dumps({'status': 'pass', 'comparisons': comparisons, 'summaries': summaries}, indent=2))


if __name__ == '__main__': main()
