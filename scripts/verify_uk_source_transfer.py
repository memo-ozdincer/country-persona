"""Replay UK source/application development records; checks do not independently judge meaning."""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json
from verify_two_context_country import exited

NAMES = ['aurora-uk-source-transfer-base-20261007-v1',
         'aurora-uk-source-transfer-source96-20261007-v1',
         'aurora-uk-referent-base-20261007-v1',
         'aurora-uk-referent-source96-20261007-v1',
         'aurora-uk-quote-backed-base-20261007-v1',
         'aurora-uk-quote-backed-source96-20261007-v1',
         'aurora-uk-raw-application-base-20261007-v2',
         'aurora-uk-raw-application-adapter-20261007-v2',
         'aurora-uk-raw-writer-base-20261007-v1',
         'aurora-uk-raw-writer-point8-20261007-v1']


def main():
    from transformers import AutoTokenizer
    config = json.loads((ROOT / 'configs/posttraining/qwen35-uk-source-transfer-base-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
    summaries, resources, inputs = {}, [], []
    raw = ROOT / 'data/raw/two-context-sudan-grounding-20261006-v1'
    download = json.loads((raw / 'download.json').read_text())
    assert sha256(raw / 'record-9492.pdf') == download['sha256']
    source = json.loads((raw / 'statements.json').read_text())['GBR']
    record = (raw / 'record-9492.txt').read_text()
    assert record[source['start']:source['end']].strip() == source['text']
    assert record[source['end']:].startswith('Mr. Agyeman (Ghana):')
    for name in NAMES:
        d = ROOT / 'runs' / name
        r = json.loads((d / 'run.json').read_text())
        i = json.loads((d / 'inspection.json').read_text())
        p = ROOT / r['config']['pack']
        manifest = json.loads((p / 'manifest.json').read_text())
        hand = json.loads((p / 'manual-inspection.json').read_text())
        assert r['status'] == 'completed' and exited(r['identity']) and r['optimizer_steps'] == 0
        assert i['all_outputs_read_complete'] and not i['independent_review_complete']
        assert r['pack_manifest_sha256'] == hand['manifest_sha256'] == sha256(p / 'manifest.json')
        assert hand['all_selected_texts_read_complete'] and not manifest['training_authorized_for_this_pack']
        assert manifest['created_at'] < r['created_at']
        for f, h in manifest['files_sha256'].items():
            assert sha256(p / f) == h
        for f, h in r['source_code_sha256'].items():
            assert sha256(d / Path(f).name) == h
        assert r['versions'] == config['runtime_pins']
        assert r['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for k in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert r['config'][k] == config[k]
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        assert i['criteria_sha256'] == sha256(p / 'criteria.json')
        assert i['manual_annotations_sha256'] == sha256(d / 'manual-annotations.json')
        c, row, v = list(read_jsonl(p / 'cases.jsonl'))[0], list(read_jsonl(d / 'transcript.jsonl'))[0], i['reviews'][0]
        assert r['outputs'] == 1 and c['id'] == row['id'] == v['id']
        assert c['input_ids'] == row['input_ids'] == tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
        assert v['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest()
        assert v['words'] == len(row['output'].split())
        assert v['content_counts'] == dict(Counter(x['status'] for x in v['ratings'].values()))
        assert not row['at_output_cap']
        assert v.get('at_output_cap') is False
        checks = list(v['ratings'].values()) + list(v['universal_checks'].values())
        all_met = all(x['status'] == 'met' for x in checks)
        if 'source_only_task_pass' in v:
            assert v['source_only_task_pass'] == (all_met and v['words'] <= 210 and v['ordinary_word_separation'] and v['one_documentary_section'])
        elif 'component_pass' in v:
            assert v['component_pass'] == (all_met and all(v['presentation'].values()))
        elif 'usable_realization_pass' in v:
            assert v['usable_realization_pass'] == (all_met and all(v['presentation'].values()))
            assert v['presentation']['within300ordinary_words'] == (v['words'] <= 300 and v['presentation']['ordinary_word_separation'])
        else:
            assert v['evidence_clause'] in source['text'] and v['exact_source_substring_verified']
            assert v['content_pass'] == all_met
            assert v['diagnostic_pass'] == (all_met and v['words'] <= 60 and v['requested_two_labels'])
        if (d / 'quote-audit.json').exists():
            audit = json.loads((d / 'quote-audit.json').read_text())
            assert audit['all_output_hand_read_complete'] and audit['output_sha256'] == v['output_sha256']
            for fragment in audit['candidate_literal_fragments']:
                assert fragment['exact_source_substring'] == (fragment['longest_exact_token_fragment'] in source['text'])
        prev = r['previous_inspected_run']
        assert prev['inspection_sha256'] == sha256(ROOT / prev['run'] / 'inspection.json')
        if r['mode'] == 'adapter':
            assert r['loaded_adapter_sha256'] == sha256(ROOT / r['config']['adapter'] / 'adapter_model.safetensors')
        inputs.append(c['input_ids'])
        criteria = json.loads((p / 'criteria.json').read_text())
        assert set(v['ratings']) == set(criteria['source_units']['sudan']['GBR']) | set(criteria['common_units'])
        assert set(v['universal_checks']) == set(criteria['universal_checks'])
        summaries[name] = {'content': v['content_counts'], 'words': v['words'], 'source_pass': v.get('source_only_task_pass'), 'content_pass': v.get('content_pass'), 'diagnostic_pass': v.get('diagnostic_pass'), 'application_pass': v.get('component_pass'), 'writer_pass': v.get('usable_realization_pass')}
        resources.append({'run': str(d.relative_to(ROOT)), 'identity': r['identity'], 'gpu': r['gpu'], 'exited': True})
    for j in range(0, len(inputs), 2):
        assert inputs[j] == inputs[j + 1]
    for pack_name in ['uk-source-transfer-20261007-v1', 'uk-quote-backed-summary-20261007-v1']:
        p = ROOT / 'data/prepared' / pack_name
        criteria = json.loads((p / 'criteria.json').read_text())
        old = json.loads((ROOT / 'data/prepared/two-context-country-fit-20261006-v1/criteria.json').read_text())
        assert criteria['source_units']['sudan']['GBR'] == old['source_units']['sudan']['GBR']
        case = list(read_jsonl(p / 'cases.jsonl'))[0]
        assert case['prompt'][1]['content'].count(source['text']) == 1
    p = ROOT / 'data/prepared/uk-raw-application-20261007-v2'
    provenance = json.loads((p / 'provenance.json').read_text())
    d = ROOT / provenance['source_run']
    assert provenance['source_inspection_sha256'] == sha256(d / 'inspection.json')
    assert provenance['source_transcript_sha256'] == sha256(d / 'transcript.jsonl')
    facts = list(read_jsonl(d / 'transcript.jsonl'))[0]['output']
    assert list(read_jsonl(p / 'cases.jsonl'))[0]['prompt'][1]['content'].count(facts) == 1
    assert json.loads((p / 'actual-source-points.json').read_text())['facts'] == facts
    p = ROOT / 'data/prepared/uk-raw-writer-20261007-v1'
    plan = json.loads((p / 'actual-plan.json').read_text())
    parts = []
    for component in plan['components']:
        d = ROOT / component['run']
        assert component['inspection_sha256'] == sha256(d / 'inspection.json')
        assert component['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        row = next(x for x in read_jsonl(d / 'transcript.jsonl') if x['id'] == component['id'])
        parts.append(row['output'])
    assert plan['plan'] == '\n\n'.join(parts) and len(plan['plan'].split()) == plan['words'] == 291
    assert not plan['application_intermediate_pass']
    assert list(read_jsonl(p / 'cases.jsonl'))[0]['prompt'][1]['content'].count(plan['plan']) == 1
    failure = ROOT / 'runs/aurora-uk-raw-application-base-20261007-v1'
    failed = json.loads((failure / 'failure.json').read_text())
    assert failed['optimizer_steps'] == failed['model_outputs'] == 0
    assert failed['failure_log_sha256'] == sha256(failure / 'failure.log')
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': len(NAMES), 'uncapped': len(NAMES), 'capped': 0, 'new_optimizer_steps': 0, 'cumulative_qwen35_steps': 3198, 'reference_qwen25_steps': 582, 'all_owned_gpu_identities_exited': True, 'resources': resources, 'summaries': summaries, 'matched_weight_arm_inputs': True, 'primary_source_and_old_source8_criteria_verified': True, 'actual_source_facts_unedited': True, 'independent_review_complete': False, 'failed_model_outputs': 0, 'failed_optimizer_steps': 0, 'scope': 'Same-assistant adaptive UK development outside reader/application fitting sources, historically exposed elsewhere. Original eight-unit failures retained; focused diagnostic and quote-contract review separate. No independent quality, sealed OOD, persona, native prediction or multi-agent gain.'}
    write_json(ROOT / 'reports/uk-source-transfer-checkpoint-20261007-v1.json', receipt)
    print(json.dumps({k: receipt[k] for k in ['status', 'new_model_outputs', 'new_optimizer_steps', 'summaries']}, indent=2))


if __name__ == '__main__':
    main()
