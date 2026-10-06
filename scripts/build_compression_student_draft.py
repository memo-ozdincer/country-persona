"""Compile audited long-plan inputs and unchanged short targets; no fit authorization."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

def main():
    old = ROOT / 'data/prepared/diverse-country-fit-20261006-v2'
    previous_plan = ROOT / 'data/prepared/plan-input-fit-20261006-v1'
    curated_path = ROOT / 'data/curation/compression-long-plans-20261006-v1.json'
    curated = json.loads(curated_path.read_text())
    assert curated['all_selected_corrected_texts_read_complete']
    targets = json.loads((old / 'preferred-targets.json').read_text())['targets']
    original = list(read_jsonl(old / 'cases.jsonl'))[:8]
    previous = list(read_jsonl(previous_plan / 'cases.jsonl'))[:8]
    previous_plans = json.loads((previous_plan / 'teacher-plans.json').read_text())['fitting_plans']
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-plan-input-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases, audits, teacher_links = [], [], []
    for raw, point in zip(original, previous, strict=True):
        id = raw['id']; assert id == point['id']
        plan = curated['plans'][id]
        assert len(plan.split()) > 300 and len(targets[id].split()) <= 300
        case = copy.deepcopy(point)
        oldpoints = previous_plans[id]
        assert case['prompt'][1]['content'].count(oldpoints) == 1
        case['prompt'][1]['content'] = case['prompt'][1]['content'].replace(oldpoints, plan)
        assert targets[id] not in case['prompt'][1]['content']
        assert case['prompt'][1]['content'].replace(plan, oldpoints) == point['prompt'][1]['content']
        case['condition'] = 'long_plan_to_unchanged_short_target'
        ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        full = tok.apply_chat_template(case['prompt'] + [{'role': 'assistant', 'content': targets[id]}], tokenize=True, return_dict=False, **cfg['chat_template_kwargs'])
        assert full[:len(ids)] == ids and len(ids) + 2048 <= 8192
        case.update(input_ids=ids, input_ids_digest=digest(ids)); cases.append(case)
        oldaudit = next(a for a in read_jsonl(old / 'pair-audit.jsonl') if a['id'] == id)
        assert full[len(ids):] == oldaudit['chosen_ids']
        audits.append({'id': id, 'prompt_ids': ids, 'chosen_ids': full[len(ids):], 'long_plan_words': len(plan.split()),
            'short_target_words': len(targets[id].split()), 'source_original_prompt_digest': digest(raw['prompt']),
            'curated_plan_digest': digest(plan), 'chosen_tokens_exact_to_old_fit': True})
        link = curated['original_teacher_links'][id]; run = ROOT / link['run']
        row = next(v for v in read_jsonl(run / 'transcript.jsonl') if v['id'] == link['id'])
        teacher_links.append({'id': id, **link, 'actual_original_output_digest': digest(row['output']),
            'actual_identity': json.loads((run / 'run.json').read_text())['identity'],
            'transcript_sha256': sha256(run / 'transcript.jsonl'), 'inspection_sha256': sha256(run / 'inspection.json'),
            'curated_plan_digest': digest(plan), 'extensive_same_assistant_correction_or_rewrite': True})
    dest = ROOT / 'data/prepared/compression-student-draft-20261006-v2'
    assert not dest.exists(); dest.mkdir(parents=True)
    write_jsonl(dest / 'cases.jsonl', cases); write_jsonl(dest / 'chosen-token-audit.jsonl', audits)
    for name in ['preferred-targets.json', 'sources.json', 'criteria.json']:
        shutil.copy2(old / name, dest / name)
    shutil.copy2(curated_path, dest / 'curated-plans.json')
    write_json(dest / 'actual-teacher-provenance.json', {'links': teacher_links,
        'scope': 'ActualQwen3.5 drafts retained, extensively corrected/rewritten bysameassistant. Not independent teacherquality evidence. Teacheroriginal sees shorttargets; student gets longcuratedplans/source/case, nevershorttarget prose as input.'})
    write_json(dest / 'provenance.json', {'scope': 'Eight audited long-to-short realization examples, unchangedpreferredtexts/nativechosentokens. Same original source/case/system/contract, only plan representation changes relative sentence-point recipe. No studentcalls, baseline negatives, fitpack oroptimization authorized. NewLibya primarysource acquired but heldrubric/controls still needed.',
        'old_pack': str(old.relative_to(ROOT)), 'old_manifest_sha256': sha256(old / 'manifest.json'),
        'old_plan_pack': str(previous_plan.relative_to(ROOT)), 'old_plan_manifest_sha256': sha256(previous_plan / 'manifest.json'),
        'preferred_targets_sha256': sha256(old / 'preferred-targets.json'), 'curation_file_sha256': sha256(curated_path),
        'fitting_ready': False, 'remaining_gates': ['Freeze/source-audit Libyahold criteria/plans and prospectivepresentation checks.', 'Matchinginspectedactualbasecontrols/negatives.', 'Bindfreshfitconfiguration/pack, inspectcomparison beforefit.']})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()}, 'training_authorized_for_this_pack': False, 'training_examples': 8, 'eval_cases': 8, 'source_scope': 'Curated long-plan student draft only; no optimization/queuedfit.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'),
        'read_scope': 'All8curatedlongplans/shorttargets hand-read and aligned. Four sharedcompleteDocsections and everycase-specific application/authority reread afterserialization. Sharedoriginalsource/currentcase/system/contract retain priorwhole-source/fullrequest audits with exact reverse replacement; newnativeids/chosencompletion lengths checked. Dataannotation quality, not student performance; independentreview pending.', 'teacher_correction_disclosed': True, 'fitting_ready': False})
    print(json.dumps({'examples': 8, 'long_plan_words': {a['id']: a['long_plan_words'] for a in audits}, 'short_target_words': {a['id']: a['short_target_words'] for a in audits}, 'chosen_tokens_exact': True, 'fit_authorized': False}))

if __name__ == '__main__':
    main()
