"""Combine actual base outputs without inventing GPU calls or changing historical reviews."""
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl


def main():
    dest = ROOT / 'runs/aurora-paired-brazil-application-base-replay-20261007-v1'
    assert not dest.exists()
    cfgpath = ROOT / 'configs/posttraining/qwen35-paired-brazil-application-base-20261007-v1.json'
    cfg = json.loads(cfgpath.read_text())
    p = ROOT / cfg['pack']
    cases = list(read_jsonl(p / 'cases.jsonl'))
    names=[]
    for c in cases:
        if c['id'].startswith('brazil-M'): name='aurora-brazil-M-base-20261007-v1'
        elif c['id'].startswith('brazil-L'): name='aurora-brazil-L-base-20261007-v1'
        elif c['id'].startswith('brazil-'): name='aurora-brazil-application-base-20261007-v1'
        elif c['id'].startswith('india-P-authenticated'): name='aurora-authenticated-india-base-20261007-v1'
        elif c['country_iso3']=='GBR': name='aurora-uk-paired-application-base-20261007-v1'
        else: name='aurora-two-country-application-base-20261007-v1'
        names.append(name)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    rows, links, annotations, source_gpu_names = [], [], {}, set()
    for c, name in zip(cases, names, strict=True):
        d = ROOT / 'runs' / name
        r = json.loads((d / 'run.json').read_text())
        i = json.loads((d / 'inspection.json').read_text())
        assert r['status'] == 'completed' and r['mode'] == 'base' and r['optimizer_steps'] == 0 and i['all_outputs_read_complete']
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        assert r['versions'] == cfg['runtime_pins']
        for k in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert r['config'][k] == cfg[k]
        row = copy.deepcopy(next(x for x in read_jsonl(d / 'transcript.jsonl') if x['id'] == c['id']))
        assert row['input_ids'] == c['input_ids'] == tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
        ann = json.loads((d / 'manual-annotations.json').read_text())['cases'][c['id']]
        annotations[c['id']] = copy.deepcopy(ann)
        rows.append(row)
        links.append({'id': c['id'], 'run': str(d.relative_to(ROOT)), 'run_sha256': sha256(d / 'run.json'), 'transcript_sha256': sha256(d / 'transcript.jsonl'), 'inspection_sha256': sha256(d / 'inspection.json'), 'actual_identity': r['identity'], 'gpu': r['gpu'], 'generation_helper_sha256': r['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']})
        source_gpu_names.add(r['gpu']['name'])
    assert source_gpu_names == {'NVIDIA RTX PRO 6000 Blackwell Server Edition'}
    assert len({x['generation_helper_sha256'] for x in links}) == 1
    dest.mkdir()
    write_jsonl(dest / 'transcript.jsonl', rows)
    write_json(dest / 'manual-annotations.json', {'all_outputs_hand_read_complete': True, 'cases': annotations, 'scope': 'Thirteen original full outputs manually read; twelve stored base reviews and newM copied unchanged. No new model call, no GPU identity fabricated.'})
    write_json(dest / 'run.json', {'status': 'completed_cpu_replay', 'mode': 'base', 'config': cfg, 'config_sha256': sha256(cfgpath), 'versions': cfg['runtime_pins'], 'optimizer_steps': 0, 'outputs': len(rows), 'pack_manifest_sha256': sha256(p / 'manifest.json'), 'transcript_sha256': sha256(dest / 'transcript.jsonl'), 'source_links': links, 'source_gpu_names': sorted(source_gpu_names), 'generation_helper_sha256': links[0]['generation_helper_sha256'], 'created_at': datetime.now(timezone.utc).isoformat(), 'scope': 'CPU combination of thirteen actual outputs: twelve historical reused and one newM call. Not a new GPU run.', 'independent_review_complete': False})
    print(json.dumps({'outputs_replayed': 13, 'new_model_calls': 0, 'reused_historical_outputs': 12, 'new_M_output_already_counted': 1}))


if __name__ == '__main__':
    main()
