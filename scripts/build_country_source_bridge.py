"""Audit an explicitly edited model card, then test the original memo task on it."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,digest,sha256,write_json,write_jsonl

def main():
    from transformers import AutoTokenizer
    pack=ROOT/'data/prepared/country-source-cards-20261006-v2';out=ROOT/'data/prepared/country-source-bridge-20261006-v1'
    if out.exists():raise ValueError('Fresh bridge required')
    selected=ROOT/'runs/aurora-country-source-cards-adapter-20261006-v2';review=json.loads((selected/'inspection.json').read_text());assert review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(selected/'transcript.jsonl')
    original=list(read_jsonl(selected/'transcript.jsonl'))[0]['output'];text=original;repairs=[]
    def replace(before,after,reason):
        nonlocal text
        assert text.count(before)==1,before
        text=text.replace(before,after);repairs.append({'before':before,'after':after,'reason':reason})
    replace('That support does not accept the acute need for comprehensive reproductive and sexual health care that was removed.', 'That support does not endorse the omission of health-service language; the UK expresses the acute need for comprehensive reproductive and sexual health care.', 'Restore correct operator/object: criticism of omission, positive care need.')
    replace('Recognition of the survivor-centred approach is conditional on further steps for justice and accountability.', 'The UK recognizes the survivor-centred approach as an achievement while saying further steps are needed for true justice and accountability.', 'Remove invented condition on recognizing the existing approach.')
    replace('Both require further justice/accountability steps.', 'The UK explicitly says further steps are needed for true justice and accountability; this specific assessment is not stated in the bounded French speech.', 'Keep UK-specific source assessment named.')
    replace('Adoption protects some health references;', 'France says the earlier WPS framework is reaffirmed;', 'Use documented reaffirmed framework rather than stronger ambiguous protection claim.')
    replace('A specific future Council text preserving this care despite a hypothetical conviction finding is not stated.', 'A specific future Council text or guaranteed future vote is not established by this speech; the actual ongoing care/promotion commitment remains stated.', 'Separate genuine continuing commitment from unspecified future voting.')
    replace('A specific future Council text adding a non-delaying, conviction-independent safeguard is not stated.', 'A specific future Council text or guaranteed future vote is not established by this speech; the actual worldwide continuing-care support remains stated.', 'Same distinction for UK; do not narrow unknown to one hypothetical text.')
    replace("Recommend preserving comprehensive sexual and reproductive health care and the right to decide about termination alongside accountability proceedings, with care continuing and not delayed by a conviction gate.", "Analytical recommendation: provide comprehensive care and pregnancy-choice support without waiting for a conviction; arrange consent-based referrals and accountability work in parallel, without making survivor care conditional on evidence or case outcomes. This is a proposed operational step, not a new French pledge or vote condition.", 'Make feasible care/access-versus-accountability step explicit; no universal delay.')
    replace('Recommend preserving comprehensive sexual and reproductive health care alongside accountability proceedings, with care continuing and not delayed by a conviction gate.', 'Analytical recommendation: provide comprehensive survivor care now and coordinate consent-based referrals and accountability work in parallel; case outcomes must not gate care. This is a proposed operational step, not a new UK pledge or vote condition.', 'Concrete parallel-care/accountability step, source pledge kept separate.')
    sources=json.loads((pack/'wps-statements.json').read_text())
    quotes={'FRA':'We will continue to support and promote that approach in the Security Council, in other United Nations bodies and elsewhere.', 'GBR':'I assure you that the United Kingdom will continue to support access to sexual and reproductive health care for survivors of sexual violence around the world — that is a priority.'}
    for iso,q in quotes.items():assert q in sources[iso]['text']
    replace('France will continue to support and promote full access to sexual and reproductive health care and rights in the Security Council, other UN bodies and elsewhere.', 'France will continue to support and promote full access to sexual and reproductive health care and rights in the Security Council, other UN bodies and elsewhere. Exact source quote: "'+quotes['FRA']+'"', 'Add requested actual exact national quote.')
    replace('The UK will continue to support access to sexual and reproductive health care for survivors of sexual violence around the world; that is a priority.', 'The UK will continue to support access to sexual and reproductive health care for survivors of sexual violence around the world; that is a priority. Exact source quote: "'+quotes['GBR']+'"', 'Add requested actual exact national quote.')
    original_case=list(read_jsonl(ROOT/'data/prepared/native-reasoning-20261006-v1/cases.jsonl'))[0]
    case={**original_case,'id':'country-source-bridge','scenario':'original_memo_plus_audited_corrected_card'}
    case['prompt']=[original_case['prompt'][0],{'role':'user','content':original_case['prompt'][1]['content']+'\n\nSOURCE-AUDITED CARD DATA (assistant-edited development aid, not new government commitments):\n'+text}]
    out.mkdir();write_jsonl(out/'cases.jsonl',[case]);(out/'selected-card.txt').write_text(text);(out/'original-model-card.txt').write_text(original)
    write_json(out/'repairs.json',repairs)
    for name in ['criteria.json','wps-statements.json','source-proof.json']:(out/name).write_bytes((pack/name).read_bytes())
    (out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
    manifest=json.loads((pack/'manifest.json').read_text());manifest.update(question='Can the original joint memo preserve a source-audited edited card, comparing base and saved adapter?',
        planned_model_answers=2,decision='Both original cards inspected; edited card fully source/criterion audited before inference. One base bridge memo, inspect, then matching saved adapter. No training/sweep.',
        comparison_scope='Given corrected data, stronger explicit coverage, longer input. Not a validated autonomous planner, isolated format effect, native prediction or persona gain. Original300word memo task/source/24units intact.',
        selected_card_run={'path':str(selected.relative_to(ROOT)),'transcript_sha256':sha256(selected/'transcript.jsonl'),'inspection_sha256':sha256(selected/'inspection.json')},
        card_provenance='Actual saved-adapter card plus10explicit assistant edits, hand-audited against complete sources; not independent teacher API transcript.',
        files_sha256={p.name:sha256(p) for p in out.iterdir() if p.is_file()})
    write_json(out/'manifest.json',manifest)
    config=json.loads((ROOT/'configs/posttraining/qwen35-country-source-cards-20261006-v2.json').read_text());config.update(pack=str(out.relative_to(ROOT)),kind='audited_card_to_original_memo_no_training')
    tok=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True);ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs']);assert len(ids)+2048<=config['max_length']
    write_json(ROOT/'configs/posttraining/qwen35-country-source-bridge-20261006-v1.json',config)
    write_json(out/'preflight.json',{'input_tokens':len(ids),'total_allowance':len(ids)+2048,'no_truncation':True,'original_source_task_before_card':True,'new_optimizer_steps':0})
    manifest['files_sha256']={p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'}
    write_json(out/'manifest.json',manifest)
    print({'card_edits':len(repairs),'input_tokens':len(ids),'word_count':len(text.split())})

if __name__=='__main__':main()
