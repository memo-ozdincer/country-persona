"""One inspected instruction-boundary repair; source/semantic criteria unchanged."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json,write_jsonl

REPAIR='''Source-boundary checks before returning the cards:
- National role means speaking for the named country as shown in this record. Do not infer a ministerial/permanent-representative office from memory or from a name; if an office is not specified by this bounded speech, say so.
- A not-stated claim must agree with the entire national speech and the other fields in that same card. Do not put a detail in both supported and absent categories.
- Procedural adoption of a text is distinct from policy endorsement of its omission. Assess the colleague's exact claimed endorsement; do not replace it with a different procedural claim.
- The last common-ground lines require support in each national speech. Country-specific facts stay named, rather than becoming a claim about both countries.
- Give an operational analytical next step that preserves access while accountability proceeds, with no delay concealed behind a care pledge. Keep existing source framework separate from an invented binding legal obligation; distinguish a recommended new mechanism from an observed government commitment.'''

def main():
    from transformers import AutoTokenizer
    original=ROOT/'data/prepared/country-source-cards-20261006-v1';out=ROOT/'data/prepared/country-source-cards-20261006-v2'
    if out.exists():raise ValueError('Fresh pack required')
    inspected=ROOT/'runs/aurora-country-source-cards-adapter-20261006-v1';review=json.loads((inspected/'inspection.json').read_text());assert review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(inspected/'transcript.jsonl')
    case=list(read_jsonl(original/'cases.jsonl'))[0];case['prompt'][1]['content']+='\n\n'+REPAIR
    out.mkdir();write_jsonl(out/'cases.jsonl',[case])
    for name in ['criteria.json','wps-statements.json','source-proof.json']:(out/name).write_bytes((original/name).read_bytes())
    (out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
    config=json.loads((ROOT/'configs/posttraining/qwen35-country-source-cards-20261006-v1.json').read_text());tok=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True)
    ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs']);assert len(ids)+2048<=config['max_length']
    manifest=json.loads((original/'manifest.json').read_text());manifest.update(question='Do explicit source-role/absence/collective-scope checks repair the observed source cards without new facts or fitting?',
        decision='One repaired base card, inspect, then matching saved adapter. Inspect both before synthesis or selecting supervision; no fit/sweep.',comparison_scope='Adds explicit checks after exposed v1 failures. Same sources/24semantic units/budget/weights/decoder; not fresh confirmation or isolated schema effect.',
        selection_inspection_sha256=sha256(inspected/'inspection.json'),preflight_input_tokens=len(ids),files_sha256={p.name:sha256(p) for p in out.iterdir() if p.is_file()})
    write_json(out/'manifest.json',manifest)
    i=json.loads((original/'manual-inspection.json').read_text());i.update(manifest_sha256=sha256(out/'manifest.json'),reviewed_at=datetime.now(timezone.utc).isoformat(),repair_read='Entire added five-check instruction read; no new national facts supplied, no source/semantic criterion edit. Role/absence/coda and operational-proposal checks selected from inspected outputs.')
    write_json(out/'manual-inspection.json',i);config.update(pack=str(out.relative_to(ROOT)),kind='source_card_boundary_repair_no_training');write_json(ROOT/'configs/posttraining/qwen35-country-source-cards-20261006-v2.json',config)
    print({'input_tokens':len(ids),'source_criteria_unchanged':True})
if __name__=='__main__':main()
