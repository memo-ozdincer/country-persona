from copy import deepcopy
import json
from pathlib import Path
import pytest
from country_persona.application_fit_checks import validate_design, match_references
from country_persona.io import read_jsonl, digest

ROOT = Path(__file__).resolve().parents[1]


def frozen():
    p = ROOT / 'data/prepared/source-application-sft-20261003-v2'
    e = ROOT / 'data/prepared/source-application-eval-20261003-v2'
    if not p.exists() or not e.exists():
        pytest.skip('Bounded frozen artifacts available in private handoff')
    return [list(read_jsonl(p / name)) for name in ('train.jsonl', 'train.manifest.jsonl', 'teacher-records.jsonl')] + [list(read_jsonl(e / 'cases.jsonl'))]


def test_frozen_design_and_family_leak_rejection():
    args = frozen()
    validate_design(*args, 'wps-8514-20190423')
    args[1][0]['split_group'] = 'wps-8514-20190423'
    with pytest.raises(ValueError, match='leakage'):
        validate_design(*args, 'wps-8514-20190423')


def test_private_plan_rejected_in_student_input():
    args = frozen()
    args[0][0]['prompt'].append(deepcopy(args[2][0]['teacher_authoring_context_specification'][-1]))
    with pytest.raises(ValueError, match='private plan'):
        validate_design(*args, 'wps-8514-20190423')


def test_changed_plan_instructions_rejected():
    args = frozen()
    c = next(c for c in args[3] if c['condition'] == 'checked_plan')
    c['prompt'][0]['content'] = 'Simplified task'
    c['case_sha256'] = digest({k:v for k,v in c.items() if k != 'case_sha256'})
    with pytest.raises(ValueError, match='append assistance'):
        validate_design(*args, 'wps-8514-20190423')


def test_matching_requires_every_case_and_unique_output():
    rows = [{'id': str(i), 'input_ids_digest': str(i)} for i in range(6)]
    refs = {r['id']: deepcopy(r) for r in rows}
    assert match_references(rows, refs)
    rows[4]['input_ids_digest'] = 'different'
    with pytest.raises(ValueError, match='per case'):
        match_references(rows, refs)
    rows[4] = deepcopy(rows[3])
    with pytest.raises(ValueError, match='distinct'):
        match_references(rows, refs)
