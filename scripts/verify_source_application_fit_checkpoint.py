"""Replay frozen bytes, pairing, measured steps and stored annotations; no semantic rejudging."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256
from country_persona.application_fit_checks import validate_design, match_references


def verify(root):
    train = root / 'data/prepared/source-application-sft-20261003-v2'
    evaluation = root / 'data/prepared/source-application-eval-20261003-v2'
    release = json.loads((train / 'release.json').read_text())
    manifest = json.loads((evaluation / 'manifest.json').read_text())
    for directory, m in ((train, release), (evaluation, manifest)):
        for name, h in m['files_sha256'].items():
            assert sha256(directory / name) == h, name
    for name, h in manifest['source_files_sha256'].items():
        assert sha256(root / name) == h, name
    rows = list(read_jsonl(train / 'train.jsonl'))
    metadata = list(read_jsonl(train / 'train.manifest.jsonl'))
    teachers = list(read_jsonl(train / 'teacher-records.jsonl'))
    cases = list(read_jsonl(evaluation / 'cases.jsonl'))
    validate_design(rows, metadata, teachers, cases, manifest['heldout_family'])
    assert all(digest(r) == m['example_sha256'] for r, m in zip(rows, metadata))
    sources = {('san', c): s['text'] for c, s in json.loads((root / 'data/raw/source-plan-grounding-20261002-v1/statements.json').read_text()).items()}
    sources.update({('clim', r['id'].split('-')[-1].upper()): r['text']
        for r in read_jsonl(root / 'data/prepared/evidence-format-20260928-v1/evidence.jsonl') if r['id'].startswith('climate-')})
    for a in json.loads((train / 'source-anchor-audit.json').read_text())['anchors']:
        s = sources[(a['family'], a['country'])]
        assert s[a['start']:a['end']] == a['quote'] and digest(s) == a['source_text_digest']
    source = root / 'data/raw/source-application-grounding-20261003-v1'
    acquisition = json.loads((source / 'acquisition.json').read_text())
    for name, h in acquisition['files_sha256'].items():
        assert sha256(source / name) == h, name
    assert len(acquisition['body_column_coverage']) == 102
    assert all(x['equal'] for x in acquisition['body_column_coverage'])
    held = json.loads((source / 'statements.json').read_text())
    text = (source / 'record-8514.txt').read_text()
    for s in held.values():
        assert text[s['start']:s['end']].strip() == s['text'] and digest(s['text']) == s['text_digest']
    for a in json.loads((evaluation / 'source-criterion-audit.json').read_text())['anchors']:
        s = held[a['country']]['text']
        assert s[a['start']:a['end']] == a['quote'] and digest(s) == a['source_text_digest']
    by_case = {c['id']: c for c in cases}
    old_spec = json.loads((root / 'configs/posttraining/qwen35-source-plan-spec-20261002.json').read_text())
    summaries = []
    transcripts = {}
    records = {}
    for mode in ('base', 'fit'):
        directory = root / f'runs/aurora-qwen35-source-application-{mode}-20261003-v1'
        run = json.loads((directory / 'run.json').read_text())
        records[mode] = run
        assert run['status'] == ('source_application_base_six_completed' if mode == 'base' else 'source_application_fit_and_six_completed')
        assert run['completed_calls'] == 6 and run['new_training_steps'] == (0 if mode == 'base' else 20)
        assert run['config']['training_release_sha256'] == sha256(train / 'release.json')
        assert run['config']['eval_manifest_sha256'] == sha256(evaluation / 'manifest.json')
        assert datetime.fromisoformat(manifest['created_utc']) < datetime.fromisoformat(run['created_at'])
        for name, h in run['source_code_sha256'].items():
            assert sha256(directory / 'source' / Path(name).name) == h
        transcript = list(read_jsonl(directory / 'transcript.jsonl'))
        assert len(transcript) == len({r['id'] for r in transcript}) == 6
        assert sha256(directory / 'transcript.jsonl') == run['transcript_sha256']
        for r in transcript:
            assert digest(r['input_ids']) == r['input_ids_digest']
            assert digest(r['output_ids']) == r['output_digest']
            assert r['case_sha256'] == by_case[r['id']]['case_sha256']
            assert not r['hit_output_cap']
        transcripts[mode] = transcript
        review = json.loads((directory / 'inspection.json').read_text())
        assert review['transcript_sha256'] == run['transcript_sha256']
        assert review['frozen_criteria_sha256'] == sha256(evaluation / 'criteria.json')
        assert review['all_six_complete_answers_inspected'] and len(review['responses']) == 6
        outputs = {r['id']: r for r in transcript}
        assert {r['response_id'] for r in review['responses']} == set(outputs)
        for r in review['responses']:
            output = outputs[r['response_id']]['output']
            assert hashlib.sha256(output.encode()).hexdigest() == r['output_sha256']
            c = by_case[r['response_id']]
            criteria = {u[0]: u[1] for u in (c['units'] if c['condition'] != 'training_control' else
                old_spec['countries'][c['country_iso3']]['units'] + old_spec['universal_units'])}
            assert len(r['ratings']) == len(criteria) == 12
            assert {x['unit'] for x in r['ratings']} == set(criteria)
            for rating in r['ratings']:
                assert rating['criterion'] == criteria[rating['unit']]
                assert rating['status'] in {'met', 'unmet', 'unratable'}
                if rating['output_quote'] is not None:
                    assert rating['output_quote'] in output
            counts = Counter(x['status'] for x in r['ratings'])
            assert r['counts'] == {k: counts[k] for k in ('met', 'unmet', 'unratable')}
            assert r['strict_result'] == ('fail' if counts['unmet'] else 'unresolved' if counts['unratable'] else 'pass')
        groups = {}
        for condition in sorted({c['condition'] for c in cases}):
            rs = [r for r in review['responses'] if by_case[r['response_id']]['condition'] == condition]
            if rs:
                groups[condition] = {'answers': len(rs), 'met': sum(r['counts']['met'] for r in rs),
                    'unmet': sum(r['counts']['unmet'] for r in rs), 'unratable': sum(r['counts']['unratable'] for r in rs),
                    'strict_passes': sum(r['strict_result'] == 'pass' for r in rs)}
        summaries.append({'mode': mode, 'groups': groups})
    base = records['base']; fit = records['fit']
    assert base['versions'] == fit['versions'] and base['gpu']['name'] == fit['gpu']['name']
    assert base['generation_config'] == fit['generation_config']
    helper = 'scripts/run_aurora_qwen35_smoke.py'
    assert base['source_code_sha256'][helper] == fit['source_code_sha256'][helper]
    historical = list(read_jsonl(root / 'runs/aurora-qwen35-source-application-base-20261003-v1/historical-controls.jsonl'))
    original_dir = root / 'runs/aurora-qwen35-source-plan-probe-20261002-v1'
    original = list(read_jsonl(original_dir / 'transcript.jsonl'))
    for mode, record in records.items():
        d = root / f'runs/aurora-qwen35-source-application-{mode}-20261003-v1'
        receipt = record['historical_controls']
        assert sha256(original_dir / 'run.json') == receipt['run_sha256']
        assert sha256(original_dir / 'transcript.jsonl') == receipt['transcript_sha256']
        assert sha256(d / 'historical-controls.jsonl') == receipt['controls_sha256']
    for row in historical:
        matches = [r for r in original if r['arm'] == 'base' and r['id'] == row['historical_case_id']]
        assert len(matches) == 1
        assert row['output_ids'] == matches[0]['output_ids'] and row['input_ids'] == matches[0]['input_ids']
    references = {r['id']: r for r in transcripts['base'] if r['condition'] == 'raw'}
    references.update({r['id']: r for r in historical})
    match_references(transcripts['fit'], references)
    assert fit['matched_input_digests']
    config = fit['config']
    baseline_dir = root / config['baseline_run']
    for name, key in (('run.json', 'baseline_run_sha256'), ('transcript.jsonl', 'baseline_transcript_sha256'), ('inspection.json', 'baseline_inspection_sha256')):
        assert sha256(baseline_dir / name) == config[key]
    assert datetime.fromisoformat(json.loads((baseline_dir / 'inspection.json').read_text())['created_utc']) < datetime.fromisoformat(fit['created_at'])
    assert fit['mask_audit']['actual_trainer_masks_checked'] and fit['mask_audit']['rows'] == 20
    check = fit['optimization_checks']['rank_checks'][0]
    assert check['steps'] == check['gradient_checks'] == 20
    assert check['all_adapter_tensors_finite'] and check['changed_adapter_tensors'] > 0
    serial = fit['serialization_checks']
    assert serial['saved_tensors_equal'] and serial['reload_verified_after_state_perturbation'] and serial['same_base_probe_logits_equal']
    for name, h in serial['files_sha256'].items():
        assert sha256(root / 'runs/aurora-qwen35-source-application-fit-20261003-v1/adapter' / name) == h
    return {'status': 'source_application_fit_bytes_pairing_steps_stored_review_replay_verified',
            'new_model_answers': 12, 'new_optimizer_steps': 20, 'reused_historical_base_answers': 2,
            'stored_annotations': 144, 'summaries': summaries, 'independent_semantic_review': False,
            'persona_or_multi_agent_gain_established': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    print(json.dumps(verify(p.parse_args().root.resolve()), indent=2))
