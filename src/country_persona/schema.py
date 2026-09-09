"""Canonical records retain source claims, attribution, and availability separately."""
from __future__ import annotations
import re
from datetime import date
from pathlib import Path
from .io import digest, sha256

COUNTRIES = {'CHN': 'China', 'DEU': 'Germany'}
TOPICS = {
    'peace_security': r'\b(?:security council|ceasefire|conflict|peacekeeping|sicherheitsrat|waffenstillstand)\b',
    'human_rights': r'\b(?:human rights|menschenrecht\w*|torture|discrimination)\b',
    'climate_environment': r'\b(?:climate|emissions|biodiversity|klima\w*)\b',
    'development_economy': r'\b(?:development|trade|debt|poverty|entwicklung\w*|handel)\b',
    'international_law': r'\b(?:international law|charter|sovereignty|völkerrecht\w*)\b',
    'nuclear_disarmament': r'\b(?:nuclear|disarmament|non-proliferation|abrüstung)\b',
    'humanitarian': r'\b(?:humanitarian|refugee\w*|humanitär\w*|flüchtling\w*)\b',
    'technology': r'\b(?:artificial intelligence|cyber\w*|digital\w*)\b',
}


def topics(text):
    return [k for k,v in TOPICS.items() if re.search(v,text,re.I)] or ['unclassified']


def record(source, key, path, url, country, when, precision, institution, capacity,
           task, text, title='', *, question='', history=None, group=None, language='en',
           raw_hash=None, available_date=None, represented_entity=None, flags=None):
    if not text.strip():
        raise ValueError(f'Empty target: {source}/{key}')
    return {
        'schema_version': '2.0', 'id': f'{source}:{key}', 'source_id': source,
        'source_record_id': str(key), 'source_url': url,
        'raw_file': str(path), 'raw_sha256': raw_hash or sha256(path),
        'country_iso3': country, 'country_name': COUNTRIES.get(country,country),
        'represented_entity': represented_entity or COUNTRIES.get(country,country),
        'institution': institution, 'speaking_capacity': capacity, 'language': language,
        'event_date': when, 'date_precision': precision, 'available_date': available_date,
        'group_id': group or f'{source}:{key}', 'document_symbols': [],
        'task': task, 'title': title, 'text': text.strip(),
        'question': question, 'history': history or [], 'context': '',
        'topics': topics(title+'\n'+question+'\n'+text),
        'topic_method': 'keyword-v1; weak labels, not adjudicated positions',
        'derivation': 'source_text', 'quality_status': 'parsed',
        'quality_flags': sorted(set(flags or [])), 'rights_status': 'unresolved',
        'review_status': 'pending', 'split': 'unassigned',
    }


def validate(r):
    required = ['id','source_id','raw_sha256','raw_file','source_url','country_iso3',
                'represented_entity','institution','speaking_capacity','language',
                'event_date','date_precision','available_date','group_id','task','text',
                'quality_flags','rights_status','split']
    for k in required:
        if k not in r:
            raise ValueError(f'Missing {k} in {r.get("id")}')
    if not re.fullmatch(r'[0-9a-f]{64}',r['raw_sha256']):
        raise ValueError('Invalid raw SHA256')
    if not r['text'].strip() or not r['group_id']:
        raise ValueError('Empty text or group')
    if r['date_precision']=='day':
        date.fromisoformat(r['event_date'])
    elif r['date_precision']=='year':
        if not re.fullmatch(r'\d{4}',r['event_date']):raise ValueError('Invalid year')
    elif r['date_precision']!='unknown':
        raise ValueError('Invalid date precision')
    if r['available_date']:
        date.fromisoformat(r['available_date'])
    if r['country_iso3'] and not re.fullmatch(r'[A-Z]{3}',r['country_iso3']):
        raise ValueError('Country must be ISO3 or null; preserve unresolved labels separately')
    if r['split'] not in ('unassigned','train','dev','test','quarantine'):
        raise ValueError('Invalid split')
    return r
