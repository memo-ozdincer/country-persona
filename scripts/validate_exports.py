"""Check row alignment and hashes in every prepared candidate export."""
from pathlib import Path
from country_persona.io import read_jsonl,digest,write_json

counts={};errors=[]
for variant in ('pilot','long-context'):
    root=Path('data/prepared')/variant/'candidates';n=0;files=0
    for data in sorted(root.rglob('*.sft.jsonl')):
        manifest=data.with_name(data.name.replace('.sft.jsonl','.manifest.jsonl'))
        rows=list(read_jsonl(data));meta=list(read_jsonl(manifest));files+=1
        if len(rows)!=len(meta):errors.append(str(data)+': length mismatch');continue
        for i,(row,m) in enumerate(zip(rows,meta)):
            if m['row_index']!=i or m['example_sha256']!=digest(row):errors.append(str(data)+f': row {i} mismatch')
        n+=len(rows)
    if not files or not n:errors.append(str(root)+': missing or empty candidate exports')
    counts[variant]={'files':files,'examples':n}
write_json('reports/export_validation.json',{'variants':counts,'errors':errors})
print(counts,'errors',len(errors))
if errors:raise SystemExit(1)
