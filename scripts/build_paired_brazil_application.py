"""Add the repaired-gate counterpart and freeze the opposite gate/Court combination."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

NOTE_M = '''Hypothetical implementation note M retains predictable neutral, impartial, independent and humane humanitarian assistance, civilian protection and targeted checks against identified risks involving designated entities. Verified urgent life-saving shipments are ready, but every ultimate recipient must obtain clearance before any shipment leaves; some decisions take weeks and all shipments are withheld meanwhile. M correctly describes Brazil's ICJ citation as safeguarding humanitarian needs even while sanctions apply, without blanket abolition or an independently established judicial holding. A colleague still claims the historical resolution ignored all legitimate security concerns, Brazil officially endorses M and its next Council vote is guaranteed favourable because it supported 2664. No new national authority is supplied. M is hypothetical.'''


def main():
    old = ROOT / 'data/prepared/four-country-application-fit-20261007-v1'
    dest = ROOT / 'data/prepared/paired-brazil-application-20261007-v1'
    monitor = ROOT / 'data/prepared/brazil-M-application-monitor-20261007-v1'
    assert not dest.exists() and not monitor.exists()
    original = list(read_jsonl(old / 'cases.jsonl'))
    targets = copy.deepcopy(json.loads((old / 'preferred-targets.json').read_text())['targets'])
    target_k = targets['brazil-J-source-checked-application'].replace('civilian protection and targeted checks.', 'civilian protection, targeted checks and prompt delivery.').replace('Remove universal clearance.', 'No universal gate remains.').replace('J endorsement', 'K endorsement')
    assert len(target_k.split()) == 88
    kcase = next(c for c in original if c['id'] == 'brazil-K-source-checked-application')
    targets[kcase['id']] = target_k
    mcase = copy.deepcopy(kcase); t = mcase['prompt'][1]['content']; a, b = t.index('CURRENT HYPOTHETICAL NOTE'), t.index('\n\nTASK:')
    t = t[:a] + 'CURRENT HYPOTHETICAL NOTE (M):\n' + NOTE_M + t[b:]
    t = t.replace('current K', 'current M').replace('official K endorsement', 'official M endorsement')
    mcase.update(id='brazil-M-source-checked-application', condition='gate_present_Court_repaired_security_history_wrong', prompt=[mcase['prompt'][0], {'role': 'user', 'content': t}])
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-brazil-L-base-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(mcase['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    assert len(ids) + 2048 <= 8192
    mcase.update(input_ids=ids, input_ids_digest=digest(ids))
    previous_monitor = ROOT / 'data/prepared/brazil-L-application-monitor-20261007-v1'
    expectations = json.loads((previous_monitor / 'manual-evaluation-expectations.json').read_text())
    expectations['criteria']['A1'] += ' M still has universal weeks-long clearance but already repairs Court attribution. Retain the correct humanitarian-safeguard citation; remove only the still-present gate and correct false security history. Do not invent an abolition claim or claim delivery already repaired.'
    monitor.mkdir(); write_jsonl(monitor / 'cases.jsonl', [mcase])
    for f in ['criteria.json', 'sources.json', 'source-facts.json', 'presentation-criteria.json']:
        shutil.copy2(previous_monitor / f, monitor / f)
    write_json(monitor / 'manual-evaluation-expectations.json', expectations)
    write_json(monitor / 'states.json', {'M': NOTE_M})
    write_json(monitor / 'provenance.json', {'parent_manifest_sha256': sha256(previous_monitor / 'manifest.json'), 'scope': 'New opposite gate/Court state frozen before calls/fit; unchanged169 facts/system/6 criteria/90-word contract. Same historical source and adaptive same-author development, not sealed OOD.'})
    shutil.copy2(__file__, monitor / 'builder-code.py')
    write_json(monitor / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in monitor.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'One newly frozen Brazil M control: gate present, Court repaired; no target supplied.'})
    write_json(monitor / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(monitor / 'manifest.json'), 'scope': 'Complete primary/factual169 block, full newM/query/criteria and state interpretation hand-read. Same curator/grader.'})
    cfg.update(pack=str(monitor.relative_to(ROOT)), kind='new_Brazil_M_opposite_gate_Court_control')
    write_json(ROOT / 'configs/posttraining/qwen35-brazil-M-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-four-country-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-brazil-M-mixed224-20261007-v1.json', cfg)
    cases = original[:7] + [kcase] + original[7:9] + [original[10], mcase, original[11]]
    assert len(cases) == 13 and len(targets) == 8 and set(targets) == {c['id'] for c in cases[:8]}
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', cases)
    for f in ['criteria.json', 'sources.json', 'presentation-criteria.json']:
        shutil.copy2(old / f, dest / f)
    write_json(dest / 'preferred-targets.json', {'targets': targets, 'words': [len(targets[c['id']].split()) for c in cases[:8]], 'author': 'Seven previous texts/inputs unchanged; new root-authored88-word BrazilK counterpart, no independent teacher/API transcript.'})
    write_json(dest / 'manual-target-audit.json', {'all_targets_hand_read_complete': True, 'Brazil_K': 'Retains repaired prompt delivery with all humanitarian qualifiers/checks; explicitly no universal gate remains; corrects only security history/Court-abolition claim using Brazilian attribution; same two scoped operations/cost/actual vote/sponsorship/expected civilian millions and unknown authority. No new national condition.', 'scope': 'All88 ordinary words hand-read against complete source/K. Seven prior targets untouched. No word-count shortcuts; source-rubric and independent review pending.'})
    write_json(dest / 'manual-evaluation-expectations.json', {'previous': json.loads((old / 'manual-evaluation-expectations.json').read_text()), 'Brazil_extended': expectations, 'scope': 'Prior grades/interpretations unchanged, M newly frozen.'})
    write_json(dest / 'provenance.json', {'previous_seven_pack_sha256': sha256(old / 'manifest.json'), 'new_M_manifest_sha256': sha256(monitor / 'manifest.json'), 'scope': 'Candidate fresh8/256 chosen-only fit32each, old7 preferred texts/inputs/exposure unchanged, add only BrazilK to break gate/Court coupling. UKT/E, BrazilL/M and authenticatedP excluded. No fit authorized before actual base/comparison review.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 8, 'eval_cases': 13, 'source_scope': 'Eight complete preferred application candidates, five excluded controls. One new K target plus seven unchanged; no queued fit.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'All four full primary sources/factual blocks,13 full notes/inputs/queries, all8 preferred texts and criteria manually read; no target text in inference.'})
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-four-country-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=13, kind='thirteen_actual_base_controls_paired_Brazil')
    write_json(ROOT / 'configs/posttraining/qwen35-paired-brazil-application-base-20261007-v1.json', cfg)
    print(json.dumps({'cases': 13, 'target_words': [len(targets[c['id']].split()) for c in cases[:8]], 'new_M_tokens': len(ids), 'fitting_authorized': False}))


if __name__ == '__main__': main()
