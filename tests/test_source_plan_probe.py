import json
from copy import deepcopy
from pathlib import Path
import pytest
from country_persona.io import digest
from country_persona.probe_checks import validate_cases, verify_matched_inputs


def fixture_cases():
    result = []
    for country in ('BRA', 'IND'):
        for condition in ('raw', 'checked_plan'):
            c = {'id': country+condition, 'country_iso3': country, 'condition': condition,
                 'prompt': [{'role': 'system', 'content': 'same'}, {'role': 'user', 'content': 'sources'+('plan' if condition=='checked_plan' else '')}],
                 'plan_appendix': 'plan' if condition=='checked_plan' else ''}
            c['case_sha256'] = digest(c)
            result.append(c)
    return result


def test_plan_may_only_append_assistance():
    cases = fixture_cases()
    validate_cases(cases)
    cases[1]['prompt'][0]['content'] = 'easier instructions'
    cases[1]['case_sha256'] = digest({k:v for k,v in cases[1].items() if k!='case_sha256'})
    with pytest.raises(ValueError, match='System instructions'):
        validate_cases(cases)


def test_matching_is_per_case_not_first_transcript_row():
    rows = [{'id': c['id'], 'arm': arm, 'input_ids_digest': digest(c['prompt'])}
            for arm in ('base','saved_adapter') for c in fixture_cases()]
    assert verify_matched_inputs(rows)
    rows[5]['input_ids_digest'] = 'changed'
    with pytest.raises(ValueError, match='identical tokens'):
        verify_matched_inputs(rows)


def test_duplicate_arm_is_not_a_pair():
    rows = [{'id': c['id'], 'arm': arm, 'input_ids_digest': digest(c['prompt'])}
            for arm in ('base','saved_adapter') for c in fixture_cases()]
    rows[4]['arm'] = 'base'
    with pytest.raises(ValueError, match='matched arm'):
        verify_matched_inputs(rows)


def test_repair_requires_both_national_roles():
    cases = [c for c in fixture_cases() if c['condition']=='checked_plan']
    for c in cases:
        c['condition'] = 'checked_plan_repair'
        c['case_sha256'] = digest({k:v for k,v in c.items() if k!='case_sha256'})
    validate_cases(cases, 'checked_plan_repair_only')
    cases[1]['country_iso3'] = 'BRA'
    with pytest.raises(ValueError, match='national role'):
        validate_cases(cases, 'checked_plan_repair_only')
