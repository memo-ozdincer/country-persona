#!/usr/bin/env python3
"""Conservative local conversion and review gates for country-persona data.

Python 3.10+; standard library only. No web requests and no external corpus bundled.
See README and schemas.md. Raw-source schema inspection date: 2026-09-09.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

VERSION = '1.0'
SPLITS = {'train', 'dev', 'test', 'quarantine'}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def normalize(text: str) -> str:
    return ' '.join(text.split()).casefold()

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open(encoding='utf-8-sig') as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{n}: invalid JSON: {exc}') from exc
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{n}: expected JSON object')
            out.append(row)
    return out

def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def require(obj: dict, keys: Iterable[str], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ValueError(f'{where}: missing fields {missing}')

def nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')
    return value.strip()

def exact_date(value: str) -> str:
    value = nonempty(value, 'date')
    for fmt in ('%Y-%m-%d', '%d %B %Y', '%d %b %Y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f'Unrecognized day-precision date: {value!r}; normalize explicitly')

def base_record(source: str, record_id: str, path: Path, file_hash: str,
                country: str, group: str, when: str, precision: str,
                task: str, context: str, question: str, target: str) -> dict:
    return {
        'schema_version': VERSION,
        'id': f'{source}:{record_id}',
        'source_id': source,
        'source_record_id': record_id,
        'source_url': '',
        'source_version': 'local-file-sha256:' + file_hash,
        'raw_sha256': file_hash,
        'raw_file': str(path),
        'country_name': country,
        'country_iso3': None,
        'represented_entity': country,
        'institution': 'UNKNOWN_REVIEW_REQUIRED',
        'speaking_capacity': 'UNKNOWN_REVIEW_REQUIRED',
        'language': 'en',
        'event_date': when,
        'date_precision': precision,
        'phase': 'unknown',
        'task': task,
        'group_id': group,
        'prompt_inputs': {'context': context, 'question': question},
        'target': {'text': nonempty(target, 'target'), 'kind': 'text'},
        'evidence_ids': [],
        'split': 'quarantine',
        'review_status': 'pending',
        'train_permission': 'pending',
        'approved_by': '',
        'source_verified': False,
        'context_asof_verified': False,
        'notes': [],
    }

def task2(csv_path: Path, drafts: Path) -> list[dict]:
    file_hash = sha256_file(csv_path)
    output = []
    cache: dict[str, tuple[dict, Path]] = {}
    with csv_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        require(dict.fromkeys(reader.fieldnames or []),
                ['Country', 'Original_id', 'Authors', 'Voting', 'Date'], str(csv_path))
        for i, raw in enumerate(reader, 2):
            original_id = nonempty(raw['Original_id'], f'row {i} Original_id')
            # Original_id is a local folder key, not a UN resolution symbol.
            if not re.fullmatch(r'[A-Za-z0-9_-]+', original_id):
                raise ValueError(f'Unsafe/unsupported folder key: {original_id!r}')
            if original_id not in cache:
                files = sorted((drafts / original_id).glob('*.json'))
                if len(files) != 1:
                    raise ValueError(f'{original_id}: expected exactly one draft JSON, found {len(files)}')
                draft = json.loads(files[0].read_text(encoding='utf-8-sig'))
                require(draft, ['Date', 'ID', 'Title', 'Authors', 'Content'], str(files[0]))
                cache[original_id] = draft, files[0]
            draft, draft_path = cache[original_id]
            country = nonempty(raw['Country'], 'Country')
            vote = raw['Voting'].strip()
            mapping = {'Y': 'yes', 'N': 'no', 'A': 'abstain'}
            if vote not in mapping:
                raise ValueError(f'row {i}: unexpected vote {vote!r}; do not remap silently')
            event_date = exact_date(raw['Date'])
            context = f"Draft {draft['ID']}\n{draft['Title']}\n\n{draft['Content']}"
            r = base_record('unbench_task2', f'{original_id}:{country}', csv_path, file_hash,
                            country, f"unsc:{draft['ID']}", event_date, 'day',
                            'vote_prediction', context,
                            'Predict the recorded vote. Reply with exactly yes, no, or abstain.', mapping[vote])
            r.update(institution='UNSC', speaking_capacity='voting_member', phase='pre_vote')
            r['target']['kind'] = 'vote'
            r['source_url'] = 'https://github.com/yueqingliang1/UNBench'
            r['draft_source'] = {'file': str(draft_path), 'sha256': sha256_file(draft_path),
                                 'document_id': draft['ID'], 'document_date': exact_date(draft['Date'])}
            r['notes'].append('Historical label task. Audit availability of the draft at prediction time; exclude outcome-bearing context.')
            output.append(r)
    return output

def task4(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, list):
        raise ValueError('task4 JSON must be an array')
    file_hash = sha256_file(path)
    output = []
    for i, item in enumerate(data):
        require(item, ['Date', 'ID', 'Content', 'Statements'], f'task4[{i}]')
        if not isinstance(item['Statements'], list):
            raise ValueError(f'task4[{i}].Statements must be an array')
        for j, speech in enumerate(item['Statements']):
            require(speech, ['representative', 'country', 'statement'], f'statement {i}/{j}')
            country = nonempty(speech['country'], 'country')
            r = base_record('unbench_task4', f"{item['ID']}:{j}", path, file_hash,
                            country, f"unsc:{item['ID']}", exact_date(item['Date']), 'day',
                            'statement_generation', f"Document {item['ID']}\n\n{item['Content']}",
                            'Give the delegation’s statement for this documented event.', speech['statement'])
            r.update(institution='UNSC', speaking_capacity='UNKNOWN_REVIEW_REQUIRED')
            r['speaker'] = speech['representative']
            r['source_url'] = 'https://github.com/yueqingliang1/UNBench'
            r['notes'].append('Phase and capacity require review: some speeches are post-vote explanations; do not turn these into pre-vote forecasts.')
            output.append(r)
    return output

def qa_csv(args: argparse.Namespace) -> list[dict]:
    file_hash = sha256_file(args.input)
    columns = [args.id_col, args.group_col, args.date_col, args.question_col, args.answer_col]
    if args.country_col:
        columns.append(args.country_col)
    output = []
    with args.input.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=args.delimiter)
        require(dict.fromkeys(reader.fieldnames or []), columns, 'QA CSV header')
        for raw in reader:
            country = args.country or raw[args.country_col]
            r = base_record(args.source_id, nonempty(raw[args.id_col], 'id'), args.input, file_hash,
                            nonempty(country, 'country'), f'{args.source_id}:{raw[args.group_col]}',
                            exact_date(raw[args.date_col]), 'day', 'question_answering', '',
                            nonempty(raw[args.question_col], 'question'), raw[args.answer_col])
            r.update(institution=args.institution, speaking_capacity=args.capacity,
                     language=args.language, phase='public_qa', source_url=args.source_url)
            r['notes'].append('Explicit column mapping; this adapter does not assume unpublished source headers. Restore follow-up context before approval.')
            output.append(r)
    return output

def ungdc(folder: Path) -> list[dict]:
    output = []
    pattern = re.compile(r'(?P<country>[A-Z]{3})_(?P<session>\d+)_(?P<year>\d{4})\.txt$')
    for path in sorted(folder.rglob('*.txt')):
        m = pattern.fullmatch(path.name)
        if not m:
            continue  # unrelated archive documentation, not a speech
        text = path.read_text(encoding='utf-8-sig')
        r = base_record('ungdc', path.stem, path, sha256_file(path), m['country'],
                        f"unga-general-debate:{m['session']}:{m['year']}", m['year'], 'year',
                        'domain_text', '', '', text)
        r.update(country_iso3=m['country'], institution='UNGA_General_Debate',
                 speaking_capacity='national_address', phase='annual_address',
                 source_url='https://doi.org/10.7910/DVN/0TJX8Y')
        r['notes'].append('Year only; exact date and speaking entity need metadata join. Conservative split groups entire annual session.')
        output.append(r)
    if not output:
        raise ValueError('No ISO3_session_year.txt speech files found')
    return output

REVIEW_FIELDS = ['id', 'split', 'review_status', 'train_permission', 'approved_by',
                 'source_verified', 'context_asof_verified', 'country_iso3',
                 'institution', 'speaking_capacity', 'phase', 'group_id', 'source_url']

def review_template(records: list[dict], path: Path) -> None:
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows({k: r.get(k, '') for k in REVIEW_FIELDS} for r in records)

def apply_review(records: list[dict], path: Path) -> None:
    ids = {r['id'] for r in records}
    seen = set()
    reviews = {}
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        require(dict.fromkeys(reader.fieldnames or []), REVIEW_FIELDS, 'review header')
        for row in reader:
            if row['id'] in seen or row['id'] not in ids:
                raise ValueError(f"Duplicate or unknown review id {row['id']!r}")
            seen.add(row['id'])
            reviews[row['id']] = row
    for record in records:
        if record['id'] not in reviews:
            continue
        for key, value in reviews[record['id']].items():
            if key not in REVIEW_FIELDS or key == 'id' or value == '':
                continue
            if key in {'source_verified', 'context_asof_verified'}:
                if value.lower() not in {'true', 'false'}:
                    raise ValueError(f'{key} must be true or false')
                value = value.lower() == 'true'
            record[key] = value

def audit(records: list[dict], reserved: set[str] | None = None) -> dict:
    reserved = reserved or set()
    ids, group_splits, duplicates = set(), defaultdict(set), defaultdict(set)
    errors = []
    for r in records:
        require(r, ['id', 'group_id', 'split', 'target', 'task', 'event_date', 'date_precision'], 'record')
        if r['id'] in ids:
            errors.append(f"Duplicate record id: {r['id']}")
        ids.add(r['id'])
        if r['split'] not in SPLITS:
            errors.append(f"Invalid split: {r['id']}")
        if r['date_precision'] == 'day':
            exact_date(r['event_date'])
        elif r['date_precision'] == 'year':
            if not re.fullmatch(r'\d{4}', r['event_date']):
                errors.append(f"Invalid year: {r['id']}")
        else:
            errors.append(f"Unsupported date precision: {r['id']}")
        if r['split'] != 'quarantine':
            group_splits[r['group_id']].add(r['split'])
            # Do not flag repeated short vote labels as duplicated speeches.
            if len(r['target']['text']) >= 200:
                duplicates[digest(normalize(r['target']['text']))].add(r['split'])
        if r['split'] == 'train' and r['group_id'] in reserved:
            errors.append(f"Reserved group assigned to train: {r['group_id']}")
    for group, splits in group_splits.items():
        if len(splits) > 1:
            errors.append(f'Group leaks across splits: {group}: {sorted(splits)}')
    for h, splits in duplicates.items():
        if len(splits) > 1:
            errors.append(f'Exact normalized long-text overlap across splits: {h[:12]}')
    return {'records': len(records), 'split_counts': dict(Counter(r['split'] for r in records)),
            'task_counts': dict(Counter(r['task'] for r in records)), 'errors': errors,
            'limitations': ['Exact-text and assigned-group checks only; semantic duplicates, unresolved source joins, pretraining contamination and paraphrase leakage need separate review.']}

def training_example(r: dict) -> dict:
    if r['task'] == 'domain_text':
        raise ValueError('domain_text is a mid-training record, not instruction SFT')
    if r['date_precision'] != 'day':
        raise ValueError(f"Exact date required for SFT export: {r['id']}")
    if r['phase'] == 'unknown' or 'UNKNOWN' in r['speaking_capacity'] or 'UNKNOWN' in r['institution']:
        raise ValueError(f"Unreviewed institutional role/phase: {r['id']}")
    if not re.fullmatch(r'[A-Z]{3}', r.get('country_iso3') or ''):
        raise ValueError(f"Reviewed country ISO3 required: {r['id']}")
    system = (f"You are a research simulation of the {r['represented_entity']} delegation, not an official representative. "
              f"Institution: {r['institution']}. Capacity: {r['speaking_capacity']}. "
              f"As-of date: {r['event_date']}. Phase: {r['phase']}. "
              'Represent documented positions rather than national stereotypes. '
              'Distinguish supplied evidence from inference; do not invent commitments.')
    inputs = r['prompt_inputs']
    user = '\n\n'.join(x for x in [inputs.get('context', ''), inputs.get('question', '')] if x)
    if not user:
        raise ValueError(f"Empty SFT input: {r['id']}")
    return {'prompt': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
            'completion': [{'role': 'assistant', 'content': r['target']['text']}]}

def build(records: list[dict], output: Path, reserved: set[str]) -> dict:
    report = audit(records, reserved)
    if report['errors']:
        raise ValueError('Audit failed:\n' + '\n'.join(report['errors']))
    examples, manifest = [], []
    skipped = Counter()
    for r in records:
        if r['split'] != 'train':
            skipped['not_train'] += 1
            continue
        if r['task'] == 'domain_text':
            skipped['midtraining_not_sft'] += 1
            continue
        if (r['review_status'] != 'approved' or r['train_permission'] != 'approved'
            or not r['approved_by'] or r['source_verified'] is not True
            or r['context_asof_verified'] is not True or not r['source_url']):
            skipped['review_or_permission_pending'] += 1
            continue
        ex = training_example(r)
        examples.append(ex)
        manifest.append({'row_index': len(examples)-1, 'id': r['id'], 'group_id': r['group_id'],
                         'source_id': r['source_id'], 'source_url': r['source_url'],
                         'source_version': r['source_version'], 'raw_sha256': r['raw_sha256'],
                         'event_date': r['event_date'], 'country_iso3': r['country_iso3'],
                         'approved_by': r['approved_by'], 'example_sha256': digest(json.dumps(ex, sort_keys=True))})
    if not examples:
        raise ValueError(f'No approved training examples. Skipped: {dict(skipped)}. Complete review; do not bypass the gate.')
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output/'train.sft.jsonl', examples)
    write_jsonl(output/'train.manifest.jsonl', manifest)
    write_jsonl(output/'reviewed.canonical.jsonl', records)
    report.update(exported_sft=len(examples), skipped=dict(skipped))
    (output/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    return report

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('unbench-task2', 'unbench-task4', 'qa-csv', 'ungdc'):
        q = sub.add_parser(name)
        q.add_argument('--input', type=Path, required=True)
        q.add_argument('--output', type=Path, required=True)
        if name == 'unbench-task2':
            q.add_argument('--drafts-dir', type=Path, required=True)
        if name == 'qa-csv':
            for col in ('id', 'group', 'date', 'question', 'answer'):
                q.add_argument(f'--{col}-col', required=True)
            group = q.add_mutually_exclusive_group(required=True)
            group.add_argument('--country'); group.add_argument('--country-col')
            q.add_argument('--source-id', required=True)
            q.add_argument('--source-url', required=True)
            q.add_argument('--institution', required=True)
            q.add_argument('--capacity', required=True)
            q.add_argument('--language', default='en')
            q.add_argument('--delimiter', default=',')
    q = sub.add_parser('review-template')
    q.add_argument('--input', type=Path, required=True)
    q.add_argument('--output', type=Path, required=True)
    q = sub.add_parser('build-sft')
    q.add_argument('--input', type=Path, required=True)
    q.add_argument('--review', type=Path, required=True)
    q.add_argument('--reserved-groups', type=Path, required=True)
    q.add_argument('--output-dir', type=Path, required=True)
    q = sub.add_parser('inspect')
    q.add_argument('--input', type=Path, required=True)
    args = p.parse_args()
    if args.cmd == 'unbench-task2':
        records = task2(args.input, args.drafts_dir)
    elif args.cmd == 'unbench-task4':
        records = task4(args.input)
    elif args.cmd == 'qa-csv':
        records = qa_csv(args)
    elif args.cmd == 'ungdc':
        records = ungdc(args.input)
    elif args.cmd == 'review-template':
        review_template(read_jsonl(args.input), args.output)
        print(f'Review template: {args.output}'); return
    elif args.cmd == 'build-sft':
        records = read_jsonl(args.input)
        apply_review(records, args.review)
        reserved = {s.strip() for s in args.reserved_groups.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')}
        print(json.dumps(build(records, args.output_dir, reserved), indent=2)); return
    else:
        if args.input.suffix.lower() in {'.csv', '.tsv'}:
            with args.input.open(encoding='utf-8-sig', newline='') as f:
                rows = csv.DictReader(f, delimiter='\t' if args.input.suffix == '.tsv' else ',')
                print(json.dumps({'fields': rows.fieldnames, 'first_record_keys': list(next(rows, {}).keys())}, indent=2))
        else:
            print(json.dumps(audit(read_jsonl(args.input)), indent=2))
        return
    result = audit(records)
    if result['errors']:
        raise ValueError('\n'.join(result['errors']))
    write_jsonl(args.output, records)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(2)
