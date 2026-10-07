"""Give the writer two complete actual outputs only, with no duplicate raw scenario."""
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
    dest = ROOT / 'data/prepared/uk-complete-plan-writer-20261007-v1'
    assert not dest.exists()
    components = [('aurora-uk-quote-backed-source96-20261007-v1', 'uk-unitams-quote-backed-full-source-summary'), ('aurora-uk-paired-application-fit-20261007-v1', 'uk-E-existing-repair-application')]
    parts, links = [], []
    for name, identifier in components:
        d = ROOT / 'runs' / name
        r = json.loads((d / 'run.json').read_text())
        i = json.loads((d / 'inspection.json').read_text())
        assert r['status'] == 'completed' and i['all_outputs_read_complete']
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        row = next(x for x in read_jsonl(d / 'transcript.jsonl') if x['id'] == identifier)
        review = next(x for x in i['reviews'] if x['id'] == identifier)
        assert review.get('source_only_task_pass', review.get('component_pass'))
        parts.append(row['output'])
        links.append({'run': str(d.relative_to(ROOT)), 'id': identifier, 'row_digest': digest(row), 'transcript_sha256': sha256(d / 'transcript.jsonl'), 'inspection_sha256': sha256(d / 'inspection.json'), 'unedited_content': True})
    plan = '\n\n'.join(parts)
    assert len(plan.split()) == 285
    old = ROOT / 'data/prepared/uk-raw-writer-20261007-v1'
    template = list(read_jsonl(old / 'cases.jsonl'))[0]
    body = '''COUNTRY/ROLE/DATE: UK, Kariuki, national Council representative after voting, 1 December 2023, S/PV.9492. Ecuador chairs. Welcome is not a supplied national vote label.

ACTUAL MODEL-GENERATED SOURCE FACTS PLUS APPLICATION FOR E (two stored complete unedited outputs; analysis is not government authority):
''' + plan + '''

TASK: Realize the supplied points as a concise country memo in at most300 ordinary English words under exactly Documented position, Analytical application and Authority. Preserve all eight documentary meanings and six application/authority meanings. The Existing and Repair bullets distinguish current E clauses from desired changes; retain that distinction. Include the supplied scoped operational directions and competing cost, real historical actions and continuing cooperation. Recommendations remain analysis of the dated national source, not a new official national statement. Do not invent a writing date, commitment, vote, condition, deadline, amount or extra scenario. Use readable prose. Do not reproduce any source or plan in multiple sections. No additional raw scenario or teacher decisions are supplied.'''
    case = copy.deepcopy(template)
    case.update(id='uk-E-complete-actual-plan-only-writer', condition='actual285_source_and_nonfitting_E_application_only', prompt=[template['prompt'][0], {'role': 'user', 'content': body}])
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-uk-raw-writer-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='UK_complete_actual285_plan_only_writer', task_max_words=300)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    assert len(ids) + 2048 <= 8192
    case.update(input_ids=ids, input_ids_digest=digest(ids))
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', [case])
    for f in ['criteria.json', 'sources.json', 'presentation-criteria.json']:
        shutil.copy2(old / f, dest / f)
    shutil.copy2(ROOT / 'data/prepared/uk-paired-application-20261007-v1/manual-evaluation-expectations.json', dest / 'manual-evaluation-expectations.json')
    write_json(dest / 'actual-plan.json', {'plan': plan, 'words': 285, 'components': links, 'facts_are_model_generated': True, 'application_unedited': True, 'source_is_fitting_reply': False, 'application_is_fitting_state': False, 'application_intermediate_pass': True, 'scope': 'Literal 201+84 outputs. E excluded from two new training targets but exposed before fitting; UK source fits application R/S and historical writer context. No human rewrite.'})
    write_json(dest / 'provenance.json', {'original_source8_and_common6_unchanged': True, 'scope': 'Complete actual E plan replaces incomplete R plan; full raw scenario removed from writer. Completeness/state/protocol change together; matched base/point8 input, not isolated removal effect or sealed OOD/persona gain. No new writer/source optimization.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'One complete actual285-point plan-only realization, full14/four guards/300words/three sections; base/point8, no optimization.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Complete primary, both actual201/84 outputs, literal285 plan, full14/source/presentation criteria and E state interpretation hand-read. No manual edit or new target.'})
    write_json(ROOT / 'configs/posttraining/qwen35-uk-complete-plan-writer-base-20261007-v1.json', cfg)
    a = ROOT / 'runs/aurora-plan-input-fit-20261006-v1/adapter'
    cfg.update(adapter=str(a.relative_to(ROOT)), adapter_sha256=sha256(a / 'adapter_model.safetensors'), adapter_config_sha256=sha256(a / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-uk-complete-plan-writer-point8-20261007-v1.json', cfg)
    print(json.dumps({'plan_words': 285, 'input_tokens': len(ids), 'intermediate_application_pass': True, 'new_writer_steps': 0}))


if __name__ == '__main__':
    main()
