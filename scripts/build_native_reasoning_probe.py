"""Freeze one unchanged failed policy task for a four-call native-mode comparison."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl


def main():
    from transformers import AutoTokenizer
    original = ROOT / 'data/prepared/synthesis-rehearsal-20261006-v1'
    out = ROOT / 'data/prepared/native-reasoning-20261006-v1'
    if out.exists(): raise ValueError('Fresh pack required')
    old_manifest = json.loads((original / 'manifest.json').read_text())
    for name, expected in old_manifest['files_sha256'].items(): assert sha256(original / name) == expected
    case = next(c for c in read_jsonl(original / 'cases.jsonl') if c['id'] == 'wps-raw')
    old_criteria = json.loads((original / 'criteria.json').read_text())
    criteria = {'wps': old_criteria['wps'], 'universal_checks': old_criteria['climate']['national_policy_rubrics']['FRA']['universal_checks'],
                'synthesis_checks': old_criteria['climate']['synthesis_checks'],
                'policy': 'Full public answer only. Reasoning is retained/read but is not policy output. No boundary means no public answer. Known contradictions fail even if a correct clause also appears. Word compliance separately reported; existing national units unchanged.'}
    config = json.loads((ROOT / 'configs/posttraining/qwen35-synthesis-rehearsal-20261006-v1.json').read_text())
    keep = ['model', 'revision', 'model_path', 'runtime_path', 'runtime_pins', 'seed', 'max_length']
    common = {k: config[k] for k in keep}
    adapter = ROOT / 'runs/aurora-synthesis-rehearsal-fit-20261006-v1/adapter'
    tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
    markers = {k: tokenizer.convert_tokens_to_ids(k) for k in ('<think>', '</think>')}
    assert all(tokenizer.encode(k, add_special_tokens=False) == [v] for k, v in markers.items())
    native = []
    for flag in (False, True):
        ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=flag)
        assert len(ids) + 2048 <= common['max_length']
        native.append({'enable_thinking': flag, 'input_tokens': len(ids), 'tail_ids': ids[-14:]})
    out.mkdir()
    write_jsonl(out / 'cases.jsonl', [case]); write_json(out / 'criteria.json', criteria)
    for name in ('wps-statements.json', 'source-proof.json'): (out / name).write_bytes((original / name).read_bytes())
    (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
    write_json(out / 'manifest.json', {'question': 'Does native thinking improve the exposed third-family composition/polarity failures beyond a matched larger nonthinking allowance, and does the learned adapter help?',
               'training_authorized_for_this_pack': False, 'optimizer_steps': 0, 'planned_model_answers': 4,
               'decision': 'Base/nonthinking, adapter/nonthinking, base/thinking, adapter/thinking; each one-answer run inspected before the next. One bounded factorial diagnostic, no fit or sweep.',
               'source_scope': 'Unchanged complete FRA/GBR post-vote WPS sources/question, same24units and guards. Outside selected adapter training, historically exposed development; not sealed OOD.',
               'comparison_scope': 'New2048total-generation-token protocol on both modes, including reasoning and boundary. Current512 nonthinking protocol remains intact; its results are historical context. Equal allowances do not equal actual compute.',
               'adapter': str(adapter.relative_to(ROOT)), 'adapter_sha256': sha256(adapter / 'adapter_model.safetensors'),
               'adapter_config_sha256': sha256(adapter / 'adapter_config.json'), 'adapter_branch_steps': 160,
               'selection_inspection_sha256': sha256(ROOT / 'runs/aurora-synthesis-rehearsal-fit-20261006-v1/inspection.json'),
               'thinking_marker_ids': markers, 'native_template_preflight': native,
               'files_sha256': {p.name: sha256(p) for p in out.iterdir() if p.is_file()}, 'independent_review_complete': False})
    write_json(out / 'manual-inspection.json', {'manifest_sha256': sha256(out / 'manifest.json'), 'all_selected_texts_read_complete': True,
               'reviewed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': 'same unblinded assistant; independent review pending',
               'texts_read': 'Full system/user question, both complete national post-vote speeches, all24national criteria,4source guards,5synthesis checks and existing failures. No new targets or teacher plans.',
               'source_claims_checked': 'France welcomes2467 but criticizes omitted care; full care/termination autonomy and reaffirmed1889/2106. UK welcomes, regrets services omission, recognizes civil society/further accountability, promises continuing worldwide access. Future-vote guarantees absent.',
               'independent_review_complete': False})
    for flag, label in ((False, 'off'), (True, 'on')):
        write_json(ROOT / ('configs/posttraining/qwen35-native-reasoning-' + label + '-20261006-v1.json'),
                   {**common, 'pack': str(out.relative_to(ROOT)), 'chat_template_kwargs': {'enable_thinking': flag},
                    'generation_max_new_tokens': 2048, 'kind': 'versioned_native_thinking_comparison_no_training',
                    'authorization': 'Recursive informative checkpoints; latest inspected decision selects small matched native thinking comparison.',
                    'adapter': str(adapter.relative_to(ROOT)), 'adapter_sha256': sha256(adapter / 'adapter_model.safetensors')})
    print(json.dumps({'pack': str(out), 'native_template_preflight': native, 'marker_ids': markers}))


if __name__ == '__main__': main()
