"""Add one complete Brazil target; retain six texts and freeze a new repaired-Court state."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

TARGET = '''Analytical decisions:
- Keep predictable, neutral, impartial, independent, humane aid, civilian protection and targeted checks. Remove universal clearance. Legitimate security concerns were considered; Brazil cites ICJ safeguarding humanitarian needs while sanctions remain, not blanket abolition.
- Agencies release verified urgent aid; authorities review identified risks alongside delivery. Review costs staff time versus speed.
- Brazil sponsored the initiative and voted for 2664; expects predictable humanitarian work benefiting millions of civilians.
Authority:
- J endorsement and future vote unknown; recommendations are analytical, not official Brazilian positions.'''

NOTE_L = '''Hypothetical implementation note L retains predictable neutral, impartial, independent and humane humanitarian assistance, civilian protection and targeted checks against identified risks involving designated entities. Verified urgent life-saving shipments leave promptly alongside targeted checks, without a universal pre-delivery clearance gate. L correctly describes Brazil's ICJ citation as safeguarding humanitarian needs even while sanctions apply; it does not claim blanket abolition or an independently established judicial holding. A colleague still claims the historical resolution ignored all legitimate security concerns, Brazil officially endorses L and its next Council vote is guaranteed favourable because it supported 2664. No new national authority is supplied. L is hypothetical.'''


def main():
    dest = ROOT / 'data/prepared/four-country-application-20261007-v1'
    monitor = ROOT / 'data/prepared/brazil-L-application-monitor-20261007-v1'
    assert not dest.exists() and not monitor.exists()
    old = ROOT / 'data/prepared/three-country-application-fit-20261007-v1'
    brazil = ROOT / 'data/prepared/brazil-application-monitor-20261007-v1'
    auth = ROOT / 'data/prepared/authenticated-india-application-20261007-v1'
    original = list(read_jsonl(old / 'cases.jsonl'))
    bcases = list(read_jsonl(brazil / 'cases.jsonl'))
    lcase = copy.deepcopy(bcases[1]); text = lcase['prompt'][1]['content']
    a, b = text.index('CURRENT HYPOTHETICAL NOTE'), text.index('\n\nTASK:')
    text = text[:a] + 'CURRENT HYPOTHETICAL NOTE (L):\n' + NOTE_L + text[b:]
    text = text.replace('current K', 'current L').replace('official K endorsement', 'official L endorsement')
    lcase.update(id='brazil-L-source-checked-application', condition='delivery_and_Court_claim_repaired_security_history_wrong', prompt=[lcase['prompt'][0], {'role': 'user', 'content': text}])
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-brazil-application-base-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(lcase['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    assert len(ids) + 2048 <= 8192
    lcase.update(input_ids=ids, input_ids_digest=digest(ids))
    expectations = json.loads((brazil / 'manual-evaluation-expectations.json').read_text())
    expectations['criteria']['A1'] += ' L already repairs both delivery and Court attribution; retain them, do not recreate clearance or criticize an absent abolition claim. Only the false security-history claim remains operationally relevant, with unauthenticated endorsement/future-vote claims still unsupported.'
    monitor.mkdir()
    write_jsonl(monitor / 'cases.jsonl', [lcase])
    for f in ['criteria.json', 'sources.json', 'source-facts.json', 'presentation-criteria.json']:
        shutil.copy2(brazil / f, monitor / f)
    write_json(monitor / 'manual-evaluation-expectations.json', expectations)
    write_json(monitor / 'states.json', {'L': NOTE_L})
    write_json(monitor / 'provenance.json', {'parent_manifest_sha256': sha256(brazil / 'manifest.json'), 'scope': 'New L state frozen before calls/next fit; same169 facts/system/generic6 criteria/90-word task. Source historical/shared sanctions exposure, no sealed OOD claim.'})
    shutil.copy2(__file__, monitor / 'builder-code.py')
    write_json(monitor / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in monitor.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'One newly frozen Brazil L application control; delivery/Court already repaired, no targets supplied.'})
    write_json(monitor / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(monitor / 'manifest.json'), 'scope': 'Complete prior primary/facts plus full newL/query/prospective interpretation hand-read. Same curator/grader.'})
    cfg.update(pack=str(monitor.relative_to(ROOT)), eval_cases=1, kind='new_Brazil_L_application_control')
    write_json(ROOT / 'configs/posttraining/qwen35-brazil-L-base-20261007-v1.json', cfg)
    previous = ROOT / 'runs/aurora-three-country-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(previous.relative_to(ROOT)), adapter_sha256=sha256(previous / 'adapter_model.safetensors'), adapter_config_sha256=sha256(previous / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-brazil-L-mixed192-20261007-v1.json', cfg)
    cases = original[:6] + [bcases[0]] + original[6:8] + [bcases[1], lcase] + list(read_jsonl(auth / 'cases.jsonl'))
    targets = json.loads((old / 'preferred-targets.json').read_text())['targets']
    targets[bcases[0]['id']] = TARGET
    assert len(cases) == 12 and len(targets) == 7 and len(TARGET.split()) == 85
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', cases)
    for f in ['criteria.json', 'sources.json', 'presentation-criteria.json']:
        shutil.copy2(old / f, dest / f)
    write_json(dest / 'preferred-targets.json', {'targets': targets, 'words': [len(targets[c['id']].split()) for c in cases[:7]], 'author': 'Six prior texts/inputs unchanged; one new root-authored source-audited85-word Brazil target, no independent teacher/API transcript.'})
    write_json(dest / 'manual-target-audit.json', {'all_targets_hand_read_complete': True, 'Brazil_J': 'Retained humanitarian principles/protection/targeted checks; universal gate removed; legitimate security consideration and attributed Court safeguard/counter-abolition corrected; two scoped agencies/authorities operations; staff-time/speed cost; actual vote/sponsorship and anticipated millions of civilians, not designated entities; unknown endorsement/future vote and analytical authority.', 'scope': 'All85 ordinary words manually reviewed against complete primary/169 facts/currentJ. No shortcut word fusion/slash counting. Existing French closed-source absence qualification retained.'})
    write_json(dest / 'manual-evaluation-expectations.json', {'previous': json.loads((old / 'manual-evaluation-expectations.json').read_text()), 'Brazil_extended': expectations, 'authenticated_India': json.loads((auth / 'manual-evaluation-expectations.json').read_text()), 'scope': 'All old interpretations unchanged; new L frozen prospectively before calls.'})
    write_json(dest / 'provenance.json', {'previous_six_pack_sha256': sha256(old / 'manifest.json'), 'new_L_manifest_sha256': sha256(monitor / 'manifest.json'), 'scope': 'Candidate fresh7/224 chosen-only fit32each after baseline inspection; retains exact old6 inputs/targets/exposure, adds only BrazilJ. K exposed, L newly frozen, UKT/E and authenticatedP excluded. No fitting authorization before complete actual controls/binding.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 7, 'eval_cases': 12, 'source_scope': 'Seven complete application target candidates across four countries; five nonfitting controls, old6 unchanged. No fit/queue authorized yet.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'All four primary national sources/factual blocks,12 full notes/inputs/queries, all7 targets/criteria and hypothetical authority update manually read. No targets in inference prompts.'})
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-three-country-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=12, kind='twelve_actual_base_controls_four_countries')
    write_json(ROOT / 'configs/posttraining/qwen35-four-country-application-base-20261007-v1.json', cfg)
    print(json.dumps({'cases': 12, 'target_words': [len(targets[c['id']].split()) for c in cases[:7]], 'new_L_tokens': len(ids), 'training_authorized': False}))


if __name__ == '__main__': main()
