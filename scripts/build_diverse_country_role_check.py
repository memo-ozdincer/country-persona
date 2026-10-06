"""Freeze a no-fit speaker/chair metadata diagnostic on unchanged UK Somalia tasks."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    old = ROOT / 'data/prepared/diverse-country-fit-20261006-v2'
    dest = ROOT / 'data/prepared/diverse-country-role-check-20261006-v1'
    assert not dest.exists()
    manifest = json.loads((old / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        assert sha256(old / name) == expected
    raw = ROOT / 'data/raw/diverse-country-somalia-grounding-20261006-v1'
    record = (raw / 'record-9490.txt').read_text()
    chair = record[record.index('President:'):record.index('Members:')]
    assert 'Mr. De la Gasca López Domínguez' in chair and '(Ecuador)' in chair
    assert 'Mr. Kariuki (United Kingdom):' in record
    metadata = ('PRIMARY RECORD ROLE METADATA — S/PV.9490, 1 December 2023:\n'
        'National speaker: Mr. Kariuki, representative of the United Kingdom, speaking before the vote.\n'
        'Presiding Council chair: Mr. De la Gasca López Domínguez, Ecuador.\n'
        'The quoted greeting addressed to "Mr. President" addresses that Council chair, not the national speaker.\n')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-diverse-country-base-20261006-v2.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases, links = [], []
    for oldcase in read_jsonl(old / 'cases.jsonl'):
        if oldcase['id'] not in ['somalia-gbr-raw','somalia-gbr-plan']:
            continue
        case = copy.deepcopy(oldcase); marker = 'COMPLETE NATIONAL STATEMENT — GBR'
        assert case['prompt'][1]['content'].count(marker) == 1
        case['prompt'][1]['content'] = case['prompt'][1]['content'].replace(marker, metadata + '\n' + marker, 1)
        case['condition'] = 'primary_role_metadata_' + oldcase['condition']
        ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        case.update(input_ids=ids, input_ids_digest=digest(ids)); assert len(ids)+2048 <= 8192
        cases.append(case); links.append({'id':case['id'],'old_prompt_digest':digest(oldcase['prompt']),
            'new_prompt_digest':digest(case['prompt']), 'old_input_tokens':len(oldcase['input_ids']), 'new_input_tokens':len(ids)})
    assert len(cases) == 2
    dest.mkdir(parents=True); write_jsonl(dest / 'cases.jsonl',cases)
    for name in ['criteria.json','sources.json']:
        shutil.copy2(old / name,dest / name)
    write_json(dest / 'role-proof.json',{'original_pack':str(old.relative_to(ROOT)), 'original_cases_sha256':sha256(old/'cases.jsonl'),
        'original_criteria_sha256':sha256(old/'criteria.json'),'primary_record':str((raw/'record-9490.txt').relative_to(ROOT)),
        'primary_record_sha256':sha256(raw/'record-9490.txt'),'primary_chair_span':chair,'metadata_added':metadata,'changes':links,
        'comparison_runs':{'base':'runs/aurora-diverse-country-base-20261006-v2','fit':'runs/aurora-diverse-country-fit-20261006-v2'},
        'scope':'Only source-checked speaker/chair metadata added; source text, scenario, task, criterion and checked plan unchanged. Input facts/length change, no training effect claim. Same exposed Somalia development.'})
    shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),
        'files_sha256':{f.name:sha256(f) for f in dest.iterdir() if f.is_file()},'training_authorized_for_this_pack':False,
        'training_examples':0,'eval_cases':2,'source_scope':'Primary-role metadata diagnostic, no fit; base/new256 matching new inputs and old UK cases.'})
    for arm in ['base','adapter']:
        acfg=copy.deepcopy(cfg); acfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=2,training_examples=0,max_steps=0,kind='primary_role_metadata_diagnostic')
        if arm=='adapter':
            adapter=ROOT/'runs/aurora-diverse-country-fit-20261006-v2/adapter'
            acfg.update(adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'))
        write_json(ROOT/f'configs/posttraining/qwen35-diverse-country-role-{arm}-20261006-v1.json',acfg)
    print(json.dumps({'metadata_added':metadata,'changes':links,'calls_planned':4,'optimizer_steps':0},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
