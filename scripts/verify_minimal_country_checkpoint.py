"""Portable byte/pairing/optimization/stored-annotation replay; no new semantic judgment."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json

def verify(pack, base, fit):
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if sha256(pack / name) != expected:
            raise ValueError('Changed frozen data: ' + name)
    sources = json.loads((pack / 'sources.json').read_text())
    original = ROOT / sources['original_source']
    if sha256(original) != sources['sha256'] or json.loads(original.read_text()) != sources['statements']:
        raise ValueError('Source statements differ from archived primary extraction')
    rows = list(read_jsonl(pack / 'train.jsonl')); cases = list(read_jsonl(pack / 'cases.jsonl'))
    identifiers = [c['id'] for c in cases]
    if len(set(identifiers)) != len(cases):
        raise ValueError('Duplicate evaluation IDs')
    for row in rows + cases:
        for statement in sources['statements'].values():
            if statement['text'] not in row['prompt'][1]['content']:
                raise ValueError('Incomplete source in student prompt')
    train_prompts = {digest(r['prompt']) for r in rows}
    for case in cases:
        in_train = digest(case['prompt']) in train_prompts
        if in_train != (case['family'] == 'exact_control'):
            raise ValueError('Held wording leaked into training or exact control changed')
    criteria = json.loads((pack / 'criteria.json').read_text())
    summaries = {}
    transcripts = {}
    for arm, directory in [('base', base), ('fit', fit)]:
        run = json.loads((directory / 'run.json').read_text())
        if run['status'] != 'completed' or run['pack_manifest_sha256'] != sha256(pack / 'manifest.json'):
            raise ValueError('Incomplete or different-pack run')
        for source_name, expected in run['source_code_sha256'].items():
            if sha256(directory / Path(source_name).name) != expected:
                raise ValueError('Archived launch source differs: ' + source_name)
        transcript = list(read_jsonl(directory / 'transcript.jsonl'))
        if [r['id'] for r in transcript] != identifiers:
            raise ValueError('Missing/reordered outputs')
        if sha256(directory / 'transcript.jsonl') != run['transcript_sha256']:
            raise ValueError('Changed generated transcript')
        review = json.loads((directory / 'inspection.json').read_text())
        if review['transcript_sha256'] != run['transcript_sha256'] or review['criteria_sha256'] != sha256(pack / 'criteria.json'):
            raise ValueError('Unbound stored review')
        if not review['all_outputs_read_complete'] or [r['id'] for r in review['reviews']] != identifiers:
            raise ValueError('Incomplete assistant inspection record')
        groups = {}
        for case, output, rating in zip(cases, transcript, review['reviews']):
            import hashlib
            if rating['output_sha256'] != hashlib.sha256(output['output'].encode()).hexdigest():
                raise ValueError('Rating points to different answer text')
            if digest(output['input_ids']) != output['input_ids_digest']:
                raise ValueError('Invalid input-token digest')
            if set(rating['ratings']) != set(criteria['units']):
                raise ValueError('Changed unit inventory')
            group = groups.setdefault(case['family'], {'met': 0, 'unmet': 0, 'unratable': 0,
                'rubric_conjunction_passes': 0, 'outputs': 0, 'additional_source_observations': 0})
            group['outputs'] += 1
            group['additional_source_observations'] += len(rating['additional_source_fidelity_observations'])
            for unit in rating['ratings'].values():
                if unit['status'] not in ('met', 'unmet', 'unratable'):
                    raise ValueError('Invalid annotation status')
                group[unit['status']] += 1
            group['rubric_conjunction_passes'] += int(all(u['status'] == 'met' for u in rating['ratings'].values())
                                                    and not output['at_output_cap'])
        summaries[arm] = groups
        transcripts[arm] = transcript
    if [r['input_ids_digest'] for r in transcripts['base']] != [r['input_ids_digest'] for r in transcripts['fit']]:
        raise ValueError('Unmatched generated inputs')
    base_record = json.loads((base / 'run.json').read_text())
    fit_record = json.loads((fit / 'run.json').read_text())
    if (base_record['versions'], base_record['gpu']['name']) != (fit_record['versions'], fit_record['gpu']['name']):
        raise ValueError('Runtime/hardware mismatch')
    for report in fit_record['optimization_checks']['rank_checks']:
        if report['steps'] != fit_record['config']['max_steps'] or report['gradient_checks'] != report['steps']:
            raise ValueError('Missing actual optimization steps/gradient checks')
        if not report['changed_adapter_tensors'] or not report['actual_target_tokens']:
            raise ValueError('Training did not update supervised adapter')
    for name, expected in fit_record['serialization_checks']['files_sha256'].items():
        if sha256(fit / 'adapter' / name) != expected:
            raise ValueError('Changed fitted weights')
    return {'status': 'portable_replay_passed', 'scope': 'Bytes, source inclusion, wording separation, matched inputs, saved optimization/serialization evidence and arithmetic of stored assistant annotations. Does not independently validate semantics.',
            'training_examples': len(rows), 'matched_cases': len(cases), 'summary': summaries,
            'actual_steps': fit_record['optimization_checks']['rank_checks'][0]['steps'],
            'all_outputs_complete': all(not r['at_output_cap'] for rows in transcripts.values() for r in rows),
            'pack_manifest_sha256': sha256(pack / 'manifest.json'),
            'base_run_sha256': sha256(base / 'run.json'), 'fit_run_sha256': sha256(fit / 'run.json')}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--fit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.pack, args.base, args.fit)
    write_json(args.output, result)
    print(json.dumps(result, indent=2))
