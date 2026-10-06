"""Seven clean actual expansions after one inspected successful-length probe."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from build_compression_teacher_probe import SYSTEM

TASK = '''EXPANSION TASK: Write350–450 ordinary English words in roughly12–16 bullets, under exactly Documented source points, Analytical decisions, Authority. Unpack every compound statement in the short content using fuller explanations of relations already stated there. Paraphrase without changing its meaning; do not reproduce the finished short memo. Preserve every name, number, negation, qualification, actor and time/scope, including current-note repairs and defects, both operations, the competing cost and the authority conclusion. Do not add a new fact, cause, purpose, guarantee, official policy condition or operational decision. Avoid unbounded all-channels commitments and invented causal guarantees. Longer explanations must restate the supplied meaning rather than import extra content. Check coverage before finishing. There is no300word ceiling for your plan:350–450words is required. Output only the three-heading bullet plan.'''
REMINDERS = {
    'wps': "Retain Germany's initiative and France's valuing of the resolution's requested SG report; do not make that a separate new request by France. Current repaired X must stay repaired, with historical omissions distinguished.",
    'mali': "The UK would not have chosen withdrawal is a UK preference, not a claim the Council has not chosen withdrawal. Welcoming2690/actualwithdrawal and conditional Council revision coexist. Retain every current X repair/defect explicitly.",
    'sanctions': "Retain funds, recruitment, evasion, due diligence and agency predictability. Current Team/reporting additions do not rewrite historical2664. Preserve supplied hypothetical endorsement when present, without other-country or future-vote extrapolation.",
    'haiti': "National capacity differs from procedural presidency. Historical2699yes and real contribution consideration do not make a troop/funding pledge or endorseX. Keep rights suspension separate from an aid-until-gang-defeat gate, and acknowledge repaired current X."
}

def main():
    old = ROOT / 'data/prepared/compression-teacher-20261006-v1'
    targets = json.loads((old / 'preferred-targets.json').read_text())['targets']
    originals = list(read_jsonl(old / 'cases.jsonl'))[1:]
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compression-teacher-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases = []
    for o in originals:
        prompt = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': 'CHECKED SHORT CONTENT (synthetic target, not new government authority):\n' + targets[o['id']] + '\n\n' + TASK + '\n\nCONTENT-RETENTION REMINDER: ' + REMINDERS[o['family']]}]
        ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        assert len(ids) + 2048 <= 8192
        cases.append({'id': o['id'], 'country_iso3': o['country_iso3'], 'family': o['family'], 'condition': 'clean_target_only_actual_teacher_expansion', 'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)})
    dest = ROOT / 'data/prepared/compression-teacher-remaining-20261006-v1'
    assert not dest.exists(); dest.mkdir(parents=True)
    write_jsonl(dest / 'cases.jsonl', cases)
    for name in ['preferred-targets.json', 'sources.json', 'criteria.json']:
        shutil.copy2(old / name, dest / name)
    write_json(dest / 'provenance.json', {'scope': 'Seven actualbase expansions after fullyinspected target-onlyprobe; only unchangedshortcontent plus retention/task prompts provided. No rawsource/memoinstructions in teacherinput. Humanprimary-source/target verification required beforestudentfit. Sameassistant, not independentreview.', 'old_pack': str(old.relative_to(ROOT)), 'old_manifest_sha256': sha256(old / 'manifest.json'), 'preferred_targets_sha256': sha256(old / 'preferred-targets.json'), 'probe_inspection_sha256': sha256(ROOT / 'runs/aurora-compression-teacher-probe-20261006-v2/inspection.json'), 'request': TASK, 'retention_reminders': REMINDERS, 'student_pack_prepared': False, 'fit_prepared': False})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 7, 'source_scope': 'Remainingseven teacher plans only; everyactualoutput handinspect/correct beforefitting.'})
    write_json(dest / 'manual-inspection.json', {'manifest_sha256': sha256(dest / 'manifest.json'), 'all_selected_texts_read_complete': True, 'read_scope': 'All7 unchangedshorttargets read inpriorserialization thisturn. Fullnew350-450word/system/finaltaskandallfourretentionreminders read; no case/source/old300word task provided. Exact target insertion verified. Sourceaudits retained, handoutputreview stillrequired.'})
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=7, phase='teacher', kind='remaining_clean_target_only_teacher_expansions')
    write_json(ROOT / 'configs/posttraining/qwen35-compression-teacher-remaining-20261006-v1.json', cfg)
    print(json.dumps({'new_calls_prepared': 7, 'optimizer_steps': 0, 'target_texts_unchanged': True}))

if __name__ == '__main__':
    main()
