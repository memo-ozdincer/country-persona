#!/usr/bin/env python3
"""Select a balanced 100-record content-review packet; leave all ratings unset."""
from collections import Counter
from pathlib import Path
import json
from country_persona.io import read_jsonl,write_json,write_jsonl,digest,sha256
ROOT=Path('data/prepared/expansion-20260913')
docs=list(read_jsonl(ROOT/'documents.jsonl'));qas=list(read_jsonl(ROOT/'authentic-qa.candidates.jsonl'))
selected=[]
def take(pool,n):
    eligible=sorted(pool,key=lambda r:digest(r['id']))
    if len(eligible)<n:raise ValueError('Insufficient review stratum')
    selected.extend(eligible[:n])
for src in ('mfa_zh','mfa_fr','mfa_es','mfa_ru'):take([r for r in qas if r['source_id']==src],10)
take([r for r in docs if r['source_id']=='china_mission_zh'],6)
take([r for r in docs if r['source_id']=='national_policy_documents' and r['country_iso3']=='CHN'],2)
take([r for r in docs if r['source_id']=='upr_national_reports' and r['country_iso3']=='CHN'],2)
# Include every German strategy language (and the two source-language summaries).
german_policy=[r for r in docs if r['source_id']=='national_policy_documents' and r['country_iso3']=='DEU']
selected.extend(german_policy)
take([r for r in docs if r['source_id']=='upr_national_reports' and r['country_iso3']=='DEU'],6)
take([r for r in docs if r['source_id']=='germany_aa'],50-len(german_policy)-6)
assert Counter(r['country_iso3'] for r in selected)=={'CHN':50,'DEU':50}
rows=[]
for r in selected:
    rows.append(dict(record=r,review=dict(reviewer=None,reviewed_at=None,source_text_correct=None,
        institution_and_speaker_correct=None,event_and_availability_correct=None,national_vs_coalition_correct=None,
        language_and_translation_scope_correct=None,answer_boundary_correct=None,policy_claims_supported=None,
        admit_for_use=None,notes='')))
write_jsonl(ROOT/'review-100.jsonl',rows)
write_json('reports/expansion-review-packet.json',dict(records=len(rows),by_country=dict(Counter(r['country_iso3'] for r in selected)),
    by_language=dict(Counter(r['language'] for r in selected)),by_source=dict(Counter(r['source_id'] for r in selected)),
    reviewed_records=0,method='deterministic SHA256 ordering within explicit country/source strata; all German policy-language variants included',
    path=str(ROOT/'review-100.jsonl')))
print('Prepared 100 unreviewed records, 50 per country')

report_path=Path('reports/expansion-20260913.json')
report=json.loads(report_path.read_text())
report['artifacts']={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in ROOT.glob('*.jsonl')}
write_json(report_path,report)
