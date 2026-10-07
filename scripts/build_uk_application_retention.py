"""Check the saved UK continuation on two exact historical France/India fitting inputs."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl


def main():
    dest = ROOT / 'data/prepared/uk-application-retention-20261007-v1'
    assert not dest.exists()
    old = ROOT / 'data/prepared/two-country-application-fit-20261007-v1'
    origin = ROOT / 'runs/aurora-two-country-application-fit-20261007-v1'
    cases = list(read_jsonl(old / 'cases.jsonl'))
    rows = list(read_jsonl(origin / 'transcript.jsonl'))
    inspection = json.loads((origin / 'inspection.json').read_text())
    fit = ROOT / 'runs/aurora-uk-paired-application-fit-20261007-v1'
    i = json.loads((fit / 'inspection.json').read_text())
    assert i['all_outputs_read_complete'] and i['transcript_sha256'] == sha256(fit / 'transcript.jsonl')
    chosen = [copy.deepcopy(cases[j]) for j in [0, 3]]
    links = []
    for j, c in zip([0, 3], chosen, strict=True):
        assert c['id'] == rows[j]['id'] and c['input_ids'] == rows[j]['input_ids']
        links.append({'run': str(origin.relative_to(ROOT)), 'id': c['id'], 'transcript_sha256': sha256(origin / 'transcript.jsonl'), 'inspection_sha256': sha256(origin / 'inspection.json'), 'previous_review': inspection['reviews'][j]})
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', chosen)
    for f in ['criteria.json', 'sources.json', 'manual-evaluation-expectations.json', 'presentation-criteria.json']:
        shutil.copy2(old / f, dest / f)
    write_json(dest / 'provenance.json', {'exact_historical_controls': links, 'selected_after_UK_fit_inspection': True, 'scope': 'Exact original fitted France Z and India N tokens/criteria; parent outputs reused, new continuation cold-loaded. Exposed retention, no source-held confirmation or new targets.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 2, 'source_scope': 'Two historical fitting retention controls after inspected UK64 continuation; no fitting or independent quality claim.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Complete primary French and Indian speeches, both full original factual/input/scenario texts, old criteria and actual original outputs fully hand-read. No token or factual change.'})
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-uk-paired-application-base-20261007-v1.json').read_text())
    a = fit / 'adapter'
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=2, adapter=str(a.relative_to(ROOT)), adapter_sha256=sha256(a / 'adapter_model.safetensors'), adapter_config_sha256=sha256(a / 'adapter_config.json'), kind='UK64_continuation_exact_France_India_retention')
    write_json(ROOT / 'configs/posttraining/qwen35-uk-application-retention-20261007-v1.json', cfg)
    print(json.dumps({'cases': 2, 'inputs_unchanged': True, 'new_steps': 0}))


if __name__ == '__main__':
    main()
