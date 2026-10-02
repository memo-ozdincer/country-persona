"""Replay byte, pairing and stored-rating checks; this does not rejudge semantics."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256
from country_persona.probe_checks import validate_cases, verify_matched_inputs


def verify(root):
    source = root / 'data/raw/source-plan-grounding-20261002-v1'
    acquisition = json.loads((source / 'acquisition.json').read_text())
    for name, expected in acquisition['files_sha256'].items():
        assert sha256(source / name) == expected, name
    assert all(x['equal'] for x in acquisition['coverage'])
    text = (source / 'record-9214.txt').read_text()
    for country, s in json.loads((source / 'statements.json').read_text()).items():
        assert text[s['start']:s['end']].strip() == s['text']
        assert digest(s['text']) == s['text_digest']
        if country == 'IND':
            assert 'I now resume my functions' not in s['text']
    summaries = []
    for kind, count, design in [('probe', 8, 'raw_vs_plan'), ('repair', 4, 'checked_plan_repair_only')]:
        run_dir = root / f'runs/aurora-qwen35-source-plan-{kind}-20261002-v1'
        run = json.loads((run_dir / 'run.json').read_text())
        assert run['completed_calls'] == count and run['new_training_steps'] == 0
        config = run['config']
        pack = root / config['eval_pack']
        manifest = json.loads((pack / 'manifest.json').read_text())
        assert sha256(pack / 'manifest.json') == config['eval_pack_manifest_sha256']
        for name, expected in manifest['files_sha256'].items():
            assert sha256(pack / name) == expected, name
        for name, expected in manifest['source_files_sha256'].items():
            assert sha256(root / name) == expected, name
        for name, expected in run['source_code_sha256'].items():
            assert sha256(run_dir / 'source' / Path(name).name) == expected, name
        cases = list(read_jsonl(pack / 'cases.jsonl'))
        validate_cases(cases, design)
        transcript = list(read_jsonl(run_dir / 'transcript.jsonl'))
        verify_matched_inputs(transcript, count)
        assert not any(r['hit_output_cap'] for r in transcript)
        assert sha256(run_dir / 'transcript.jsonl') == run['transcript_sha256']
        review = json.loads((run_dir / 'inspection.json').read_text())
        assert review['transcript_sha256'] == run['transcript_sha256']
        assert review['frozen_spec_sha256'] == manifest['spec_sha256'] == sha256(pack / 'spec.json')
        spec = json.loads((pack / 'spec.json').read_text())
        by_id = {r['response_id']:r for r in transcript}
        assert len(review['responses']) == count
        assert {r['response_id'] for r in review['responses']} == set(by_id)
        for r in review['responses']:
            output = by_id[r['response_id']]['output']
            import hashlib
            assert hashlib.sha256(output.encode()).hexdigest() == r['output_sha256']
            criteria = {u[0]:u[1] for u in spec['countries'][r['country']]['units'] + spec['universal_units']}
            assert {x['unit'] for x in r['ratings']} == set(criteria)
            assert len(r['ratings']) == len(criteria)
            for rating in r['ratings']:
                assert rating['criterion'] == criteria[rating['unit']]
                assert rating['status'] in {'met','unmet','unratable'}
                if rating['output_quote'] is not None:
                    assert rating['output_quote'] in output
            counts = Counter(x['status'] for x in r['ratings'])
            assert r['counts'] == {k:counts[k] for k in ('met','unmet','unratable')}
            result = 'fail' if counts['unmet'] else 'unresolved' if counts['unratable'] else 'pass'
            assert result == r['strict_result']
        if kind == 'repair':
            predecessor = root / config['prerequisite_inspection']
            assert sha256(predecessor) == config['prerequisite_inspection_sha256']
            assert datetime.fromisoformat(json.loads(predecessor.read_text())['created_utc']) < datetime.fromisoformat(manifest['created_at'])
        summaries.append({'kind':kind,'calls':count,'ratings':count*12,'matched_tokens':True,
                          'strict_passes':sum(r['strict_result']=='pass' for r in review['responses']),
                          'peak_allocated_gpu_gib':run['peak_allocated_gpu_gib']})
    return {'status':'source_pack_pairing_and_stored_review_replay_verified',
            'new_model_calls':12,'new_optimizer_steps':0,'comparisons':summaries,
            'independent_semantic_review':False,'persona_quality_claim':False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    print(json.dumps(verify(p.parse_args().root.resolve()), indent=2))
