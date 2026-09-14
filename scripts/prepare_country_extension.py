"""Build attributed evidence and observed actions for the four-country extension.

No generic whole-document SFT export: text passages are retrieval/review material.
All new records remain quarantined while proposed family splits protect holdouts.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

from country_persona.bulk import parse_unga_dm, parse_uhri, parse_unga_rdata, unga_meeting_dates
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.prepare import UnionFind, normalized
from country_persona.schema import record, validate

VERSION = 'country-extension-20260914'
RAW = Path('data/raw') / VERSION
OUT = Path('data/prepared') / VERSION
NAMES = {'France': 'FRA', 'United Kingdom': 'GBR',
         'United Kingdom of Great Britain and Northern Ireland': 'GBR', 'India': 'IND', 'Brazil': 'BRA'}
CODES = set(NAMES.values())
RANK = {'train': 0, 'dev': 1, 'test': 2, 'quarantine': 3}
UPR_DATES = {'FRA': '2023-03-07', 'GBR': '2022-08-17', 'IND': '2022-08-17', 'BRA': '2022-09-01'}


def parse_document(item):
    path = Path(item['raw_file'])
    if sha256(path) != item['raw_sha256']:
        raise ValueError('Raw document hash mismatch')
    if item['format'] == 'pdf':
        # Validate with the parser, not only the MIME header or filename.
        text = subprocess.check_output(['pdftotext', str(path), '-'], text=True)
    elif item['format'] == 'json':
        obj = json.loads(path.read_text())
        text = BeautifulSoup(obj['details']['body'], 'html.parser').get_text('\n', strip=True)
        if obj.get('document_type') != 'speech':
            raise ValueError('GOV.UK object is not a speech')
    else:
        soup = BeautifulSoup(path.read_bytes(), 'html.parser')
        selectors = {'india_pib': '#condiv', 'india_un_mission': '#innerContent .mcontent',
                     'brazil_mre': '#parent-fieldname-text', 'brazil_planalto': '#parent-fieldname-text',
                     'france_elysee': '.card__body.ck-styled'}
        blocks = soup.select(selectors[item['source_id']])
        if not blocks:
            raise ValueError('Expected article body missing')
        texts = list(dict.fromkeys(b.get_text('\n', strip=True) for b in blocks))
        text = '\n\n'.join(texts)
    text = text.strip()
    if len(normalized(text)) < 400:
        raise ValueError('Document body too short')
    source_date = item.get('date')
    country = item['countries'][0] if len(item['countries']) == 1 else None
    when = UPR_DATES[country] if item.get('upr_cycle') == 4 else source_date
    precision = 'day' if when and len(when) == 10 else 'year' if when and len(when) in (4, 7) else 'unknown'
    if precision == 'year':
        when = when[:4]
    flags = ['evidence_document_not_response_target', 'individual_claims_require_review',
             'historical_version_availability_unverified']
    if len(item['countries']) > 1:
        flags.append('shared_institutional_scope_not_independent_national_statements')
    if item['kind'] == 'foreign_policy_compendium':
        flags += ['compendium_extract_each_speaker_and_date_before_supervision', 'reporting_period_not_event_date']
        # Do not assign all 2023–2024 quotations to the opening year.
        when, precision = None, 'unknown'
    if item['source_id'] == 'france_elysee':
        flags.append('publisher_transcript_body_selected_editorial_overview_excluded')
    r = record(item['source_id'], item['id'], path, item['url'], country,
               when, precision, item['source_id'], item['attribution'], 'policy_evidence_document',
               text, item['title'], group=item['group_id'], language=item['language'],
               raw_hash=item['raw_sha256'], represented_entity=item['represented_entity'], flags=flags)
    r.update(document_type=item['kind'], related_countries=item['countries'],
             document_symbols=[item['document_symbol']] if item.get('document_symbol') else [],
             date_basis=item['date_basis'], publisher_date_label=source_date,
             retrieved_at=item['retrieved_at'], translation_family=item['group_id'],
             translation_status='publisher_language_version; sentence_alignment_not_reviewed',
             upr_cycle='Cycle 4' if item.get('upr_cycle') == 4 else None,
             original_language=('fr' if country == 'FRA' else 'en') if item.get('upr_cycle') == 4 else None)
    if item['format'] == 'pdf':
        r['pdf_pages'] = len(text.rstrip('\f\n').split('\f'))
    if item['source_id'] == 'wto_government_reports':
        match = re.search(r'\b(\d{1,2} [A-Z][a-z]+ 20\d\d)\b', text.split('\f')[0])
        r['pdf_issue_date_label'] = match.group(1) if match else None
        r['quality_flags'].append('government_submission_not_independent_WTO_assessment')
    text_path = OUT / 'source-text' / (item['id'] + '.txt')
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text)
    r.update(extracted_text_file=str(text_path), extracted_text_sha256=sha256(text_path))
    return r


def propose(row):
    if 'Cycle 4' in str(row.get('upr_cycle')):
        return 'test'
    if 'Cycle 3' in str(row.get('upr_cycle')):
        return 'dev'
    date = row['event_date']
    if not date:
        return 'quarantine'
    if len(date) == 4:
        date += '-12-31'
    if date > '2026-09-14':
        return 'quarantine'
    return 'test' if date > '2026-06-30' else 'dev' if date > '2025-12-31' else 'train'


def protect_families(rows):
    """Share a split across documents, translations, votes and old exposed events."""
    uf, owners = UnionFind(), {}
    previous = []
    for path in ['data/prepared/pilot/pilot.canonical.jsonl',
                 'data/prepared/expansion-20260913/documents.jsonl']:
        if not Path(path).exists():
            raise ValueError('Previous split ledger missing: ' + path)
        for r in read_jsonl(path):
            previous.append({k: r.get(k) for k in ['id', 'parent_id', 'group_id', 'document_symbols', 'text']} |
                            {'existing_split': r.get('proposed_split', r['split'])})
    for r in previous + rows:
        group = r['group_id']; uf.find(group)
        keys = ['id:' + r['id']]
        if r.get('parent_id'):
            keys.append('id:' + r['parent_id'])
        keys += ['symbol:' + s for s in r.get('document_symbols', [])]
        if len(r.get('text', '')) >= 200:
            keys.append('text:' + digest(normalized(r['text'])))
        for key in keys:
            if key in owners:
                uf.union(group, owners[key])
            else:
                owners[key] = group
    rank, seen_splits = defaultdict(int), defaultdict(set)
    for r in previous:
        split = r['existing_split']
        if split in RANK:
            gid = uf.find(r['group_id'])
            rank[gid] = max(rank[gid], RANK[split]); seen_splits[gid].add(split)
    for r in rows:
        gid = uf.find(r['group_id'])
        rank[gid] = max(rank[gid], RANK[propose(r)])
    inverse = {v: k for k, v in RANK.items()}
    for r in rows:
        gid = uf.find(r['group_id'])
        r.update(split_group=gid, proposed_split=inverse[rank[gid]], split='quarantine',
                 training_admitted=False, review_status='pending',
                 existing_event_splits=sorted(seen_splits[gid]),
                 fresh_evaluation_eligible=False,
                 fresh_evaluation_note='requires cross-language/semantic and base-model contamination review')
        validate(r)


def passages(doc, cap=2800):
    """Exact spans within PDF pages; page boundaries are never crossed."""
    offset = 0
    for number, page in enumerate(doc['text'].split('\f'), 1):
        pos = 0
        while pos < len(page):
            end = min(pos + cap, len(page))
            if end < len(page):
                boundary = page.rfind('\n\n', pos + cap // 2, end)
                if boundary > pos:
                    end = boundary
            a, b = pos, end
            while a < b and page[a].isspace(): a += 1
            while b > a and page[b - 1].isspace(): b -= 1
            t = page[a:b]
            if len(normalized(t)) >= 180:
                yield {'id': doc['id'] + f':span:{offset+a}:{offset+b}', 'parent_id': doc['id'],
                       'source_id': doc['source_id'], 'source_url': doc['source_url'],
                       'raw_sha256': doc['raw_sha256'], 'country_iso3': doc['country_iso3'],
                       'related_countries': doc['related_countries'], 'represented_entity': doc['represented_entity'],
                       'language': doc['language'], 'event_date': doc['event_date'],
                       'available_date': doc['available_date'], 'document_type': doc['document_type'],
                       'group_id': doc['group_id'], 'split_group': doc['split_group'],
                       'proposed_split': doc['proposed_split'], 'split': 'quarantine',
                       'text': t, 'start_char': offset + a, 'end_char': offset + b,
                       'pdf_page': number if 'pdf_pages' in doc else None,
                       'use': 'retrieval_and_claim_review_not_automatic_supervision',
                       'training_admitted': False, 'review_status': 'pending'}
            pos = end
        offset += len(page) + 1


def context_facts():
    collection = json.loads((RAW / 'context/collection.json').read_text())
    obs = collection['observations']
    if sha256(obs['raw_file']) != obs['sha256']:
        raise ValueError('World Bank observations hash mismatch')
    metadata = {}
    for item in collection['metadata']:
        if sha256(item['raw_file']) != item['sha256']:
            raise ValueError('World Bank metadata hash mismatch')
        metadata[item['indicator']] = {**json.loads(Path(item['raw_file']).read_text())[1][0], 'explicit_unit': item['unit']}
    head, values = json.loads(Path(obs['raw_file']).read_text())
    rows = []
    for n, r in enumerate(values):
        meta = metadata[r['indicator']['id']]
        rows.append({'id': f"WDI:{r['countryiso3code']}:{r['indicator']['id']}:{r['date']}",
            'country_iso3': r['countryiso3code'], 'indicator': r['indicator']['id'],
            'label': r['indicator']['value'], 'reference_year': r['date'], 'value': r['value'],
            'missing': r['value'] is None, 'unit': meta['explicit_unit'],
            'definition': meta['sourceNote'], 'upstream_organization': meta['sourceOrganization'],
            'database_last_updated': head['lastupdated'], 'retrieved_at': obs['retrieved_at'],
            'source_url': obs['url'], 'raw_file': obs['raw_file'], 'raw_sha256': obs['sha256'],
            'json_pointer': f'/1/{n}', 'available_at_reference_year': None,
            'use': 'dated_material_context_not_political_preferences', 'split': 'quarantine', 'training_admitted': False})
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    collection = json.loads((RAW / 'collection.json').read_text())
    docs, errors, manifest = [], [], []
    for item in collection['documents']:
        if item['status'] != 'acquired':
            manifest.append(item); continue
        try:
            r = parse_document(item); docs.append(r)
            manifest.append({**item, 'canonical_id': r['id'], 'parse_status': 'parsed'})
        except Exception as exc:
            manifest.append({**item, 'parse_status': 'excluded', 'parse_error': str(exc)})
            errors.append({'id': item['id'], 'error': str(exc)})
    votes_path = Path('data/raw/unga_dm/votes.csv')
    for path in [votes_path, Path('data/raw/uhri/export-full-en.json'),
                 Path('data/raw/unga_speech_corpus/corpus.zip')]:
        receipt = json.loads(path.with_name(path.name + '.receipt.json').read_text())
        if sha256(path) != receipt['sha256']:
            raise ValueError('Bulk source receipt mismatch: ' + str(path))
    with zipfile.ZipFile('data/raw/unga_speech_corpus/corpus.zip') as archive:
        names = [n for n in archive.namelist() if n.rsplit('/', 1)[-1] == 'unga_speech_corpus.RData']
        if len(names) != 1:
            raise ValueError('Ambiguous speech-corpus archive entry')
        h = hashlib.sha256()
        with archive.open(names[0]) as member:
            while block := member.read(1024 * 1024): h.update(block)
        if h.hexdigest() != sha256('data/raw/unga_speech_corpus/unga_speech_corpus.RData'):
            raise ValueError('Extracted speech table differs from verified source archive')
    votes = list(parse_unga_dm(votes_path, country_map=NAMES))
    uhri = list(parse_uhri('data/raw/uhri/export-full-en.json', countries_only=True, country_map=NAMES))
    dates = unga_meeting_dates(votes_path)
    speeches = [r for r in parse_unga_rdata('data/raw/unga_speech_corpus/unga_speech_corpus.RData',
               'https://www.linneaturco.com/research', dates, votes_path, country_map=NAMES)
                if r['country_iso3'] in CODES]
    all_rows = docs + votes + uhri + speeches
    assert len({r['id'] for r in all_rows}) == len(all_rows)
    protect_families(all_rows)
    evidence = [p for d in docs for p in passages(d)]
    parents = {r['id']: r for r in docs}
    for p in evidence:
        assert p['text'] == parents[p['parent_id']]['text'][p['start_char']:p['end_char']]
    facts = context_facts()
    for name, rows in [('documents', docs), ('evidence-passages', evidence), ('unga-votes', votes),
                       ('uhri-records', uhri), ('unga-speech-segments', speeches), ('country-context', facts)]:
        write_jsonl(OUT / f'{name}.jsonl', rows)
    source_paths = sorted({r['raw_file'] for r in all_rows} | {r['raw_file'] for r in facts})
    source_hashes = [{'raw_file': p, 'sha256': sha256(p)} for p in source_paths]
    write_json('data/manifests/' + VERSION + '.json', {'version': VERSION, 'documents': manifest,
        'bulk_and_context_sources': source_hashes, 'exhaustive': False,
        'context_collection': json.loads((RAW / 'context/collection.json').read_text()),
        'previous_split_ledgers': [{'path': p, 'sha256': sha256(p)} for p in
                                  ['data/prepared/pilot/pilot.canonical.jsonl', 'data/prepared/expansion-20260913/documents.jsonl']]})
    stats = {'version': VERSION, 'countries': sorted(CODES), 'documents': len(docs),
        'document_groups': len({d['group_id'] for d in docs}),
        'pdf_pages_including_language_versions': sum(d.get('pdf_pages', 0) for d in docs),
        'languages': dict(Counter(d['language'] for d in docs)),
        'documents_by_entity': dict(Counter(d['represented_entity'] for d in docs)),
        'document_types': dict(Counter(d['document_type'] for d in docs)),
        'evidence_passages': len(evidence), 'unga_votes': len(votes),
        'unga_decisions': len({r['group_id'] for r in votes}),
        'votes_by_country': dict(Counter(r['country_iso3'] for r in votes)),
        'uhri_by_task': dict(Counter(r['task'] for r in uhri)),
        'speech_segments_by_task': dict(Counter(r['task'] for r in speeches)),
        'country_context_cells': len(facts), 'country_context_nonmissing': sum(not r['missing'] for r in facts),
        'proposed_splits_all_canonical_rows': dict(Counter(r['proposed_split'] for r in all_rows)),
        'rows_overlapping_previous_train_events': sum('train' in r['existing_event_splits'] for r in all_rows),
        'download_exclusions': sum(r['status'] == 'excluded' for r in manifest),
        'parse_errors': errors, 'training_admitted': 0, 'four_h100_node_hours': 0,
        'quality_limits': ['All new rows quarantined; no independent subject-matter review',
            'Passages are evidence, not automatically extracted or adjudicated policy claims',
            'Most vote labels still lack joined proposal text',
            'Speech-boundary heuristics and cross-language equivalence require review',
            'Historical knowledge may exist in base-model pretraining',
            'Public source-use terms retained; not a blanket redistribution/training license'],
        'artifacts': {str(p): {'sha256': sha256(p), 'bytes': p.stat().st_size} for p in
                      [OUT / f'{name}.jsonl' for name in ['documents', 'evidence-passages', 'unga-votes',
                                                         'uhri-records', 'unga-speech-segments', 'country-context']]}}
    write_json('reports/' + VERSION + '.json', stats)
    print(json.dumps({k: v for k, v in stats.items() if k != 'artifacts'}, indent=2))


if __name__ == '__main__':
    main()
