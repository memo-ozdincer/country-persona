"""CPU guards for the frozen raw-source / checked-plan paired comparison."""
from country_persona.io import digest


def validate_cases(cases, design='raw_vs_plan'):
    count = 4 if design == 'raw_vs_plan' else 2 if design == 'checked_plan_repair_only' else 0
    if not count or len(cases) != count or len({c['id'] for c in cases}) != count:
        raise ValueError('Unexpected comparison design/case count')
    for country in ('BRA', 'IND'):
        pair = [c for c in cases if c['country_iso3'] == country]
        if design == 'checked_plan_repair_only':
            if len(pair) != 1 or pair[0]['condition'] != 'checked_plan_repair':
                raise ValueError('Require one repair prompt per national role')
            continue
        if {c['condition'] for c in pair} != {'raw', 'checked_plan'} or len(pair) != 2:
            raise ValueError('Require raw and plan for each role')
        raw = next(c for c in pair if c['condition'] == 'raw')
        plan = next(c for c in pair if c['condition'] == 'checked_plan')
        if raw['prompt'][:-1] != plan['prompt'][:-1]:
            raise ValueError('System instructions differ across conditions')
        if plan['prompt'][-1]['content'] != raw['prompt'][-1]['content'] + plan['plan_appendix']:
            raise ValueError('Plan condition must only append checked plan')
    for c in cases:
        if c['case_sha256'] != digest({k:v for k,v in c.items() if k != 'case_sha256'}):
            raise ValueError('Frozen case changed')


def verify_matched_inputs(transcript, expected_calls=8):
    if len(transcript) != expected_calls:
        raise ValueError('Incomplete comparison')
    by_case = {}
    for row in transcript:
        by_case.setdefault(row['id'], []).append(row)
    if len(by_case) != expected_calls // 2:
        raise ValueError('Case count differs')
    for rows in by_case.values():
        if len(rows) != 2 or {r['arm'] for r in rows} != {'base', 'saved_adapter'}:
            raise ValueError('Duplicate or absent matched arm')
        if rows[0]['input_ids_digest'] != rows[1]['input_ids_digest']:
            raise ValueError('Matched weights must receive identical tokens')
    return True
