"""Audit the actual prepared release against immutable source and tokenizer bytes."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from transformers import AutoTokenizer
from country_persona.io import read_jsonl,sha256,write_json
from country_persona.posttraining import tokenize_example
from country_persona.train import validated_export
from country_persona.evaluate import check_case
root=Path('data/prepared/posttraining-qwen3-v1');release=json.loads((root/'release.json').read_text());lock=json.loads(Path('configs/posttraining/model.lock.json').read_text())
for f in lock['files']:assert sha256(f['path'])==f['sha256']
tok=AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True)
canonical={r['id']:r for r in read_jsonl('data/prepared/pilot/pilot.canonical.jsonl')};raw={};groups=defaultdict(set);checked_tokens={};n=0
for name,stats in release['outputs'].items():
    path=root/(name+'.jsonl');mp=path.with_suffix('.manifest.jsonl');split=name.rsplit('.',1)[-1]
    assert sha256(path)==stats['data_sha256'] and sha256(mp)==stats['manifest_sha256']
    rows,meta=validated_export(path,mp,split,True);total=supervised=0
    for row,m in zip(rows,meta):
        source=canonical[m['id']];assert row['completion'][0]['content']==source['text'];assert m['split_group']==source['split_group'] and m['split']==source['split']
        if source['raw_file'] not in raw:raw[source['raw_file']]=sha256(source['raw_file'])
        assert raw[source['raw_file']]==m['raw_sha256']
        if m['id'] not in checked_tokens:checked_tokens[m['id']]=tokenize_example(tok,row)
        length,target=checked_tokens[m['id']];assert length==m['sequence_tokens'] and target==m['supervised_tokens'] and length<=8192
        groups[m['split_group']].add(split);total+=length;supervised+=target;n+=1
    assert total==stats['sequence_tokens'] and supervised==stats['supervised_tokens']
assert all(len(s)==1 for s in groups.values())
evalroot=Path('data/prepared/eval-qwen3-v1');cases=list(read_jsonl(evalroot/'cases.jsonl'));smoke=list(read_jsonl(evalroot/'smoke_cases.jsonl'))
for case in cases:
    check_case(case)
    assert len(tok.apply_chat_template(case['prompt'],tokenize=True,add_generation_prompt=True,**lock['chat_template_kwargs']))+256<=8192
assert {c['id'] for c in smoke}<={c['id'] for c in cases}
counts=Counter((c['suite'],c['country'],c['condition']) for c in cases)
write_json('reports/posttraining_validation.json',{'status':'pass','model':lock['model'],'revision':lock['revision'],'chat_template_kwargs':lock['chat_template_kwargs'],'export_rows_checked_including_comparators':n,
    'unique_examples_tokenized':len(checked_tokens),'raw_source_files_verified':len(raw),
    'split_groups':len(groups),'eval_cases':len(cases),'first_inspection_cases':len(smoke),
    'eval_breakdown':{'/'.join(k):v for k,v in counts.items()},'checks':['source answer equality','source byte hashes','export hashes','real tokenizer lengths and completion boundaries','event split isolation','evaluation hashes and context budgets']})
print('Post-training release and evaluation audit passed')
