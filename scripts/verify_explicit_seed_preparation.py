"""CPU-only byte/token/provenance checks; no model or semantic quality result."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json
from build_explicit_seed_control import MODE, REMOVE


def main():
    from transformers import AutoTokenizer
    p = ROOT / 'data/prepared/explicit-seed-control-20261007-v1'
    provenance = json.loads((p / 'provenance.json').read_text())
    old = ROOT / provenance['parent_pack']
    m, hand = json.loads((p / 'manifest.json').read_text()), json.loads((p / 'manual-inspection.json').read_text())
    assert not m['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(p / 'manifest.json')
    assert provenance['parent_manifest_sha256'] == sha256(old / 'manifest.json')
    assert provenance['parent_cases_sha256'] == sha256(old / 'cases.jsonl')
    assert provenance['parent_provenance_sha256'] == sha256(old / 'provenance.json')
    for name, value in m['files_sha256'].items(): assert sha256(p / name) == value
    for name in ['criteria.json', 'full-primary-spans.json']: assert (p / name).read_bytes() == (old / name).read_bytes()
    before, after = json.loads((old / 'protocol.json').read_text()), json.loads((p / 'protocol.json').read_text())
    assert after['proposal'] == before['proposal'] and after['initial_task'] == before['initial_task']
    assert after['revision_task'] == MODE + '\n\n' + before['revision_task'].replace(REMOVE, '')
    configs = {}
    for mode in ['base', 'adapter']:
        current = json.loads((ROOT / f'configs/posttraining/qwen35-explicit-seed-{mode}-20261007-v1.json').read_text())
        parent = json.loads((ROOT / f'configs/posttraining/qwen35-sanctions-interaction-seed-{mode}-20261007-v1.json').read_text())
        assert {k: v for k, v in current.items() if k not in ['pack', 'kind']} == {k: v for k, v in parent.items() if k not in ['pack', 'kind']}
        assert current['max_steps'] == current['training_examples'] == 0 and current['eval_cases'] == 2
        configs[mode] = current
    assert configs['adapter']['adapter_sha256'] == sha256(ROOT / configs['adapter']['adapter'] / 'adapter_model.safetensors')
    tok = AutoTokenizer.from_pretrained(configs['base']['model_path'], local_files_only=True)
    cases, parents = list(read_jsonl(p / 'cases.jsonl')), list(read_jsonl(old / 'cases.jsonl'))
    for current, parent, link in zip(cases, parents, provenance['cases'], strict=True):
        assert current['id'] == link['id'] and parent['id'] == link['parent_id']
        assert current['condition'] == parent['condition'] == 'seed' and current['prompt'][0] == parent['prompt'][0]
        suffix = '\n\nREVISION TASK:\n' + before['revision_task']
        original = parent['prompt'][1]['content']; assert original.endswith(suffix)
        prefix = original[:-len(suffix)]
        assert hashlib.sha256(prefix.encode()).hexdigest() == link['unchanged_prefix_sha256']
        assert current['prompt'][1]['content'] == prefix + '\n\nREVISION TASK:\n' + after['revision_task']
        assert current['input_ids'] == tok.apply_chat_template(current['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(current['input_ids']) + 2048 <= 8192
    record = {'status': 'preparation_verified_not_model_quality', 'verified_at': datetime.now(timezone.utc).isoformat(),
              'pack': str(p.relative_to(ROOT)), 'manifest_sha256': sha256(p / 'manifest.json'),
              'parent_manifest_sha256': sha256(old / 'manifest.json'), 'planned_model_outputs': 4,
              'actual_model_outputs': 0, 'optimizer_steps': 0, 'cumulative_qwen35_steps': 3934,
              'actual_model_execution_started': False, 'native_input_lengths': [len(c['input_ids']) for c in cases],
              'sources_proposal_actual_seeds_rubric_and_model_settings_unchanged': True,
              'scope': 'CPU preparation only. Explicit-mode addition and peer-only clause removal are coupled. GPU availability must be rechecked; no automatic launch, independent review or performance claim.'}
    write_json(ROOT / 'reports/explicit-seed-preparation-20261007-v1.json', record)
    print(json.dumps(record, indent=2))


if __name__ == '__main__': main()
