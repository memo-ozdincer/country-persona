"""Freeze complete UK UNITAMS source outside the three-source reader fit; no optimization."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest


def main():
    dest=ROOT/'data/prepared/uk-source-transfer-20261007-v1';assert not dest.exists()
    raw=ROOT/'data/raw/two-context-sudan-grounding-20261006-v1';s=json.loads((raw/'statements.json').read_text())['GBR'];record=(raw/'record-9492.txt').read_text()
    download=json.loads((raw/'download.json').read_text());assert sha256(raw/'record-9492.pdf')==download['sha256']
    assert record[s['start']:s['end']].strip()==s['text'] and s['text'].startswith('Mr. Kariuki (United Kingdom):')
    assert record[s['end']:].startswith('Mr. Agyeman (Ghana):')
    old=ROOT/'data/prepared/two-context-country-fit-20261006-v1';crit=json.loads((old/'criteria.json').read_text())
    sourcecrit=crit['source_units']['sudan']['GBR'];assert len(sourcecrit)==8
    system=list(read_jsonl(ROOT/'data/prepared/india-actual-extraction-20261007-v1/cases.jsonl'))[0]['prompt'][0]
    body='''PUBLIC SOURCE METADATA: S/PV.9492, 1 December 2023. Kariuki speaks nationally for the United Kingdom after voting; Ecuador chairs. The complete bounded national source below excludes the chair and following Ghana statement. Welcoming a resolution is not a supplied national vote label. Attribute source positions and reports to the UK, not independent findings.

QUESTIONS ONLY, NO ANSWERS PROVIDED:
1. What resolution response, closure preference and assessment of the Mission's work are recorded?
2. Whose demand prompted which penholder role, compromise and transition arrangements?
3. Who bears safety and security responsibility, for what; what cooperation, withdrawal, task-transfer and visa duties are sought?
4. What political-transition consequences, suffering, atrocities and reported violence are described?
5. What conflict-resolution stance, talks and political outcomes are sought?
6. What support need remains despite mission closure?
7. Which appointment is welcomed, in which capacity, and who should engage?
8. What actual continuing national cooperation, partners and goals remain; what new condition or future vote is stated?

COMPLETE NATIONAL STATEMENT:
'''+s['text']+'''

TASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve recorded actors, dates, conditional versus established claims, scope and actual ongoing commitments or hopes. Attribute assertions to the UK, not independent findings. No slash-list or fused-word shortcut, no invented amount, vote, deadline or support condition, no source repetition.'''
    prompt=[system,{'role':'user','content':body}]
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-india-actual-extraction-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),kind='UK_UNITAMS_source_transfer_outside_reader_fit')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
    c={'id':'uk-unitams-complete-source-transfer','family':'sudan','country_iso3':'GBR','condition':'outside_three_source_reader_fit_historically_exposed','prompt':prompt,'input_ids':ids,'input_ids_digest':digest(ids)}
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[c]);write_json(dest/'sources.json',{'sudan':{'GBR':s}})
    write_json(dest/'criteria.json',{'source_units':{'sudan':{'GBR':sourcecrit}},'common_units':{},'universal_checks':crit['universal_checks'],'policy':'Existing eightUK UNITAMS source compounds/fourguards unchanged; full305wordprimary, source-only210word/one-section extraction. Differentcountry/topic fromreaderfit, historicalexposure/unknownpretraining, notsealed/strongOOD.'})
    shutil.copy2(ROOT/'data/prepared/india-actual-extraction-20261007-v1/presentation-criteria.json',dest/'presentation-criteria.json')
    write_json(dest/'provenance.json',{'source_download_sha256':sha256(raw/'download.json'),'raw_statement_sha256':sha256(raw/'statements.json'),'primary_pdf_sha256':sha256(raw/'record-9492.pdf'),'original_eight_source_criteria_sha256':sha256(old/'criteria.json'),'previous_checkpoint_sha256':sha256(ROOT/'reports/three-source-extraction-checkpoint-20261007-v1.json'),
               'scope':'Baseversus saved3source96 reader, completeUK nationalstatement outside readerfit. Source previously used inotherdevelopment/writertraining. No teacherfacts/targets, no optimization. Inspectall beforedownstream ordataexpansion.'})
    shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'Frozen outside-reader-fitting UK UNITAMS source8/210word control; sameassistantsource audit/grader, no broadcountry/persona/multiagent claim.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Entire305wordprimarysource/roles/boundaries, eightquestions/sourcecriteria/guards and210wordcontract fullyhandread beforecalls. No preferredtarget or teacherfacts. Independentreview pending.'})
    write_json(ROOT/'configs/posttraining/qwen35-uk-source-transfer-base-20261007-v1.json',cfg)
    a=ROOT/'runs/aurora-three-source-extraction-fit-20261007-v1/adapter';cfg.update(adapter=str(a.relative_to(ROOT)),adapter_sha256=sha256(a/'adapter_model.safetensors'),adapter_config_sha256=sha256(a/'adapter_config.json'))
    write_json(ROOT/'configs/posttraining/qwen35-uk-source-transfer-source96-20261007-v1.json',cfg)
    print(json.dumps({'source_words':len(s['text'].split()),'input_tokens':len(ids),'criteria_unchanged':True,'new_steps':0}))


if __name__=='__main__':main()
