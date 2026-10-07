"""Bind two complete UK targets to inspected real parent errors; authorize one 64-update fit."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    draft = ROOT / 'data/prepared/uk-paired-application-20261007-v1'
    dest = ROOT / 'data/prepared/uk-paired-application-fit-20261007-v1'
    assert not dest.exists()
    manifest = json.loads((draft / 'manifest.json').read_text())
    hand = json.loads((draft / 'manual-inspection.json').read_text())
    assert not manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(draft / 'manifest.json')
    for f, h in manifest['files_sha256'].items():
        assert sha256(draft / f) == h
    base = ROOT / 'runs/aurora-uk-paired-application-base-20261007-v1'
    parent = ROOT / 'runs/aurora-uk-paired-application-parent-20261007-v1'
    controls = []
    for d in [base, parent]:
        r = json.loads((d / 'run.json').read_text())
        i = json.loads((d / 'inspection.json').read_text())
        assert r['status'] == 'completed' and i['all_outputs_read_complete']
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        assert i['criteria_sha256'] == sha256(draft / 'criteria.json')
        controls.append({'run': str(d.relative_to(ROOT)), 'run_sha256': sha256(d / 'run.json'), 'transcript_sha256': sha256(d / 'transcript.jsonl'), 'inspection_sha256': sha256(d / 'inspection.json')})
    cases = list(read_jsonl(draft / 'cases.jsonl'))
    negatives = list(read_jsonl(parent / 'transcript.jsonl'))
    assert [c['input_ids'] for c in cases] == [r['input_ids'] for r in negatives]
    targets = json.loads((draft / 'preferred-targets.json').read_text())['targets']
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-uk-paired-application-base-20261007-v1.json').read_text())
    adapter = ROOT / 'runs/aurora-two-country-application-fit-20261007-v1/adapter'
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='UK_two_paired_states_warm_chosen_only64', max_steps=64, training_examples=2, eval_cases=4, parent_steps=128, starting_adapter=str(adapter.relative_to(ROOT)), starting_adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), starting_adapter_config_sha256=sha256(adapter / 'adapter_config.json'), initialization='continue_saved_application128_new_optimizer', baseline_run=str(parent.relative_to(ROOT)), comparison_run=str(parent.relative_to(ROOT)), preparation='reports/uk-paired-application-preparation-20261007-v1.json')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    pairs, audits, links = [], [], []
    for c, row in zip(cases[:2], negatives[:2], strict=True):
        assert c['id'] == row['id']
        pair = {'prompt': c['prompt'], 'chosen': [{'role': 'assistant', 'content': targets[c['id']]}], 'rejected': [{'role': 'assistant', 'content': row['output']}], 'chat_template_kwargs': {'enable_thinking': False}}
        prefix = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert prefix == c['input_ids']
        audit = {'id': c['id'], 'pair_sha256': digest(pair), 'prompt_ids': prefix}
        for arm in ['chosen', 'rejected']:
            ids = tok.apply_chat_template(pair['prompt'] + pair[arm], tokenize=True, return_dict=False, enable_thinking=False)
            assert ids[:len(prefix)] == prefix and len(ids) <= cfg['max_length']
            audit[arm + '_ids'] = ids[len(prefix):]
        pairs.append(pair)
        audits.append(audit)
        links.append({'id': c['id'], 'run': str(parent.relative_to(ROOT)), 'output_digest': digest(row['output']), 'transcript_sha256': sha256(parent / 'transcript.jsonl'), 'inspection_sha256': sha256(parent / 'inspection.json')})
    dest.mkdir()
    for f in draft.iterdir():
        if f.name not in ['manifest.json', 'manual-inspection.json']:
            shutil.copy2(f, dest / f.name)
    write_jsonl(dest / 'pairs.jsonl', pairs)
    write_jsonl(dest / 'pair-audit.jsonl', audits)
    write_json(dest / 'actual-negative-provenance.json', {'links': links, 'controls': controls, 'negative_gradient_enabled': False, 'draft_manifest_sha256': sha256(draft / 'manifest.json'), 'scope': 'Two actual inspected parent errors, native chosen-only NLL; rejected/reference diagnostics computed with zero preference gradient. Partial T/E excluded from fitting, exposed by inspected controls.'})
    shutil.copy2(__file__, dest / 'finalizer-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': True, 'training_examples': 2, 'eval_cases': 4, 'source_scope': 'One inspected UK R/S 64-update continuation from application128,32 presentations each; T/E not fitted but exposed development controls. Fixed actual201 source, six compounds/90word application. No writer/source updates.'})
    write_json(dest / 'manual-inspection.json', {**hand, 'manifest_sha256': sha256(dest / 'manifest.json'), 'actual_negative_binding_complete': True, 'fitting_ready': True, 'scope': 'Complete primary/actual201 facts/four inputs/two85-word targets/eight parent-base outputs/real negative tokens all hand-read. Only R/S optimized; no independent teacher/grader.'})
    path = ROOT / 'configs/posttraining/qwen35-uk-paired-application-fit-20261007-v1.json'
    write_json(path, cfg)
    write_json(ROOT / cfg['preparation'], {'config_sha256': sha256(path), 'all_selected_texts_read_complete': True, 'fit_manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'One source-audited two-target chosen-only64 continuation with saved application128 initialization,32 each, same matched controls. No queue/sweep or negative/reference gradient.'})
    print(json.dumps({'pairs': 2, 'cases': 4, 'updates': 64, 'presentations_each': 32, 'starting_steps': 128}))


if __name__ == '__main__':
    main()
