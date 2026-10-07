"""Bind six unchanged chosen targets to real inspected base outputs for one mixed fit."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    draft = ROOT / 'data/prepared/three-country-application-20261007-v1'
    dest = ROOT / 'data/prepared/three-country-application-fit-20261007-v1'
    assert not dest.exists()
    hand = json.loads((draft / 'manual-inspection.json').read_text())
    m = json.loads((draft / 'manifest.json').read_text())
    assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256'] == sha256(draft / 'manifest.json')
    assert not m['training_authorized_for_this_pack']
    for f, h in m['files_sha256'].items():
        assert sha256(draft / f) == h
    base = ROOT / 'runs/aurora-three-country-application-base-replay-20261007-v1'
    r = json.loads((base / 'run.json').read_text())
    i = json.loads((base / 'inspection.json').read_text())
    assert r['status'] == 'completed_cpu_replay' and i['all_outputs_read_complete']
    assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(base / 'transcript.jsonl')
    comparison = ROOT / 'runs/aurora-brazil-application-sequential192-20261007-v1'
    ci = json.loads((comparison / 'inspection.json').read_text())
    assert ci['all_outputs_read_complete'] and ci['transcript_sha256'] == sha256(comparison / 'transcript.jsonl')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-two-country-application-fit-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), max_steps=192, training_examples=6, eval_cases=10, kind='fresh_mixed_six_unchanged_application_targets192', baseline_run=str(base.relative_to(ROOT)), comparison_run=str(comparison.relative_to(ROOT)), preparation='reports/three-country-application-preparation-20261007-v1.json')
    cases = list(read_jsonl(draft / 'cases.jsonl'))
    rows = list(read_jsonl(base / 'transcript.jsonl'))
    assert [c['input_ids'] for c in cases] == [row['input_ids'] for row in rows]
    targets = json.loads((draft / 'preferred-targets.json').read_text())['targets']
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    pairs, audits = [], []
    for c, row in zip(cases[:6], rows[:6], strict=True):
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
    dest.mkdir()
    for f in draft.iterdir():
        if f.name not in ['manifest.json', 'manual-inspection.json']:
            shutil.copy2(f, dest / f.name)
    write_jsonl(dest / 'pairs.jsonl', pairs)
    write_jsonl(dest / 'pair-audit.jsonl', audits)
    write_json(dest / 'actual-negative-provenance.json', {'base_replay_run': str(base.relative_to(ROOT)), 'base_replay_sha256': sha256(base / 'run.json'), 'base_replay_transcript_sha256': sha256(base / 'transcript.jsonl'), 'base_replay_inspection_sha256': sha256(base / 'inspection.json'), 'source_links': r['source_links'][:6], 'negative_gradient_enabled': False, 'scope': 'Six real base errors copied unchanged, actual source GPU identities retained; replay is CPU provenance aggregation, not six new model calls.'})
    shutil.copy2(__file__, dest / 'finalizer-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': True, 'training_examples': 6, 'eval_cases': 10, 'source_scope': 'One fresh six-target192 chosen-only fit,32 presentations each, fixed texts/inputs same as sequential192. Single mixed optimizer/order differ. UK T/E and Brazil J/K excluded, all exposed controls frozen before fit.'})
    write_json(dest / 'manual-inspection.json', {**hand, 'manifest_sha256': sha256(dest / 'manifest.json'), 'actual_negative_binding_complete': True, 'fitting_ready': True, 'scope': 'All four primary speeches/10 complete inputs/6 unchanged targets/10 base outputs and two sequential Brazil replies manually read. First6 actual base errors bound as zero-gradient negatives. No independent author/grader.'})
    path = ROOT / 'configs/posttraining/qwen35-three-country-application-fit-20261007-v1.json'
    write_json(path, cfg)
    write_json(ROOT / cfg['preparation'], {'config_sha256': sha256(path), 'all_selected_texts_read_complete': True, 'fit_manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'One bounded fresh mixed6/192 comparison to sequential192; same6 texts/inputs and32 presentations each. No teacher target edits, active preference/KL, source/writer updates or queue.'})
    print(json.dumps({'pairs': 6, 'cases': 10, 'updates': 192, 'presentations_each': 32, 'fitting_authorized': True}))


if __name__ == '__main__':
    main()
