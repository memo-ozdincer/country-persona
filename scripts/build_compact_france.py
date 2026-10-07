"""One source-audited compact France plan, matched base/point8 controls; no fitting."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

COMPACT = '''Documented source points:
- France thanks Khan's twenty-sixth Libya report and welcomes Libya's representative; defends victim justice, the rules-based order and Rome Statute integrity; condemns the cyberattack; supports Court and staff.
- Continues political, operational, human and financial support; notes requested budget increase addressing April 2022 strategy risks, twenty-third report, without approving an amount.
- Four inquiries progress; 2014–2020 operations inquiry nears completion; Office expects a potential next-report roadmap under 1970, not completed activities or judgments.
- Active national–Court cooperation; September floods impair missions, condolences and support. Detention and migrant-crime progress includes national arrests and prosecutions assisted by Office information, evidence and guidelines, not ICC verdicts.
- Document access, technical authorities, visas, assistance requests, stronger joint-team missions; progress towards Tripoli office in 2024. Ambassador posted in Netherlands, nationality unstated.
- Victim, witness, community engagement; regional civil-society seminar on guidelines documenting international crimes and human-rights violations; intensify exchanges.
- All serious crimes since 2011, including Daesh, migrants and refugees, investigated and prosecuted; international, regional and civil-society assistance, coordinated investigations with third States and agencies, UNSMIL and Independent Fact-Finding Mission on Libya support.
- Sovereign, united, stable, democratic Libya and regional stability; actual ongoing support remains.

Analytical decisions:
- Keep Q's national justice, documentation, visas, technical cooperation and protected channels. Correct completed judgments and activities, already-open office, excluded crimes and cooperation exception; restore equal coverage, no new budget condition.
- Brazil's detailed non-party legal explanation is absent from France's speech.
- Coordinate document, visa and technical requests; maintain protected victim and community evidence channels.
- Inclusive verification and protection cost staff time versus quickly closing fewer files.

Authority:
- No official Q endorsement or future-vote guarantee; recommendations analytical, real support retained.'''


def main():
    parent = ROOT / 'data/prepared/compression-points-only-20261007-v1'
    dest = ROOT / 'data/prepared/compact-france-20261007-v1'
    assert not dest.exists() and len(COMPACT.split()) <= 300
    case = copy.deepcopy(next(c for c in read_jsonl(parent / 'cases.jsonl') if c['country_iso3'] == 'FRA'))
    original = json.loads((parent / 'held-plans.json').read_text())['plans']['FRA']
    assert case['prompt'][1]['content'].count(original) == 1
    case['prompt'][1]['content'] = case['prompt'][1]['content'].replace(original, COMPACT)
    case.update(id='libya-fra-compact-points', condition='readable_compact_checked_points')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compact-points-base-20261007-v2.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    case.update(input_ids=ids, input_ids_digest=digest(ids))
    assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
    dest.mkdir()
    for name in ['sources.json', 'criteria.json', 'presentation-criteria.json']:
        shutil.copy2(parent / name, dest / name)
    write_jsonl(dest / 'cases.jsonl', [case])
    write_json(dest / 'checked-plan.json', {'plan': COMPACT, 'words': len(COMPACT.split()),
        'author': 'same root assistant; all new compact text hand-read against complete France source and14 frozen meanings',
        'all_source_application_authority_meanings_audited': True, 'ordinary_readable_word_boundaries': True})
    write_json(dest / 'provenance.json', {'scope': 'One exposed France/Libya compact-point realization check; source/Q/metadata/request/contract/criteria identical, only complete-meaning plan representation changes. No optimization or new source family.',
        'parent_manifest_sha256': sha256(parent / 'manifest.json'), 'original_plan_sha256': digest(original)})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {p.name: sha256(p) for p in dest.iterdir() if p.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1,
        'source_scope': 'Frozen exposed compact-France check; two calls, zero updates.'})
    write_json(dest / 'manual-inspection.json', {'manifest_sha256': sha256(dest / 'manifest.json'),
        'all_selected_texts_read_complete': True,
        'read_scope': 'Full France speech and all14 criteria reread; all compact bullets checked for actor, time, cooperation scope, requested-versus-actual funding, possible-versus-completed inquiries, national-versus-ICC verdicts, French-original ambassador posting, known repairs, source absence, operations/cost and authority. Standard acronyms and hyphenation, ordinary word separation; all slash lists expanded before freezing.'})
    cfg.update(pack=str(dest.relative_to(ROOT)))
    write_json(ROOT / 'configs/posttraining/qwen35-compact-france-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-plan-input-fit-20261006-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
               adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-compact-france-point8-20261007-v1.json', cfg)
    print(json.dumps({'plan_words': len(COMPACT.split()), 'input_tokens': len(ids), 'calls': 2, 'optimizer_steps': 0}))


if __name__ == '__main__':
    main()
