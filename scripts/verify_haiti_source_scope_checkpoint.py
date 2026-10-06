"""Replay source deletion, native tokens, matched protocol and stored four-answer annotations."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    pack = ROOT / 'data/prepared/haiti-source-scope-20261006-v1'
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    assert not manifest['training_authorized_for_this_pack'] and manifest['training_examples'] == 0
    provenance = json.loads((pack / 'provenance.json').read_text())
    parent = ROOT / provenance['parent_pack']
    assert sha256(parent / 'manifest.json') == provenance['parent_manifest_sha256']
    assert sha256(parent / 'cases.jsonl') == provenance['parent_cases_sha256']
    assert sha256(pack / 'criteria.json') == sha256(parent / 'criteria.json') == provenance['criteria_sha256']
    original = {c['id']: c for c in read_jsonl(parent / 'cases.jsonl')}
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    criteria = json.loads((pack / 'criteria.json').read_text())
    sources = json.loads((pack / 'haiti-statements.json').read_text())
    sourceproof = json.loads((pack / 'haiti-source-proof.json').read_text())
    raw = ROOT / sourceproof['raw_directory']
    for name, expected in sourceproof['files_sha256'].items():
        assert sha256(raw / name) == expected
    record = (raw / 'record-9430.txt').read_text()
    for source in sources.values():
        assert record[source['start']:source['end']].strip() == source['raw_text']
        assert digest(source['raw_text']) == source['raw_text_digest']
        assert re.sub('\u00ad\\s*', '', source['raw_text']) == source['text']
        assert digest(source['text']) == source['text_digest']
    blocks = {co: 'COMPLETE NATIONAL POST-VOTE STATEMENT — ' + co +
              ' — S/PV.9430, 2 October2023\n' + s['text'] for co, s in sources.items()}
    combined = '\n\n'.join(blocks.values())
    from transformers import AutoTokenizer
    adapter = ROOT / 'runs/aurora-conditional-india-fit-20261006-v2/adapter'
    saved = json.loads((adapter.parent / 'run.json').read_text())['serialization_checks']['files_sha256']
    for name in ['adapter_model.safetensors', 'adapter_config.json']:
        assert sha256(adapter / name) == saved[name]
    # Saved tokenizer bytes were bound by the verified v26 snapshot before new calls.
    tokenizer_sha256 = {
        'tokenizer.json': '06b9509352d2af50381ab2247e083b80d32d5c0aba91c272ca9ff729b6a0e523',
        'tokenizer_config.json': 'bee8eba30f0eb4af73c0fe2cd06d0f89b657d7819941c438157ec42f7c80ea87',
        'chat_template.jinja': 'a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715'}
    for name, expected in tokenizer_sha256.items():
        assert sha256(adapter / name) == expected
    tok = AutoTokenizer.from_pretrained(adapter, local_files_only=True)
    assert len(cases) == 2
    for case, change in zip(cases, provenance['changes'], strict=True):
        old = original[case['id']]
        assert old['prompt'][1]['content'].endswith(combined)
        prefix = old['prompt'][1]['content'][:-len(combined)]
        assert case['prompt'][0] == old['prompt'][0]
        assert case['prompt'][1]['content'] == prefix + blocks[case['country_iso3']]
        assert change['prefix_digest'] == digest(prefix) and change['new_prompt_digest'] == digest(case['prompt'])
        assert change['old_prompt_digest'] == digest(old['prompt'])
        assert change['own_block_digest'] == digest(blocks[case['country_iso3']])
        assert case['condition'] == 'raw_own_statement_only'
        for key in set(old) - {'prompt', 'input_ids', 'input_ids_digest', 'condition'}:
            assert case[key] == old[key]
    summaries, resources = {}, {}
    new_generations, tokens, seconds = 0, 0, 0.0
    for arm in ['base', 'adapter']:
        newdir = ROOT / f'runs/aurora-haiti-source-scope-{arm}-20261006-v1'
        olddir = ROOT / provenance['comparison_runs'][arm]
        summaries[arm] = {}
        newcfg = json.loads((ROOT / f'configs/posttraining/qwen35-haiti-source-scope-{arm}-20261006-v1.json').read_text())
        actual = json.loads((newdir / 'run.json').read_text())
        assert actual['config'] == newcfg and actual['config_sha256'] == sha256(ROOT / f'configs/posttraining/qwen35-haiti-source-scope-{arm}-20261006-v1.json')
        assert actual['pack_manifest_sha256'] == sha256(pack / 'manifest.json')
        assert actual['manual_inspection_sha256'] == sha256(pack / 'manual-inspection.json')
        assert actual['mode'] == arm and actual['optimizer_steps'] == 0
        previous = ROOT / ('runs/aurora-conditional-india-fit-20261006-v2' if arm == 'base'
                           else 'runs/aurora-haiti-source-scope-base-20261006-v1')
        assert Path(actual['previous_inspected_run']['run']).resolve() == previous
        assert actual['previous_inspected_run']['inspection_sha256'] == sha256(previous / 'inspection.json')
        if arm == 'adapter':
            assert actual['loaded_adapter_sha256'] == saved['adapter_model.safetensors']
        resources[arm] = {'run_directory': str(newdir), 'identity': actual['identity'], 'gpu': actual['gpu']}
        for scope, directory in [('combined', olddir), ('own', newdir)]:
            run = json.loads((directory / 'run.json').read_text())
            inspection = json.loads((directory / 'inspection.json').read_text())
            assert run['status'] == 'completed' and inspection['all_outputs_read_complete']
            assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
            assert inspection['criteria_sha256'] == sha256(pack / 'criteria.json')
            assert run['versions'] == newcfg['runtime_pins']
            assert run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
            for key in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
                assert run['config'][key] == newcfg[key]
            assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
            for source, expected in run['source_code_sha256'].items():
                assert sha256(directory / Path(source).name) == expected
            if arm == 'base':
                assert run['mode'] == 'base'
            elif scope == 'combined':
                assert run['serialization_checks']['files_sha256']['adapter_model.safetensors'] == newcfg['adapter_sha256']
            rows = {r['id']: r for r in read_jsonl(directory / 'transcript.jsonl')}
            reviews = {r['id']: r for r in inspection['reviews']}
            if scope == 'own':
                assert set(rows) == set(reviews) == {c['id'] for c in cases}
            results = {}
            for case in cases:
                selected = original[case['id']] if scope == 'combined' else case
                row, review = rows[case['id']], reviews[case['id']]
                ids = tok.apply_chat_template(selected['prompt'], tokenize=True, return_dict=False,
                                             add_generation_prompt=True, **newcfg['chat_template_kwargs'])
                assert ids == selected['input_ids'] == row['input_ids']
                assert digest(ids) == row['input_ids_digest']
                assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
                assert len(row['output_ids']) == row['generated_tokens']
                assert row['at_output_cap'] == (row['generated_tokens'] == newcfg['generation_max_new_tokens'])
                assert hashlib.sha256(row['output'].encode()).hexdigest() == review['output_sha256']
                assert review['all_output_read_complete']
                expected = set(criteria['haiti']['source_units'][case['country_iso3']]) | set(criteria['haiti']['common_units'])
                assert set(review['ratings']) == expected
                assert set(review['universal_checks']) == set(criteria['universal_checks'])
                values = list(review['ratings'].values()) + list(review['universal_checks'].values())
                assert all(v['status'] in {'met', 'unmet', 'unratable'} and v['reason'].strip() for v in values)
                results[case['id']] = {'met': sum(v['status'] == 'met' for v in review['ratings'].values()),
                    'unratable': sum(v['status'] == 'unratable' for v in review['ratings'].values()),
                    'units': len(expected), 'words': len(row['output'].split()), 'at_cap': row['at_output_cap'],
                    'universal_met': sum(v['status'] == 'met' for v in review['universal_checks'].values()),
                    'strict_pass': all(v['status'] == 'met' for v in values) and not row['at_output_cap'] and len(row['output'].split()) <= 300}
                if scope == 'own':
                    new_generations += 1; tokens += row['generated_tokens']; seconds += row['generation_seconds']
            summaries[arm][scope] = results
    assert new_generations == 4
    write_json(args.output, {'status': 'source_deletion_tokens_protocol_weights_four_answers_and_stored_annotations_replayed',
        'new_model_generations': new_generations, 'new_optimizer_steps': 0, 'generated_tokens': tokens,
        'generation_seconds': seconds, 'summary': summaries, 'resources': resources,
        'cumulative_aurora_qwen35_steps': 1246, 'reference_qwen25_steps': 582,
        'independent_review_complete': False, 'scope': provenance['scope']})
    print(json.dumps({'status': 'replayed', 'summary': summaries, 'new_model_generations': new_generations}, indent=2))


if __name__ == '__main__':
    main()
