"""Small auditable country-knowledge layer; no automatic SFT admission or GPU use.

Run from the repository root after acquiring the source snapshot. The source lock
written by the first build allows source-hash verification on every later build.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

from country_persona.acquire import download
from country_persona.io import sha256, write_json, write_jsonl

VERSION = 'country-knowledge-20260914'
RAW = Path('data/raw') / VERSION
OUT = Path('data/prepared') / VERSION
LOCK = Path('data/manifests') / f'{VERSION}.json'
COUNTRIES = {'CHN': 'China', 'DEU': 'Germany', 'FRA': 'France',
             'GBR': 'United Kingdom', 'IND': 'India', 'BRA': 'Brazil'}
GATE = {'split': 'quarantine', 'training_admitted': False,
        'review_status': 'author_checked_independent_review_pending',
        'fresh_evaluation_eligible': False}


def normalize(text):
    return re.sub(r'\s+', ' ', text.replace('\u00ad', '').replace('\x07', '').replace('\x08', '')).strip()


def source_span(source, start, end=None, *, end_before=None):
    """Unique start and end anchors bound evidence, never another speaker's turn."""
    text = source['_text']
    if text.count(start) != 1:
        raise ValueError(f"Nonunique/missing start in {source['id']}: {start}")
    a = text.index(start)
    if end_before:
        b = text.index(end_before, a + len(start))
    elif end == start or not end:
        b = a + len(start)
    else:
        b = text.index(end, a + len(start)) + len(end)
    return {'source_id': source['id'], 'text_file': source['text_file'],
            'text_sha256': source['text_sha256'], 'char_start': a, 'char_end': b,
            'pdf_pages': sorted({p['page'] for p in source.get('pages', [])
                                 if p['end'] > a and p['start'] < b})}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = json.loads(Path('data/curation/country_knowledge_seed.json').read_text())
    sources = {}
    accepted = ['world_bank_2024.json', 'france_unsc.html', 'india_brazil_joint_2025.html',
                'uk_unsc_2024.json', 'es11_1.pdf', 'es11_pv5.pdf']
    accepted += [f'metadata_{i}.json' for i in ['SP.POP.TOTL', 'NY.GDP.MKTP.CD', 'NE.TRD.GNFS.ZS']]
    paths = [(Path('data/raw/unga_dm/votes.csv'), 'unga_dm_votes')]
    paths += [(RAW / name, name.rsplit('.', 1)[0]) for name in accepted]
    for old_id, source_id in [('germany_china_strategy-en', 'germany_china_strategy'),
                              ('china_development_whitepaper_2021-en', 'china_development_whitepaper')]:
        paths.append((Path('data/raw/expansion-20260913/national_policy_documents') / f'{old_id}.pdf', source_id))

    for path, source_id in paths:
        receipt = json.loads(path.with_name(path.name + '.receipt.json').read_text())
        if sha256(path) != receipt['sha256']:
            raise ValueError(f'Raw hash mismatch: {path}')
        s = {'id': source_id, 'raw_file': str(path), **receipt,
             'source_language': 'en', 'rights_status': 'see_original_source_terms_not_blanket_cleared'}
        s.pop('source_id', None)
        if path.suffix == '.pdf':
            if not path.read_bytes().startswith(b'%PDF-'):
                raise ValueError(f'Not a PDF: {path}')
            # Default reading order, not -layout: the UN transcript uses two columns.
            raw_text = subprocess.check_output(['pdftotext', str(path), '-'], text=True)
            pages = [normalize(p) for p in raw_text.split('\f')]
            if pages and not pages[-1]:
                pages.pop()
            s['pages'], pos = [], 0
            for number, page in enumerate(pages, 1):
                s['pages'].append({'page': number, 'start': pos, 'end': pos + len(page)})
                pos += len(page) + 1
            text = ' '.join(pages)
            s['extraction'] = 'pdftotext default reading order; whitespace/soft-hyphen/control normalization per page'
        elif path.suffix == '.html':
            soup = BeautifulSoup(path.read_text(), 'html.parser')
            for node in soup(['script', 'style', 'nav', 'footer', 'header']):
                node.decompose()
            text = normalize(soup.get_text(' ', strip=True))
            s['extraction'] = 'BeautifulSoup visible text; claim spans only, not whole-page training'
        elif source_id == 'uk_unsc_2024':
            obj = json.loads(path.read_text())
            text = normalize(BeautifulSoup(obj['details']['body'], 'html.parser').get_text(' ', strip=True))
            s['extraction'] = 'GOV.UK Content API details.body'
            s['speech_type'] = obj['details']['speech_type_explanation']
            s['event_date'] = obj['details']['delivered_on'][:10]
            s['available_date'] = obj['details']['first_public_at'][:10]
        else:
            text = None
        if text is not None:
            text_path = OUT / 'source-text' / f'{source_id}.txt'
            text_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_text(text)
            s.update(text_file=str(text_path), text_sha256=sha256(text_path), _text=text)
        sources[source_id] = s

    if LOCK.exists():
        locked = json.loads(LOCK.read_text())
        expected = {s['id']: s['sha256'] for s in locked['sources']}
        actual = {s['id']: s['sha256'] for s in sources.values()}
        if expected != actual:
            raise ValueError('Frozen source manifest changed; create a new version explicitly')

    policies = []
    for seed in seeds['policies']:
        s = sources[seed['source']]
        evidence = source_span(s, seed['start'], seed['end'])
        policies.append({k: v for k, v in seed.items() if k not in ['start', 'end', 'source']} |
                        {'record_type': 'stated_policy', 'evidence': [evidence], **GATE,
                         'source_url': s['url'], 'retrieved_at': s['retrieved_at'],
                         'available_date': s.get('available_date'),
                         'truth_scope': 'attributed public position; implementation not independently verified',
                         'group_id': ('policy:china_development_whitepaper_2021' if
                                      seed['source'] == 'china_development_whitepaper' else
                                      f"policy:{seed['source']}")})

    wb = json.loads((RAW / 'world_bank_2024.json').read_text())
    if len(wb) != 2 or wb[0]['pages'] != 1 or wb[0]['total'] != 18:
        raise ValueError('Unexpected/incomplete World Bank response')
    facts = []
    units = {'SP.POP.TOTL': 'persons', 'NY.GDP.MKTP.CD': 'current_USD', 'NE.TRD.GNFS.ZS': 'percent_of_GDP'}
    for index, r in enumerate(wb[1]):
        indicator = r['indicator']['id']
        metadata = json.loads((RAW / f'metadata_{indicator}.json').read_text())[1][0]
        facts.append({'id': f"WDI-{r['countryiso3code']}-{indicator}-{r['date']}",
                      'record_type': 'country_statistic', 'country_iso3': r['countryiso3code'],
                      'indicator': indicator, 'label': r['indicator']['value'],
                      'value': r['value'], 'missing': r['value'] is None, 'unit': units[indicator],
                      'reference_year': int(r['date']), 'database_last_updated': wb[0]['lastupdated'],
                      'retrieved_at': sources['world_bank_2024']['retrieved_at'],
                      'available_at_reference_year': None, 'source_id': 'world_bank_2024',
                      'source_pointer': f'/1/{index}', 'source_url': sources['world_bank_2024']['url'],
                      'definition': metadata['sourceNote'], 'upstream_organization': metadata['sourceOrganization'],
                      'use': 'dated background context; not a political preference or causal explanation', **GATE})
    assert len({f['id'] for f in facts}) == 18

    # Keep the full adopted resolution and primary roll call with the derived vote.
    transcript = sources['es11_pv5']
    official = transcript['_text']
    yes = official.split('In favour:', 1)[1].split('Against:', 1)[0]
    abstain = official.split('Abstaining:', 1)[1].split('The draft resolution', 1)[0]
    labels = {normalize(name): 'in favor' for name in yes.split(',')}
    labels.update({normalize(name): 'abstaining' for name in abstain.split(',')})
    explanation_seeds = {r['country_iso3']: r for r in seeds['explanations']}
    by_name = {v: k for k, v in COUNTRIES.items()}
    actions = []
    with Path('data/raw/unga_dm/votes.csv').open() as f:
        for row_number, r in enumerate(csv.DictReader(f), 2):
            if r['resolution_id'] != 'A/RES/ES-11/1' or r['member_state'] not in by_name:
                continue
            code = by_name[r['member_state']]
            seat = r['current_seat_name']
            if labels.get(seat) != r['original_vote']:
                raise ValueError(f'Primary roll call mismatch: {seat}')
            explanation = explanation_seeds.get(code)
            actions.append({'id': f"{code}-ES-11-1-20220302", 'record_type': 'observed_vote',
                            'country_iso3': code, 'date': r['meeting_date'],
                            'decision_id': r['decision_id'], 'group_id': 'unga:decision:A/RES/ES-11/1-FP',
                            'document_symbols': ['A/RES/ES-11/1', 'A/ES-11/PV.5', 'A/ES-11/L.1'],
                            'original_vote': r['original_vote'], 'amended_vote': r['amended_vote'],
                            'bulk_source_id': 'unga_dm_votes', 'csv_line': row_number,
                            'proposal_source_id': 'es11_1', 'primary_vote_source_id': 'es11_pv5',
                            'primary_vote_pdf_pages': [14, 15], 'primary_roll_call_verified': True,
                            'public_explanation_summary': explanation['summary'] if explanation else None,
                            'explanation_evidence': source_span(transcript, explanation['start'],
                                end_before=explanation['end_before']) if explanation else None,
                            'explanation_text_language': 'en' if explanation else None,
                            'language_of_delivery': explanation.get('language_of_delivery') if explanation else None,
                            'explanation_status': 'located' if explanation else 'not_acquired_in_this_snapshot',
                            'evaluation_use': 'retrospective demonstration, not a blind historical forecast',
                            'private_motive': None, **GATE})
    assert {a['country_iso3'] for a in actions} == set(COUNTRIES) and len(actions) == 6

    # These targets are authored interpretations with visible evidence, not
    # historical utterances, measured model outputs or independently reviewed gold.
    lookup = {r['id']: r for r in policies + actions}
    examples = []
    for example in seeds['examples']:
        evidence, groups = [], set()
        for ref in example['record_ids']:
            record = lookup[ref]
            groups.add(record['group_id'])
            spans = record.get('evidence', [])
            if record.get('explanation_evidence'):
                spans = spans + [record['explanation_evidence']]
            evidence.append({'record_id': ref, 'claim': record.get('claim'),
                             'observed_vote': record.get('original_vote'),
                             'source_spans': spans,
                             'source_text': [sources[s['source_id']]['_text'][s['char_start']:s['char_end']]
                                             for s in spans]})
        context = json.dumps(evidence, ensure_ascii=False)
        examples.append({**example, 'record_type': 'evidence_conditioned_example',
                         'derivation': 'assistant_authored_from_cited_evidence_not_authentic_QA',
                         'group_ids': sorted(groups), 'enable_thinking': False,
                         'messages': [
                             {'role': 'system', 'content': 'Answer as a research simulation of the specified government at the stated policy date. Use the supplied evidence. Distinguish stated policy, recorded action and inference; acknowledge unsupported details. Do not invent private motives or fixed national traits.'},
                             {'role': 'user', 'content': f"Country: {example['country_iso3']}\nPolicy date: {example['date']}\nEvidence: {context}\nQuestion: {example['question']}"},
                             {'role': 'assistant', 'content': example['answer']}], **GATE})

    profiles = [{'country_iso3': code, 'country_name': name,
                 'fact_ids': [f['id'] for f in facts if f['country_iso3'] == code],
                 'policy_ids': [p['id'] for p in policies if code in p['country_iso3']],
                 'action_ids': [a['id'] for a in actions if a['country_iso3'] == code],
                 'coverage_status': 'small prototype, not a comprehensive country dossier', **GATE}
                for code, name in COUNTRIES.items()]
    for filename, rows in [('policies', policies), ('facts', facts), ('actions', actions),
                           ('profiles', profiles), ('examples', examples)]:
        write_jsonl(OUT / f'{filename}.jsonl', rows)
    public_sources = [{k: v for k, v in s.items() if k != '_text'} for s in sources.values()]
    write_json(LOCK, {'version': VERSION, 'sources': public_sources,
                     'excluded_downloads': [{'file': str(RAW / 'world_bank_indicators.json'),
                         'reason': 'API returned null; replaced by validated individual indicator metadata queries'}]})
    report = {'version': VERSION, 'counts': {'countries': len(profiles), 'statistics': len(facts),
               'stated_policy_records': len(policies), 'observed_votes': len(actions),
               'public_explanations': len(explanation_seeds), 'authored_examples': len(examples),
               'training_admitted': 0},
              'four_h100_node_hours': 0, 'verification': ['all raw hashes match receipts and frozen manifest',
                  'all policy and explanation anchors resolve to source spans',
                  'all six vote labels match the official UN roll call',
                  'all 18 requested statistic cells present; missing values preserved'],
              'limitations': ['No independent subject-matter review', 'Policy dates differ between sources',
                  '2024 statistics are a 2026 database vintage, not a contemporaneous 2024 snapshot',
                  'Joint India-Brazil statements are shared evidence, not independent observations',
                  'No claim of future vote prediction or private preference recovery'],
              'artifacts': {str(p): sha256(p) for p in sorted(OUT.glob('*.jsonl'))}}
    write_json(Path('reports') / f'{VERSION}.json', report)
    print(json.dumps(report['counts'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Replay the frozen source URLs and hashes first')
    args = parser.parse_args()
    if args.fetch:
        for source in json.loads(LOCK.read_text())['sources']:
            download(source['url'], source['raw_file'], source_id=source['id'],
                     expected_sha256=source['sha256'])
    build()
