"""One larger allowance, selected only after both sampled2048 caps were inspected."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import sha256,write_json

def main():
    original=ROOT/'data/prepared/native-sampling-20261006-v1';out=ROOT/'data/prepared/native-sampling-20261006-v2'
    if out.exists():raise ValueError('Fresh pack required')
    previous=ROOT/'runs/aurora-native-sampling-adapter-20261006-v1'
    review=json.loads((previous/'inspection.json').read_text());assert review['all_outputs_read_complete'] and review['all_reasoning_read_complete']
    trace=json.loads((previous/'transcript.jsonl').read_text());assert trace['at_output_cap'] and trace['protocol_status']=='no_public_boundary'
    out.mkdir()
    for name in ('cases.jsonl','criteria.json','wps-statements.json','source-proof.json'):(out/name).write_bytes((original/name).read_bytes())
    (out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
    manifest=json.loads((original/'manifest.json').read_text());manifest.update(question='Does one4096total-token author-profile allowance reach public answers, and does the saved adapter improve their fidelity?',
        decision='One base4096call, inspect, then one matching adapter4096call. Budget correction selected from completed2048cap failures. No further allowance/seed sweep or training queued.',
        comparison_scope='Only max_new_tokens2048→4096 versus sampledv1; model/profile/seed/source/rubric unchanged. This pair compares weights at4096, not a fully matched new thinking/off factorial.',
        selection_inspection_sha256=sha256(previous/'inspection.json'),files_sha256={p.name:sha256(p) for p in out.iterdir() if p.is_file()})
    write_json(out/'manifest.json',manifest)
    inspection=json.loads((original/'manual-inspection.json').read_text());inspection.update(manifest_sha256=sha256(out/'manifest.json'),reviewed_at=datetime.now(timezone.utc).isoformat(),budget_review='Both complete2048token sampled traces hand read; no public boundary. Same complete source/question/rubric/profile bytes reread/verified unchanged.4096+1228=5324fits8192guard; model context/rope unchanged.')
    write_json(out/'manual-inspection.json',inspection)
    config=json.loads((ROOT/'configs/posttraining/qwen35-native-sampling-20261006-v1.json').read_text());config.update(pack=str(out.relative_to(ROOT)),generation_max_new_tokens=4096,kind='one_evidence_selected_native_sampling_budget_correction')
    write_json(ROOT/'configs/posttraining/qwen35-native-sampling-20261006-v2.json',config)
    print('Same source/rubric/profile;4096total tokens, no optimizer.')
if __name__=='__main__':main()
