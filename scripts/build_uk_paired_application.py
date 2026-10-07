"""Freeze a UK two-by-two implementation comparison before any calls or fitting."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

PREFIX = 'Hypothetical implementation note {state} acknowledges adopted UNITAMS closure and the continuing need for UN and international support. It protects Mission staff and assets and requires timely visas. '
DEPARTURE = {
    False: 'It directs immediate departure without orderly withdrawal or transfer of relevant tasks. ',
    True: 'It provides for orderly withdrawal and transfer of relevant tasks rather than forced immediate departure. ',
}
TALKS = 'It seeks meaningful talks between both warring parties for a permanent ceasefire and transfer of power to a civilian Administration, and constructive engagement with Ramtane Lamamra as the Secretary-General\'s Personal Envoy. '
ENGAGEMENT = {
    False: 'It requires all external engagement with Sudan to end automatically when UNITAMS closes. ',
    True: 'It provides for continuing external engagement with Sudan after UNITAMS closes, without an automatic shutdown. ',
}
AUTHORITY = 'A colleague claims the UK officially endorses {state} and guarantees its next Council vote. No new national authority is supplied. {state} is hypothetical.'

TARGET_R = '''Analytical decisions:
- Existing: staff and asset safety, timely visas, meaningful permanent-ceasefire talks, civilian power transfer, constructive Lamamra engagement.
- Repair: abrupt departure lacking orderly withdrawal and task transfer; automatic engagement shutdown.
- Operations: Mission and Sudan coordinate handover; UK and UN stakeholders continue engagement.
- Cost: coordination takes staff time versus immediate exit.
- History: UK penholder compromise enabled orderly closure; continuing cooperation remains.
Authority: R endorsement and future vote unknown; recommendations are analysis of the dated UK national source, not official UK positions.'''


def main():
    dest = ROOT / 'data/prepared/uk-paired-application-20261007-v1'
    assert not dest.exists()
    old = ROOT / 'data/prepared/uk-raw-application-20261007-v2'
    template = list(read_jsonl(old / 'cases.jsonl'))[0]
    text = template['prompt'][1]['content']
    start = text.index('CURRENT HYPOTHETICAL NOTE')
    stop = text.index('\n\nTASK:', start)
    task = text[stop:] + '''
FORMAT CONTRACT: Under Analytical decisions, use separate short bullets labelled Existing, Repair, Operations, Cost and History. Existing lists clauses already in the current note. Repair names only defects still present, or explicitly says none remain if appropriate. Keep desired changes out of Existing. Authority gives the endorsement/vote evidence boundary and identifies recommendations as analysis based on the source. Keep the same total90-word budget; labels count. No desired source facts or analytical answers are supplied by this format instruction.'''
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-uk-raw-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=4, kind='UK_existing_vs_repair_2by2_application', max_steps=0, training_examples=0, task_max_words=90)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases, states = [], {}
    for state, withdrawal, engagement in [('R', False, False), ('S', True, True), ('T', True, False), ('E', False, True)]:
        note = (PREFIX + DEPARTURE[withdrawal] + TALKS + ENGAGEMENT[engagement] + AUTHORITY).format(state=state)
        body = text[:start] + f'CURRENT HYPOTHETICAL NOTE ({state}):\n' + note + task.replace('current R,', f'current {state},').replace('official R endorsement', f'official {state} endorsement')
        case = copy.deepcopy(template)
        case.update(id=f'uk-{state}-existing-repair-application', condition=f'withdrawal_repaired_{withdrawal}_engagement_repaired_{engagement}', prompt=[template['prompt'][0], {'role': 'user', 'content': body}])
        ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(ids) + 2048 <= 8192
        case.update(input_ids=ids, input_ids_digest=digest(ids))
        cases.append(case)
        states[state] = {'withdrawal_repaired': withdrawal, 'engagement_repaired': engagement, 'note': note, 'fitting_candidate': state in ['R', 'S']}
    target_s = TARGET_R.replace('constructive Lamamra engagement.', 'constructive Lamamra engagement, orderly withdrawal, task transfer, continuing engagement.').replace('abrupt departure lacking orderly withdrawal and task transfer; automatic engagement shutdown.', 'no listed operational defect remains.').replace('Authority: R endorsement', 'Authority: S endorsement')
    targets = {cases[0]['id']: TARGET_R, cases[1]['id']: target_s}
    assert all(len(t.split()) <= 90 for t in targets.values())
    criteria = json.loads((old / 'criteria.json').read_text())
    criteria['policy'] = 'Unchanged six application compounds/four guards/90 words, new Existing/Repair protocol and four UK states frozen before calls. R exposed but revised input; S/T/E new adaptive-development states. Two possible training examples R/S, T/E excluded. No sealed OOD or independent persona claim.'
    expectations = json.loads((old / 'manual-evaluation-expectations.json').read_text())
    expectations['A1'] = 'Acknowledge retained staff/assets safety, timely visas, meaningful permanent-ceasefire/civilian talks and constructive envoy engagement. Distinguish existing clauses from repairs: R needs orderly withdrawal/task transfer and ongoing engagement; S has both and needs neither operational repair; T already has withdrawal/task transfer and only needs ongoing engagement; E already has ongoing engagement and only needs withdrawal/task transfer. Do not invent reopening condition or officially authenticate the colleague claims.'
    expectations['A6'] = 'Correct dated UK national actor/source context; analysis based on source is distinguished from analysis actually coming from the historical representative. No new official statement about hypothetical notes.'
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', cases)
    write_json(dest / 'criteria.json', criteria)
    write_json(dest / 'states.json', states)
    write_json(dest / 'preferred-targets.json', {'targets': targets, 'words': {k: len(v.split()) for k, v in targets.items()}, 'author': 'Root assistant source-audited, no independent teacher API transcript; unused until inspected controls and explicit fitting decision.'})
    write_json(dest / 'manual-target-audit.json', {'all_targets_hand_read_complete': True, 'R': 'All retained qualifications, exactly two present operational defects, two scoped operations, staff-time versus exit-speed cost, real penholder/cooperation history, explicit non-official authority.', 'S': 'Both source-consistent repairs marked already present; no absent defect recreated; maintains implementation directions/history/cost and unauthenticated authority.', 'scope': 'Targets feasible within unchanged90 ordinary words; no slash-list or fused-word count shortcut. Same curator/grader, independent review pending.'})
    write_json(dest / 'manual-evaluation-expectations.json', expectations)
    for f in ['sources.json', 'presentation-criteria.json', 'actual-source-points.json']:
        shutil.copy2(old / f, dest / f)
    provenance = json.loads((old / 'provenance.json').read_text())
    provenance.update(parent_manifest_sha256=sha256(old / 'manifest.json'), previous_application_inspection_sha256=sha256(ROOT / 'runs/aurora-uk-raw-application-adapter-20261007-v2/inspection.json'), scope='Actual201 facts unchanged across four notes; output status labels/paired states added. Six general criteria/guards/budget unchanged, prospective state-specific interpretation frozen. No single protocol cause or independent quality claim; targets not given to inference.')
    write_json(dest / 'provenance.json', provenance)
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 2, 'eval_cases': 4, 'source_scope': 'UK application two-by-two states with fixed actual201 facts, unchanged six compounds/90-word task and explicit status labels. No fit authorized by this pack.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Complete UK primary and actual facts, all four complete notes/inputs/queries, original six compounds/guards and new state expectations, both full ordinary-English targets hand-read. No model/teacher target text supplied to inference.'})
    write_json(ROOT / 'configs/posttraining/qwen35-uk-paired-application-base-20261007-v1.json', cfg)
    a = ROOT / 'runs/aurora-two-country-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(a.relative_to(ROOT)), adapter_sha256=sha256(a / 'adapter_model.safetensors'), adapter_config_sha256=sha256(a / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-uk-paired-application-adapter-20261007-v1.json', cfg)
    print(json.dumps({'cases': 4, 'target_words': [len(t.split()) for t in targets.values()], 'input_tokens': [len(c['input_ids']) for c in cases], 'training_authorized': False}))


if __name__ == '__main__':
    main()
