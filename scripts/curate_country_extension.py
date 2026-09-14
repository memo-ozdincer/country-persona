"""Bind authored policy applications to exact evidence spans in the new release."""
from __future__ import annotations
import json
import re
from collections import defaultdict
from pathlib import Path
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

OUT = Path('data/prepared/country-extension-20260914')


def locate(text, start, end):
    def pattern(anchor):
        return re.escape(anchor).replace(r'\ ', r'\s+')
    starts = list(re.finditer(pattern(start), text))
    if len(starts) != 1:
        raise ValueError(f'Expected one start anchor, found {len(starts)}: {start}')
    a = starts[0].start()
    tail = re.search(pattern(end), text[starts[0].end():])
    if not tail:
        raise ValueError('Missing end anchor: ' + end)
    b = starts[0].end() + tail.end()
    return a, b


def main():
    docs = {r['source_record_id']: r for r in read_jsonl(OUT / 'documents.jsonl')}
    seeds = json.loads(Path('data/curation/country_extension_positions.json').read_text())['positions']
    positions, examples = [], []
    checked = set()
    for seed in seeds:
        doc = docs[seed['source']]
        if doc['id'] not in checked:
            if sha256(doc['extracted_text_file']) != doc['extracted_text_sha256'] or Path(doc['extracted_text_file']).read_text() != doc['text']:
                raise ValueError('Canonical document differs from extracted text')
            checked.add(doc['id'])
        a, b = locate(doc['text'], seed['start'], seed['end'])
        if not set(seed['countries']).issubset(doc['related_countries']):
            raise ValueError('Claim country attribution differs from its source')
        evidence = {'document_id': doc['id'], 'source_url': doc['source_url'],
                    'text_file': doc['extracted_text_file'], 'text_sha256': doc['extracted_text_sha256'],
                    'raw_sha256': doc['raw_sha256'], 'char_start': a, 'char_end': b,
                    'pdf_start_page': doc['text'][:a].count('\f') + 1 if 'pdf_pages' in doc else None,
                    'pdf_end_page': doc['text'][:b].count('\f') + 1 if 'pdf_pages' in doc else None,
                    'language': doc['language']}
        common = {'countries': seed['countries'], 'date': seed['date'], 'issue': seed['issue'],
                  'scope': seed.get('scope'), 'represented_entity': doc['represented_entity'],
                  'group_id': doc['group_id'], 'split_group': doc['split_group'],
                  'proposed_split': doc['proposed_split'], 'split': 'quarantine',
                  'training_admitted': False, 'fresh_evaluation_eligible': False,
                  'review_status': 'assistant_curated_independent_review_pending',
                  'evidence': evidence, 'available_date': doc['available_date']}
        positions.append({'id': seed['id'], 'record_type': 'attributed_policy_claim',
                          'claim': seed['claim'], 'claim_language': 'en',
                          'translation_status': 'assistant_paraphrase_from_original' if doc['language'] != 'en' else 'English_paraphrase',
                          'date_note': seed.get('date_note'), **common})
        source = doc['text'][a:b]
        user = (f"Represented entity: {doc['represented_entity']}\nPolicy date: {seed['date']}\n"
                f"Source language: {doc['language']}\nScope: {seed.get('scope') or 'national public position'}\n"
                f"Evidence [{seed['id']}]:\n{source}\n\nQuestion: {seed['question']}")
        examples.append({'id': seed['id'] + ':application', 'record_type': 'evidence_conditioned_application',
            'derivation': 'assistant_authored_not_authentic_QA_or_model_output',
            'answer_language': 'en', 'enable_thinking': False, 'rubric': seed['inspect'],
            'messages': [{'role': 'system', 'content': 'Answer as a research simulation of the specified institution, using the supplied dated evidence. Preserve conditions, scope and uncertainty. Attribute government claims; do not invent private motives or confuse public statements with independent verification.'},
                         {'role': 'user', 'content': user},
                         {'role': 'assistant', 'content': seed['answer'] + f" [{seed['id']}]"}], **common})
    write_jsonl(OUT / 'policy-positions.candidates.jsonl', positions)
    write_jsonl(OUT / 'policy-applications.candidates.jsonl', examples)
    buckets, manifests = defaultdict(list), defaultdict(list)
    for ex in examples:
        split = ex['proposed_split']
        row = {'prompt': ex['messages'][:-1], 'completion': ex['messages'][-1:],
               'chat_template_kwargs': {'enable_thinking': False}}
        manifests[split].append({'row_index': len(buckets[split]), 'id': ex['id'],
            'split': split, 'split_group': ex['split_group'], 'countries': ex['countries'],
            'country_iso3': ex['countries'][0] if len(ex['countries']) == 1 else None,
            'represented_entity': ex['represented_entity'], 'event_date': ex['date'],
            'source_url': ex['evidence']['source_url'], 'raw_sha256': ex['evidence']['raw_sha256'],
            'example_sha256': digest(row), 'status': 'candidate_not_training_approved',
            'review_status': ex['review_status'], 'rights_status': 'unresolved',
            'quality_flags': ['assistant_authored_application', 'development_demonstration_not_hidden_eval'],
            'derivation': ex['derivation'], 'evidence': ex['evidence']})
        buckets[split].append(row)
    for split, rows in buckets.items():
        write_jsonl(OUT / 'sft-candidates' / f'{split}.jsonl', rows)
        write_jsonl(OUT / 'sft-candidates' / f'{split}.manifest.jsonl', manifests[split])
    facts = list(read_jsonl(OUT / 'country-context.jsonl'))
    write_json(OUT / 'country-dossiers.json', [
        {'country_iso3': c, 'country_name': name,
         'policy_claim_ids': [r['id'] for r in positions if c in r['countries']],
         'context_fact_ids': [r['id'] for r in facts if r['country_iso3'] == c],
         'coverage': 'bounded policy/economic/UN evidence release; not exhaustive country intelligence',
         'training_admitted': False}
        for c, name in [('FRA', 'France'), ('GBR', 'United Kingdom'), ('IND', 'India'), ('BRA', 'Brazil')]])
    lines = ['# Four-country policy applications', '',
        'These are the 12 actual authored candidate examples in the release. They are not observed model outputs or authentic historical Q&A. Every source span is linked in the prepared record; all examples remain review candidates.', '']
    for p, ex, seed in zip(positions, examples, seeds):
        e = ex['evidence']
        lines += [f"## {p['id']}", '',
                  f"**Represented entity:** {ex['represented_entity']} · **Policy date:** {ex['date']} · **Source language:** {e['language']}", '']
        if ex.get('scope'): lines += ['**Scope:** ' + ex['scope'], '']
        lines += ['**Policy claim:** ' + p['claim'], '', '**Question:** ' + seed['question'], '',
                  '**Authored target:** ' + ex['messages'][2]['content'], '',
                  '**Inspect:** ' + '; '.join(ex['rubric']) + '.', '',
                  f"[Official source]({e['source_url']})" +
                  (f" · PDF page {e['pdf_start_page']}" if e['pdf_start_page'] else '') + '.', '']
    Path('docs/COUNTRY_EXTENSION_EXAMPLES.md').write_text('\n'.join(lines) + '\n')
    write_json('reports/country-extension-curation.json', {
        'positions': len(positions), 'authored_applications': len(examples),
        'country_relevance_counts': {code: sum(code in p['countries'] for p in positions) for code in ['FRA', 'GBR', 'IND', 'BRA']},
        'national_claims_by_country': {code: sum(p['countries'] == [code] for p in positions) for code in ['FRA', 'GBR', 'IND', 'BRA']},
        'sft_candidates_by_proposed_split': {s: len(r) for s, r in buckets.items()},
        'cross_language_applications': sum(p['evidence']['language'] != 'en' for p in examples),
        'all_evidence_spans_resolved': True, 'independent_review_complete': False,
        'training_admitted': 0, 'status': 'development_demonstrations_not_hidden_evaluation',
        'artifacts': {str(p): sha256(p) for p in
                      [OUT / 'policy-positions.candidates.jsonl', OUT / 'policy-applications.candidates.jsonl'] +
                      sorted((OUT / 'sft-candidates').glob('*.jsonl'))}})
    print(f'Bound {len(positions)} policy claims and {len(examples)} applications to exact source spans.')


if __name__ == '__main__':
    main()
