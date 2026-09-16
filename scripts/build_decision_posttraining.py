"""Project reviewed decision cases into quarantined TRL rows and a public showcase.

The showcase contains only project-authored summaries, never publisher document bodies.
Rows are demonstrations: review and event-level split assignment precede training.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/prepared/decision-cases-20260914/cases.jsonl'
OUT = ROOT / 'data/prepared/decision-posttraining-20260916'
SHOWCASE = ROOT / 'explorer/decision-showcase.json'
DOSSIERS = ROOT / 'data/curation/decision_dossiers_v2.json'
COUNTRIES = {'CHN', 'DEU'}
VOTES = {'in favor', 'against', 'abstaining'}


def row(prompt, answer):
    return {
        'prompt': [
            {'role': 'system', 'content': 'Report only what the supplied historical evidence establishes. Do not infer private motives or bargaining conditions.'},
            {'role': 'user', 'content': prompt},
        ],
        'completion': [{'role': 'assistant', 'content': answer}],
        'chat_template_kwargs': {'enable_thinking': False},
    }


def report_answer(case, dossier):
    return (f"Observed action: {case['country_name']} voted {case['observed_action']} on {case['proposal_symbol']}. "
            f"The Assembly {dossier['event']['assembly_result'].lower()}\n"
            f"Public position and proposal relationship: {dossier['country']['synthesis']}\n"
            f"Evidence limit: {dossier['country']['evidence_limit']}")


def project(cases, dossiers=None):
    dossiers = dossiers or json.loads(DOSSIERS.read_text())
    rows, metadata, cards = [], [], []
    for case in sorted(cases, key=lambda c: (c['event_date'], c['country_iso3'])):
        if case['country_iso3'] not in COUNTRIES:
            continue
        assert case['observed_action'] in VOTES
        assert case['split'] == 'quarantine' and case['training_admitted'] is False
        assert case['fresh_evaluation_eligible'] is False
        assert case['vote_evidence']['primary_roll_call_verified'] is True
        assert case['proposal_evidence']['source_url'] and case['vote_evidence']['source_url']
        assert case['conditions_for_agreement'] is None and case['private_motive'] is None
        for evidence in (case['proposal_evidence'], case['explanation_evidence']):
            if evidence is None:
                continue
            source = ROOT / evidence['text_file']
            assert source.is_file(), source
            assert hashlib.sha256(source.read_bytes()).hexdigest() == evidence['text_sha256'], source
            assert 0 <= evidence['char_start'] < evidence['char_end'] <= len(source.read_text()), source
        kind = case['explanation_kind']
        assert kind in {'explanation_of_vote', 'pre_vote_statement', 'not_acquired'}
        assert bool(case['public_explanation']) == (kind != 'not_acquired')
        if kind != 'not_acquired':
            assert case['explanation_evidence']['source_url']
        event = dossiers['events'][case['proposal_symbol']]
        national = dossiers['countries'][case['country_iso3'] + '|' + case['proposal_symbol']]
        assert event['source_url'] == case['proposal_evidence']['source_url']
        if case['country_iso3'] == 'CHN':
            assert national['source_url'] == case['explanation_evidence']['source_url']
            assert national['statement_time'] == ('after_vote' if kind == 'explanation_of_vote' else 'before_vote')
        else:
            assert kind == 'not_acquired' and national['statement_time'] == 'before_vote'
        clauses = '\n'.join(f"{p['id']}: {p['text']}" for p in event['clauses'])
        positions = '\n'.join(f"- {s}" for s in national['positions'])

        common = (f"Country: {case['country_name']}\nDecision date: {case['event_date']}\n"
                  f"Draft: {case['proposal_symbol']}\nMeeting setting: {event['setting']}\n"
                  f"Proposal provisions (project paraphrases):\n{clauses}")
        action = row(common + '\nUsing this draft-only context, which recorded final vote matches the country? Answer with only: in favor, against, or abstaining.', case['observed_action'])
        statement = (f"\nRecorded final vote: {case['observed_action']}\nAssembly result: {event['assembly_result']}\n"
                     f"Attributed public position by {national['speaker']} ({national['statement_time'].replace('_', ' ')}):\n{positions}\n"
                     f"Source-status note: {national['evidence_limit']}")
        report = row(common + statement + '\nWrite an evidence-grounded decision report connecting specific proposal provisions to the attributed public position. State the observed outcome and the limits of inference.', report_answer(case, {'event': event, 'country': national}))
        tasks = [
            ('vote_reconstruction', action, 'Exact roll-call label. Draft-only baseline; no claimed causal or predictive validity.'),
            ('grounded_decision_report', report, 'Check clause references, vote, speaker, temporal status, source support and uncertainty.'),
        ]
        for task, training_row, scoring in tasks:
            row_index = len(rows)
            rows.append(training_row)
            metadata.append({
                'id': case['id'] + ':' + task, 'case_id': case['id'], 'task': task,
                'row_index': row_index, 'example_sha256': hashlib.sha256(json.dumps(training_row, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                'country_iso3': case['country_iso3'], 'event_date': case['event_date'],
                'proposal_symbol': case['proposal_symbol'], 'group_id': case['group_id'], 'split_group': case['group_id'],
                'split': 'quarantine', 'training_admitted': False,
                'status': 'candidate_not_training_approved',
                'fresh_evaluation_eligible': False, 'review_status': case['review_status'],
                'source_urls': {'draft': case['proposal_evidence']['source_url'],
                                'vote': case['vote_evidence']['source_url'],
                                'statement': national['source_url']},
            })
        cards.append({
            'case_id': case['id'], 'country': case['country_name'], 'country_iso3': case['country_iso3'],
            'event_date': case['event_date'], 'title': case['title'],
            'proposal_symbol': case['proposal_symbol'], 'resolution_symbol': case['resolution_symbol'],
            'proposal_summary': case['proposal_summary'], 'observed_action': case['observed_action'],
            'statement_kind': kind, 'statement_summary': case['public_explanation'],
            'setting': event['setting'], 'decision_rule': event['decision_rule'],
            'assembly_result': event['assembly_result'], 'clauses': event['clauses'],
            'national_position': national,
            'group_id': case['group_id'], 'tasks': [
                {'id': task, 'format': training_row, 'inspection': scoring}
                for task, training_row, scoring in tasks
            ],
            'sources': metadata[-1]['source_urls'],
            'status': 'Source checked; independent review pending. Quarantined; not admitted to training or fresh evaluation.',
        })
    assert len(cards) == 4 and len(rows) == 8
    assert len({c['group_id'] for c in cards}) == 2
    return rows, metadata, {'version': 'decision-posttraining-candidates-v2',
                            'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                            'dossier_sha256': hashlib.sha256(DOSSIERS.read_bytes()).hexdigest(),
                            'case_count': len(cards), 'task_count': len(rows), 'event_count': 2,
                            'training_admitted': 0, 'cases': cards}


def write_jsonl(path, records):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))


def main():
    cases = [json.loads(s) for s in SOURCE.read_text().splitlines() if s.strip()]
    rows, metadata, showcase = project(cases)
    OUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT / 'candidates.jsonl', rows)
    write_jsonl(OUT / 'candidates.manifest.jsonl', metadata)
    SHOWCASE.write_text(json.dumps(showcase, ensure_ascii=False, indent=2) + '\n')
    print(f"{len(showcase['cases'])} case views, {len(rows)} quarantined task rows, {showcase['event_count']} events")


if __name__ == '__main__':
    main()
