"""Preserve French targets, add two audited India targets and freeze a fourth Indian state."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest

INDIA_TARGETS = [
'''Analytical decisions:
- Keep added proactive 1267 Monitoring Team involvement and robust reports, provisional sanctions, trade and anti-mainstreaming safeguards. Reject the all-shipment clearance gate and claimed historical completion.
- Release verified urgent aid with risk-targeted checks; send diversion reports to the Monitoring Team. Reporting costs staff time versus delivery speed.
- India negotiated 2664 constructively; hopes review and Team feedback correct shortfalls.
Authority:
- Official M endorsement and a future vote are unknown. Recommendations are analytical.''',
'''Analytical decisions:
- Keep prompt verified shipments, risk-targeted checks, provisional sanctions, trade and anti-mainstreaming safeguards. Restore proactive 1267 Monitoring Team involvement and robust reporting; historical concerns were not fully addressed.
- Assign diversion follow-up to the Monitoring Team; define agency reporting standards while aid continues. Oversight costs staff time versus delivery speed.
- India negotiated 2664 constructively; hopes review and Team feedback correct shortfalls.
Authority:
- Official N endorsement and a future vote are unknown. Recommendations are analytical.''']

NOTE_Q = '''Alternative hypothetical implementation note Q retains provisional sanctions, legitimate trade, targeted due diligence and safeguards against terrorist exploitation or political mainstreaming. Verified urgent life-saving shipments leave promptly while ongoing checks target identified diversion risks. It gives the 1267 Monitoring Team a proactive role but leaves reporting standards unchanged, without robust diversion reports. A colleague claims every Indian concern is satisfied, both requests were already fully secured in the historical resolution, India officially endorses Q, and its next Council vote is guaranteed favourable. No new national authority is supplied. Q is hypothetical.'''


def main():
    dest = ROOT / 'data/prepared/two-country-application-20261007-v1'; assert not dest.exists()
    india = ROOT / 'data/prepared/country-application-transfer-20261007-v1'
    france = ROOT / 'data/prepared/paired-application-fit-20261007-v1'
    previous = ROOT / 'runs/aurora-country-application-transfer-adapter-20261007-v1'
    inspected = json.loads((previous / 'inspection.json').read_text())
    assert inspected['all_outputs_read_complete'] and inspected['transcript_sha256'] == sha256(previous / 'transcript.jsonl')
    french = list(read_jsonl(france / 'cases.jsonl'))[:2]; ind = list(read_jsonl(india / 'cases.jsonl'))
    fourth = copy.deepcopy(ind[1]); t = fourth['prompt'][1]['content']
    a = t.index('CURRENT HYPOTHETICAL NOTE'); b = t.index('\n\nTASK:', a)
    t = t[:a] + 'CURRENT HYPOTHETICAL NOTE (Q):\n' + NOTE_Q + t[b:]
    t = t.replace('current N,', 'current Q,').replace('remaining N claims', 'remaining Q claims').replace('official N endorsement', 'official Q endorsement')
    fourth.update(id='india-sanctions-team-only-application-monitor', condition='new_partial_repair_team_present_reporting_missing', prompt=[fourth['prompt'][0], {'role': 'user', 'content': t}])
    fourth.pop('input_ids'); fourth.pop('input_ids_digest')
    cases = french + ind + [fourth]
    targets = {c['id']: json.loads((france / 'preferred-targets.json').read_text())['targets'][c['id']] for c in french}
    targets.update({c['id']: target for c, target in zip(ind[:2], INDIA_TARGETS, strict=True)})
    assert len(targets) == 4 and all(len(t.split()) <= 90 for t in targets.values())
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=6, kind='two_countries_four_application_targets_two_India_monitors', baseline_run='runs/aurora-two-country-application-base-20261007-v1')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    for c in cases:
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        if 'input_ids' in c: assert c['input_ids'] == ids
        assert len(ids) + 2048 <= 8192
        c.update(input_ids=ids, input_ids_digest=digest(ids))
    criteria = json.loads((india / 'criteria.json').read_text()); oldcriteria = json.loads((france / 'criteria.json').read_text())
    assert criteria['common_units'] == oldcriteria['common_units'] and criteria['universal_checks'] == oldcriteria['universal_checks']
    criteria['source_units']['ukraine24'] = {'FRA': {}}
    sources = json.loads((india / 'sources.json').read_text()); sources['ukraine24'] = json.loads((france / 'sources.json').read_text())['ukraine24']
    expectations = json.loads((india / 'manual-evaluation-expectations.json').read_text())
    expectations['states']['team-only'] = 'Acknowledge prompt aid, targeted checks and present proactive Team role; identify only missing robust reporting plus false historical full satisfaction. Do not repeat removed gate or ask to remove present Team. Give two scoped operations/cost; retain constructive2664 engagement and review/Team-feedback hope; no official endorsement/future vote.'
    expectations['source_audit'] = expectations['source_audit'].replace('both requested mechanisms/absence in final text', 'both requested mechanisms/not-fully-addressed concerns in final text')
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', cases); write_json(dest / 'criteria.json', criteria); write_json(dest / 'sources.json', sources)
    write_json(dest / 'preferred-targets.json', {'targets': targets, 'words': [len(t.split()) for t in targets.values()], 'author': 'Same root assistant; original French texts byte-identical, two new source-hand-audited Indian texts. No independent teacher/API transcript.'})
    write_json(dest / 'manual-target-audit.json', {'all_targets_hand_read_complete': True, 'France_83_79_unchanged': True,
               'M': 'Retains both hypothetical additions/valid safeguards; rejects still-present shipment gate and false historical satisfaction, two scoped acts/cost, actual constructive engagement/review-feedback hope, analytical/no-endorsement authority.',
               'N': 'Retains real prompt shipment/risk-check repairs; restores only absent proactive role/reporting, no recreated gate, two scoped acts/cost, same real history/hope and authority.',
               'source_qualification': 'Specific concerns NOT FULLY addressed historically, not proof of total omission. A policy recommendation is not an official new Indian commitment.',
               'independent_review_complete': False})
    for f in ['presentation-criteria.json', 'source-facts.json']: shutil.copy2(india / f, dest / f)
    write_json(dest / 'manual-evaluation-expectations.json', expectations)
    write_json(dest / 'provenance.json', {'France_fit_manifest_sha256': sha256(france / 'manifest.json'), 'India_monitor_manifest_sha256': sha256(india / 'manifest.json'),
               'previous_transfer_inspection_sha256': sha256(previous / 'inspection.json'),
               'scope': 'Proposed fresh4target128update chosen-only fit after inspected transfer failure. French texts/inputs/exposure32 retained; adds two India states32each, doubles totalbudget64to128. Indian P exposed development monitor; newQ frozen before calls/fit. Same source facts, no extractor/writer update. Country/data/dose change together; no pure diversity or strong OOD/persona/multi-agent gain.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()},
               'training_authorized_for_this_pack': False, 'training_examples': 4, 'eval_cases': 6, 'source_scope': 'Two French and two Indian preferred application states, two Indian states absent from fit (P exposed, Q newly frozen). Source-guided six-unit90word task, same assistant author/grader.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'),
               'scope': 'Complete selected sources, all original/new factual points, six full inputs/notes/questions, all six criteria/guards and four full preferred targets read by root. Original France texts/IDs unchanged. No future fit before actualbase inspection/binding.'})
    write_json(ROOT / 'configs/posttraining/qwen35-two-country-application-base-20261007-v1.json', cfg)
    print(json.dumps({'cases': 6, 'targets': 4, 'target_words': [len(t.split()) for t in targets.values()], 'input_tokens': [len(c['input_ids']) for c in cases], 'fit_authorized': False}))


if __name__ == '__main__': main()
