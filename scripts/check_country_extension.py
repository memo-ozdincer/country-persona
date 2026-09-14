"""Verify prepared artifacts and Qwen3 formatting on CPU; never admit or train rows."""
import argparse
import json
from pathlib import Path
from country_persona.io import read_jsonl, sha256, digest, write_json

OUT = Path('data/prepared/country-extension-20260914')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tokenizer', default='data/metadata/qwen3-8b-tokenizer')
    args = parser.parse_args()
    docs = {r['id']: r for r in read_jsonl(OUT / 'documents.jsonl')}
    assert len(docs) == 40
    for r in docs.values():
        assert sha256(r['raw_file']) == r['raw_sha256']
        assert sha256(r['extracted_text_file']) == r['extracted_text_sha256']
        assert Path(r['extracted_text_file']).read_text() == r['text']
        if r.get('upr_cycle') == 'Cycle 4': assert r['proposed_split'] == 'test'
    for p in read_jsonl(OUT / 'evidence-passages.jsonl'):
        assert p['text'] == docs[p['parent_id']]['text'][p['start_char']:p['end_char']]
    for r in read_jsonl(OUT / 'policy-positions.candidates.jsonl'):
        e = r['evidence']; parent = docs[e['document_id']]
        assert 0 <= e['char_start'] < e['char_end'] <= len(parent['text'])
        assert sha256(e['text_file']) == e['text_sha256']
    for name in ['documents', 'unga-votes', 'uhri-records', 'unga-speech-segments', 'country-context']:
        seen = set()
        for r in read_jsonl(OUT / f'{name}.jsonl'):
            assert r['id'] not in seen; seen.add(r['id'])
            assert r['split'] == 'quarantine' and not r['training_admitted']
    for report in ['country-extension-20260914', 'country-extension-curation']:
        for p, info in json.loads(Path(f'reports/{report}.json').read_text())['artifacts'].items():
            assert sha256(p) == (info['sha256'] if isinstance(info, dict) else info)
    from transformers import AutoTokenizer
    tpath = Path(args.tokenizer)
    tokenizer = AutoTokenizer.from_pretrained(tpath, local_files_only=True)
    checks = []
    for path in sorted((OUT / 'sft-candidates').glob('*.jsonl')):
        if '.manifest.' in path.name: continue
        rows = list(read_jsonl(path)); metas = list(read_jsonl(path.with_suffix('.manifest.jsonl')))
        assert len(rows) == len(metas)
        for i, (r, m) in enumerate(zip(rows, metas)):
            assert m['row_index'] == i and m['example_sha256'] == digest(r)
            assert m['status'] == 'candidate_not_training_approved'
            kwargs = r['chat_template_kwargs']; assert kwargs == {'enable_thinking': False}
            prompt = tokenizer.apply_chat_template(r['prompt'], tokenize=True, add_generation_prompt=True, **kwargs)
            full = tokenizer.apply_chat_template(r['prompt'] + r['completion'], tokenize=True, add_generation_prompt=False, **kwargs)
            assert full[:len(prompt)] == prompt and 0 < len(full) - len(prompt) and len(full) <= 4096
            checks.append({'id': m['id'], 'proposed_split': m['split'], 'sequence_tokens': len(full),
                           'supervised_tokens': len(full) - len(prompt)})
    write_json('reports/country-extension-token-preflight.json', {
        'model': 'Qwen/Qwen3-8B', 'tokenizer_files': {str(p): sha256(p) for p in sorted(tpath.glob('*')) if p.is_file()},
        'enable_thinking': False, 'max_length': 4096, 'candidate_rows': len(checks),
        'sequence_tokens': sum(r['sequence_tokens'] for r in checks),
        'supervised_tokens': sum(r['supervised_tokens'] for r in checks),
        'max_sequence_tokens': max(r['sequence_tokens'] for r in checks),
        'four_h100_node_hours': 0, 'training_admitted': 0, 'rows': checks})
    print('Source spans, hashes, quarantine and Qwen3 prompt/completion boundaries verified; no training launched.')


if __name__ == '__main__':
    main()
