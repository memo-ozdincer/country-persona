"""Replay source-card or card-to-memo traces and stored source judgments."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--bridge', action='store_true'); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--version', choices=['v1','v2'], default='v1')
    args = parser.parse_args(); name = 'country-source-bridge' if args.bridge else 'country-source-cards'
    pack = ROOT / ('data/prepared/' + name + '-20261006-' + args.version); manifest = json.loads((pack / 'manifest.json').read_text())
    for filename, expected in manifest['files_sha256'].items(): assert sha256(pack / filename) == expected
    case = list(read_jsonl(pack / 'cases.jsonl'))[0]; criteria = json.loads((pack / 'criteria.json').read_text())
    sources = json.loads((pack / 'wps-statements.json').read_text()); proof = json.loads((pack / 'source-proof.json').read_text())
    raw = ROOT / 'data/raw/source-application-grounding-20261003-v1'
    for filename, expected in proof['wps_raw_files_sha256'].items(): assert sha256(raw / filename) == expected
    document = (raw / 'record-8514.txt').read_text()
    for source in sources.values():
        assert document[source['start']:source['end']].strip() == source['text'] and digest(source['text']) == source['text_digest']
        assert source['text'] in case['prompt'][1]['content']
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(ROOT / manifest['adapter'], local_files_only=True)
    expected_units = {c + ':' + key for c in ('FRA','GBR') for key, _ in criteria['wps']['common'] + criteria['wps']['specific'][c]}
    summaries = {}; runs = {}; outputs = {}
    for arm in ('base','adapter'):
        directory = ROOT / ('runs/aurora-' + name + '-' + arm + '-20261006-' + args.version)
        run = json.loads((directory / 'run.json').read_text()); inspection = json.loads((directory / 'inspection.json').read_text())
        row = list(read_jsonl(directory / 'transcript.jsonl'))[0]; rating = inspection['reviews'][0]
        assert run['status'] == 'completed' and run['optimizer_steps'] == 0 and inspection['all_outputs_read_complete'] and inspection['all_reasoning_read_complete']
        assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert run['pack_manifest_sha256'] == sha256(pack / 'manifest.json') and inspection['criteria_sha256'] == sha256(pack / 'criteria.json')
        assert row['id'] == case['id'] == rating['id'] and rating['all_output_read_complete'] and row['protocol_status'] == 'public_answer' and not row['reasoning_ids']
        assert hashlib.sha256(row['output'].encode()).hexdigest() == rating['output_sha256']
        config = run['config']; assert config['chat_template_kwargs'] == {'enable_thinking':False} and config['generation_max_new_tokens'] == 2048
        ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
        assert ids == row['input_ids'] and len(ids)+2048 <= config['max_length'] and tokenizer.decode(row['public_ids'], skip_special_tokens=True) == row['output']
        assert set(rating['ratings']) == expected_units and set(rating['universal_checks']) == set(criteria['universal_checks']) and set(rating['synthesis_checks']) == set(criteria['synthesis_checks'])
        for source, expected in run['source_code_sha256'].items(): assert sha256(directory / Path(source).name) == expected
        if arm == 'adapter': assert run['loaded_adapter_sha256'] == manifest['adapter_sha256'] == sha256(ROOT / manifest['adapter'] / 'adapter_model.safetensors')
        values = [*rating['ratings'].values(),*rating['universal_checks'].values(),*rating['synthesis_checks'].values()]
        assert all(v['status'] in {'met','unmet','unratable'} and v['reason'].strip() for v in values)
        summaries[arm] = {'content_met':sum(v['status']=='met' for v in rating['ratings'].values()),'content_unratable':sum(v['status']=='unratable' for v in rating['ratings'].values()),
                          'content_units':24,'guards_met':sum(v['status']=='met' for v in rating['universal_checks'].values()),'synthesis_met':sum(v['status']=='met' for v in rating['synthesis_checks'].values()),
                          'source_criteria_pass':bool(row['output'].strip()) and not row['at_output_cap'] and not rating.get('additional_source_fidelity_observations') and all(v['status']=='met' for v in values),
                          'words':len(row['output'].split()),'tokens':row['generated_tokens'],'generation_seconds':row['generation_seconds'],'at_cap':row['at_output_cap']}
        runs[arm]=run; outputs[arm]=row
    assert outputs['base']['input_ids']==outputs['adapter']['input_ids']
    for key in ('versions','source_code_sha256'): assert runs['base'][key]==runs['adapter'][key]
    assert runs['base']['gpu']['name']==runs['adapter']['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
    if args.bridge:
        binding=manifest['selected_card_run']; original=ROOT/binding['path']
        assert sha256(original/'transcript.jsonl')==binding['transcript_sha256'] and sha256(original/'inspection.json')==binding['inspection_sha256']
        original_text=list(read_jsonl(original/'transcript.jsonl'))[0]['output']
        assert (pack/'original-model-card.txt').read_text()==original_text
        repaired=original_text
        for change in json.loads((pack/'repairs.json').read_text()):
            assert repaired.count(change['before'])==1
            repaired=repaired.replace(change['before'],change['after'])
        assert (pack/'selected-card.txt').read_text()==repaired and repaired in case['prompt'][1]['content']
    result={'status':'source_bytes_tokens_weights_and_stored_card_annotations_replayed','stage':name,'new_model_calls':2,'new_optimizer_steps':0,'summary':summaries,
            'cumulative_aurora_qwen35_steps':414,'reference_qwen25_steps':582,'scope':manifest['comparison_scope'],'independent_review_complete':False,'actual_input_output_tokens_replayed':True}
    write_json(args.output,result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
