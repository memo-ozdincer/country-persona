"""Freeze one exposed Brazil ICC case, changing only the plan's shorthand representation."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

NORMAL_PLAN = '''Documented source points:
- National representative França Danese at the ICC briefing on 13 July 2023, not the chair or Prosecutor. UK representative Kariuki chairs; no meeting vote. Thanks the UK presidency, Japan and Switzerland for the briefing and Khan's 37th report under resolution 1593; first Council referral to the ICC despite criticism of discriminatory jurisdiction.
- Grimmer, stalled road map: war impairs the Office of the Prosecutor's investigations and outreach, and Sudan's assistance capacity. Necessary security and immediate cessation of hostilities; steps when the situation allows, not unlimited unsafe deployment.
- Improve cooperation between the Prosecutor and national authorities despite the crisis. States have primary responsibility for justice; complementarity means the ICC acts when they are unable or unwilling. International support strengthens Sudanese justice institutions.
- Calls for Council referral expenses to be borne by the UN as well as Rome Statute parties; no Brazilian appropriation or pledge. The prosecution presented its case against Abd-Al-Rahman in the first trial following resolution 1593; families' suffering, not a conviction.
- Welcomes engagement with third States and regional organizations, and dialogue with civil society and affected communities despite outreach obstacles.
- Severe economic hardship worsened by the April war; half the population needs urgent aid, and there are refugees. All stakeholders have civilian and aid obligations under IHL and IHRL; mediation, and the 2020 Juba Agreement binding all signatories.
- Founding ICC member with deep commitment to international law and justice. A permanent treaty-based Court for accountability; all investigations deserve equal zeal and international support.
Analytical decisions:
- Z confuses enabling security with a universal military-victory gate, erases cooperation and complementarity, and fabricates convictions. Parties-only referral costs and abandoning other cases contradict the source. The public-witness assistance gate is an analytical protection problem; Brazil's source does not contain France's explicit witness clause.
- Coordinate safe evidence and cooperation where conditions allow, with remote, refugee and community channels; build national justice capacity alongside complementary ICC work. Seek appropriate UN referral-funding consideration and equal case support, without an actual new appropriation.
- Safety, verification and coordination cost time and resources versus speed; avoid unsafe on-site work or waiting for total victory everywhere.
Authority: no official Z endorsement or guaranteed future vote. Retain the real founding commitment, cooperation and hopes; recommendations are analytical.'''


def main():
    old = ROOT / 'data/prepared/plan-input-fit-20261006-v1'
    manifest = json.loads((old / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        assert sha256(old / name) == expected
    original = next(c for c in read_jsonl(old / 'cases.jsonl') if c['id'] == 'icc-bra-plan')
    shorthand = json.loads((old / 'teacher-plans.json').read_text())['icc_plans']['BRA']
    assert original['prompt'][1]['content'].count(shorthand) == 1
    case = copy.deepcopy(original)
    case.update(id='icc-bra-ordinary-points', condition='same_semantic_plan_ordinary_spaced_english')
    case['prompt'][1]['content'] = original['prompt'][1]['content'].replace(shorthand, NORMAL_PLAN)
    assert case['prompt'][0] == original['prompt'][0]
    assert case['prompt'][1]['content'].replace(NORMAL_PLAN, shorthand) == original['prompt'][1]['content']
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-plan-input-base-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
    case.update(input_ids=ids, input_ids_digest=digest(ids))
    assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
    dest = ROOT / 'data/prepared/ordinary-points-20261006-v2'
    assert not dest.exists()
    dest.mkdir(parents=True)
    write_jsonl(dest / 'cases.jsonl', [case])
    shutil.copy2(old / 'criteria.json', dest / 'criteria.json')
    source = json.loads((old / 'sources.json').read_text())['icc']['BRA']
    write_json(dest / 'source.json', source)
    write_json(dest / 'plans.json', {'original_shorthand': shorthand, 'ordinary_english': NORMAL_PLAN,
        'author': 'Same assistant hand-expanded the existing synthetic plan; no new teacher model call.'})
    scope = 'Exposed Brazil ICC development; only plan representation/length change, no new facts or decisions intended. Same source/scenario/rubric/contract/model/runtime for base/raw8/plan8. Three calls, zero optimization; independent review pending.'
    write_json(dest / 'provenance.json', {'scope': scope, 'old_pack': str(old.relative_to(ROOT)),
        'old_manifest_sha256': sha256(old / 'manifest.json'), 'old_case_id': original['id'],
        'old_case_digest': digest(original), 'old_input_ids_digest': original['input_ids_digest'],
        'criteria_sha256': sha256(old / 'criteria.json'), 'shorthand_digest': digest(shorthand),
        'ordinary_plan_digest': digest(NORMAL_PLAN), 'replacement_count': 1,
        'changes': ['Spelling, spaces, punctuation and abbreviation expansion in plan only.', 'Plan token/word length changes.'],
        'source_scenario_system_contract_unchanged': True, 'same_meanings_intended': True,
        'old_point_case_reviews': {arm: {'run': 'runs/' + name, 'inspection_sha256': sha256(ROOT / 'runs' / name / 'inspection.json')}
            for arm, name in [('base', 'aurora-plan-input-base-20261006-v1'), ('raw8', 'aurora-plan-input-raw8-20261006-v1'), ('plan8', 'aurora-plan-input-fit-20261006-v1')]}})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': scope})
    # Inspection is written separately after the serialized plan is read in full.
    cfg = {k: cfg[k] for k in ['model', 'revision', 'model_path', 'runtime_path', 'runtime_pins', 'seed',
        'max_length', 'chat_template_kwargs', 'generation_max_new_tokens', 'authorization']}
    cfg.update(pack=str(dest.relative_to(ROOT)), phase='writer', eval_cases=1, training_examples=0,
        max_steps=0, kind='ordinary_spaced_points_no_optimization')
    write_json(ROOT / 'configs/posttraining/qwen35-ordinary-points-base-20261006-v2.json', cfg)
    for arm, path in [('raw8', 'runs/aurora-diverse-country-fit-20261006-v2/adapter'),
                      ('plan8', 'runs/aurora-plan-input-fit-20261006-v1/adapter')]:
        adapter = ROOT / path
        trained = {**cfg, 'adapter': path, 'adapter_sha256': sha256(adapter / 'adapter_model.safetensors'),
            'adapter_config_sha256': sha256(adapter / 'adapter_config.json')}
        write_json(ROOT / f'configs/posttraining/qwen35-ordinary-points-{arm}-20261006-v2.json', trained)
    print(json.dumps({'input_tokens': len(ids), 'normal_plan_words': len(NORMAL_PLAN.split()),
        'old_shorthand_words': len(shorthand.split()), 'new_calls_prepared': 3, 'new_optimizer_steps': 0}))


if __name__ == '__main__':
    main()
