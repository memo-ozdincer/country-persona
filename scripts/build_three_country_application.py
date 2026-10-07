"""Combine six unchanged targets and freeze four nonfitting application cases."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl


def main():
    dest = ROOT / 'data/prepared/three-country-application-20261007-v1'
    assert not dest.exists()
    old = ROOT / 'data/prepared/two-country-application-fit-20261007-v1'
    uk = ROOT / 'data/prepared/uk-paired-application-fit-20261007-v1'
    brazil = ROOT / 'data/prepared/brazil-application-monitor-20261007-v1'
    original_cases = list(read_jsonl(old / 'cases.jsonl'))[:4]
    uk_cases = list(read_jsonl(uk / 'cases.jsonl'))
    brazil_cases = list(read_jsonl(brazil / 'cases.jsonl'))
    cases = original_cases + uk_cases[:2] + uk_cases[2:] + brazil_cases
    targets = {**json.loads((old / 'preferred-targets.json').read_text())['targets'], **json.loads((uk / 'preferred-targets.json').read_text())['targets']}
    assert len(cases) == 10 and len(targets) == 6 and set(targets) == {c['id'] for c in cases[:6]}
    crit = copy.deepcopy(json.loads((old / 'criteria.json').read_text()))
    for p in [uk, brazil]:
        other = json.loads((p / 'criteria.json').read_text())
        assert crit['common_units'] == other['common_units'] and crit['universal_checks'] == other['universal_checks']
        for family, countries in other['source_units'].items():
            crit['source_units'].setdefault(family, {}).update(countries)
    crit['policy'] = 'Same six application compounds/four guards/90-word task. Six byte-identical France/India/UK fitting candidates, excluded UK T/E and new Brazil J/K. Historical sources/UK states development-exposed; Brazil outside current application fitting countries, shared sanctions family, no sealed OOD claim.'
    sources = copy.deepcopy(json.loads((old / 'sources.json').read_text()))
    for p in [uk, brazil]:
        for family, countries in json.loads((p / 'sources.json').read_text()).items():
            sources.setdefault(family, {}).update(countries)
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', cases)
    write_json(dest / 'criteria.json', crit)
    write_json(dest / 'sources.json', sources)
    write_json(dest / 'preferred-targets.json', {'targets': targets, 'words': [len(targets[c['id']].split()) for c in cases[:6]], 'author': 'All six prior hand-audited preferred texts unchanged. No new teacher outputs or target edits.'})
    write_json(dest / 'manual-target-audit.json', {'all_targets_hand_read_complete': True, 'targets_and_inputs_unchanged': True, 'scope': 'Two France, two India and two UK full targets/inputs/primaries manually reviewed. French no package adopted phrase interpreted under bounded source, not independently proved global absence; retained text unchanged, independent adjudication desirable. All country/source authority boundaries remain.'})
    write_json(dest / 'manual-evaluation-expectations.json', {'France_India': json.loads((old / 'manual-evaluation-expectations.json').read_text()), 'UK': json.loads((uk / 'manual-evaluation-expectations.json').read_text()), 'Brazil': json.loads((brazil / 'manual-evaluation-expectations.json').read_text()), 'scope': 'All prior state-specific interpretations retained; Brazil frozen prospectively. No prior grade revised.'})
    shutil.copy2(old / 'presentation-criteria.json', dest / 'presentation-criteria.json')
    write_json(dest / 'provenance.json', {'parent_pack_manifest_sha256': {str(p.relative_to(ROOT)): sha256(p / 'manifest.json') for p in [old, uk, brazil]}, 'scope': 'Candidate fresh mixed6/192 chosen-only fit,32 presentations each, same six texts/inputs/exposure as sequential fresh4/128 then warm2/64. Joint order/single optimizer differ from sequential reset; not isolated replay-effect or objective change. UK T/E excluded, Brazil J/K newly frozen outside fitting country. No fit authorized before inspected controls.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 6, 'eval_cases': 10, 'source_scope': 'Six unchanged three-country preferred application texts and four nonfitting monitors. Targets not supplied to inference; no speculative queue.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Complete four national sources, all10 factual/input/note/query texts, all6 preferred texts, generic criteria/guards and all state-specific interpretations fully read by root. Fitting decision requires complete inspected baseline/provenance.'})
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-two-country-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=10, training_examples=0, max_steps=0, kind='combined_actual_base_controls_three_countries_and_Brazil')
    write_json(ROOT / 'configs/posttraining/qwen35-three-country-application-base-20261007-v1.json', cfg)
    print(json.dumps({'cases': 10, 'targets': 6, 'target_words': [len(targets[c['id']].split()) for c in cases[:6]], 'fitting_authorized': False}))


if __name__ == '__main__':
    main()
