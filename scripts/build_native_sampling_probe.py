"""Prepare one fixed author-profile pair only after inspected greedy-cap failures."""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import sha256, write_json


def main():
    old = ROOT / 'data/prepared/native-reasoning-20261006-v1'; out = ROOT / 'data/prepared/native-sampling-20261006-v1'
    guide = ROOT / 'runs/native-reasoning-guidance-20261006-v1'
    if out.exists() or guide.exists(): raise ValueError('Fresh preparation directories required')
    inspected = ROOT / 'runs/aurora-native-reasoning-adapter-on-20261006-v1'
    review = json.loads((inspected / 'inspection.json').read_text()); assert review['all_outputs_read_complete'] and review['all_reasoning_read_complete']
    assert review['transcript_sha256'] == sha256(inspected / 'transcript.jsonl')
    url = 'https://huggingface.co/Qwen/Qwen3.5-4B/resolve/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md'
    guide.mkdir(); body = urllib.request.urlopen(url, timeout=60).read(); (guide / 'README.md').write_bytes(body)
    write_json(guide / 'acquisition.json', {'url': url, 'bytes': len(body), 'sha256': sha256(guide / 'README.md'), 'retrieved_at': datetime.now(timezone.utc).isoformat(),
               'sections_hand_read': 'Quickstart/Best Practices general-thinking sampling, presence semantics and output-length recommendations. No published-benchmark reproduction claim.',
               'presence_semantics_source': 'https://docs.vllm.ai/en/latest/api/vllm/sampling_params/', 'presence_semantics': 'Fixed logit penalty once per distinct generated token, excluding prompt; not frequency penalty. Explicit Transformers port.'})
    out.mkdir()
    for name in ('cases.jsonl', 'criteria.json', 'wps-statements.json', 'source-proof.json'): (out / name).write_bytes((old / name).read_bytes())
    (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
    manifest = json.loads((old / 'manifest.json').read_text())
    manifest.update(question='Does author general-thinking sampling/presence avoid the greedy drafting loop and improve public fidelity within the same2048token allowance?', planned_model_answers=2,
                    decision='After four inspected greedy controls: one sampled base call, inspect, then one matching saved-adapter call. One fixed seed, no fit/sweep.',
                    comparison_scope='Compound decoder change; model/source/rubric/budget unchanged. No isolated presence effect or expected-performance claim from one draw.',
                    selection_inspection_sha256=sha256(inspected / 'inspection.json'), guidance_acquisition_sha256=sha256(guide / 'acquisition.json'),
                    files_sha256={p.name: sha256(p) for p in out.iterdir() if p.is_file()})
    write_json(out / 'manifest.json', manifest)
    inspection = json.loads((old / 'manual-inspection.json').read_text()); inspection.update(manifest_sha256=sha256(out / 'manifest.json'), profile_read='Author general-thinking temperature1/top_p.95/top_k20/min_p0/presence1.5/repetition1; both consistent model-card sections. Same2048cap intentionally retained, below general32Krecommendation. Identical source/criteria bytes already read.')
    write_json(out / 'manual-inspection.json', inspection)
    config = json.loads((ROOT / 'configs/posttraining/qwen35-native-reasoning-on-20261006-v1.json').read_text())
    config.update(pack=str(out.relative_to(ROOT)), kind='versioned_author_general_thinking_profile_same_budget',
                  sampling_profile={'temperature': 1., 'top_p': .95, 'top_k': 20, 'min_p': 0., 'presence_penalty': 1.5, 'repetition_penalty': 1.}, guidance_url=url)
    write_json(ROOT / 'configs/posttraining/qwen35-native-sampling-20261006-v1.json', config)


if __name__ == '__main__': main()
