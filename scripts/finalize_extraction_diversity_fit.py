"""Bind two chosen-only rows to actual inspected base outputs, with native token audits."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    draft = ROOT / 'data/prepared/extraction-diversity-20261007-v1'
    dest = ROOT / 'data/prepared/extraction-diversity-fit-20261007-v1'
    assert not dest.exists()
    manifest = json.loads((draft / 'manifest.json').read_text())
    hand = json.loads((draft / 'manual-inspection.json').read_text())
    assert not manifest['training_authorized_for_this_pack']
    assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256'] == sha256(draft / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha256(draft / name) == expected
    cfgpath = ROOT / 'configs/posttraining/qwen35-extraction-diversity-fit-20261007-v1.json'
    cfg = json.loads(cfgpath.read_text())
    base = ROOT / cfg['baseline_run']
    run = json.loads((base / 'run.json').read_text())
    inspection = json.loads((base / 'inspection.json').read_text())
    assert run['status'] == 'completed' and run['mode'] == 'base' and run['optimizer_steps'] == 0
    assert inspection['all_outputs_read_complete'] and inspection['criteria_sha256'] == sha256(draft / 'criteria.json')
    assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(base / 'transcript.jsonl')
    cases = list(read_jsonl(draft / 'cases.jsonl')); targets=json.loads((draft/'preferred-targets.json').read_text())['targets']; pairs=[{'prompt':c['prompt'],'chosen':[{'role':'assistant','content':targets[c['id']]}],'rejected':[{'role':'assistant','content':'UNBOUND'}],'chat_template_kwargs':{'enable_thinking':False}} for c in cases[:2]]
    outputs = list(read_jsonl(base / 'transcript.jsonl')); assert len(cases) == len(outputs) == 3 and len(pairs) == 2
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    audits, links = [], []
    for pair, case, row in zip(pairs, cases[:2], outputs[:2], strict=True):
        assert case['id'] == row['id'] and pair['prompt'] == case['prompt']
        assert row['input_ids'] == case['input_ids']
        pair['rejected'] = [{'role': 'assistant', 'content': row['output']}]
        prefix = tok.apply_chat_template(pair['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert prefix == case['input_ids']
        audit = {'id': case['id'], 'pair_sha256': digest(pair), 'prompt_ids': prefix}
        for name in ['chosen', 'rejected']:
            ids = tok.apply_chat_template(pair['prompt'] + pair[name], tokenize=True, return_dict=False, enable_thinking=False)
            assert ids[:len(prefix)] == prefix and len(ids) <= cfg['max_length']
            audit[name + '_ids'] = ids[len(prefix):]
        audits.append(audit)
        links.append({'id': case['id'], 'run': str(base.relative_to(ROOT)), 'actual_identity': run['identity'],
            'output_digest': digest(row['output']), 'run_sha256': sha256(base / 'run.json'),
            'transcript_sha256': sha256(base / 'transcript.jsonl'), 'inspection_sha256': sha256(base / 'inspection.json')})
    dest.mkdir(parents=True)
    for source in draft.iterdir():
        if source.name not in ['manifest.json', 'manual-inspection.json', 'draft-pairs.jsonl']:
            assert source.is_file(); shutil.copy2(source, dest / source.name)
    # Preserve the original private feasibility witness; make its settlement
    # decision explicit. This file is never model input or an optimized target.
    private = dest/'private-monitor-reference.json'
    original_private = json.loads(private.read_text())
    write_json(dest/'initial-private-monitor-reference.json', original_private)
    revised = original_private['reference'].replace('condemn five settlements', 'condemn recognition of five new settlements')
    assert revised != original_private['reference'] and len(revised.split()) <= 210
    write_json(private, {**original_private, 'reference':revised, 'words':len(revised.split()),
        'correction':'Make recognition/new status explicit in private feasibility text; frozen student input, criterion and both optimized targets unchanged.'})
    write_jsonl(dest / 'pairs.jsonl', pairs); write_jsonl(dest / 'pair-audit.jsonl', audits)
    write_json(dest / 'actual-negative-provenance.json', {'links': links,
        'all_negatives_actual_inspected_base_outputs': True, 'negative_gradient_enabled': False,
        'draft_manifest_sha256': sha256(draft / 'manifest.json'),
        'scope': 'Native chosen-only NLL; rejected/reference compute retained, no active preference objective.'})
    shutil.copy2(__file__, dest / 'finalizer-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()},
        'training_authorized_for_this_pack': True, 'training_examples': 2, 'eval_cases': 3,
        'source_scope': json.loads((draft / 'provenance.json').read_text())['scope']})
    write_json(dest / 'manual-inspection.json', {**hand, 'manifest_sha256': sha256(dest / 'manifest.json'),
        'actual_negative_binding_complete': True, 'fitting_ready': True, 'negative_read_continuity': 'All3 actual base outputs read before fitting; first2 bound unchanged as zero-gradient native negatives. All preferred texts unchanged from audited draft.'})
    cfg.update(pack=str(dest.relative_to(ROOT)))
    write_json(cfgpath, cfg)
    write_json(ROOT/cfg['preparation'], {'config_sha256':sha256(cfgpath),'all_selected_texts_read_complete':True,'fit_manifest_sha256':sha256(dest/'manifest.json'),'target_source_proof_sha256':sha256(ROOT/'data/raw/compact-planner-ukraine-grounding-20261007-v1/source-proof.json'),'scope':'Two unchanged198/194word checked source-only targets, actualbase negatives withzerograd, fresh128updates/nativeobjective; data/token lengths changed; independentreview pending.'})
    print(json.dumps({'pairs': 2, 'cases': 3, 'fit_manifest_sha256': sha256(dest / 'manifest.json'), 'config_sha256': sha256(cfgpath)}))


if __name__ == '__main__':
    main()
