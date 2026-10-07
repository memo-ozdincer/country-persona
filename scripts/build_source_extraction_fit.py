"""One audited documentary-extraction target, separate frozen Libya monitor,32updates proposed."""
import copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,digest,sha256

LIBYA_QUESTIONS='''1. What speaker/capacity/date, thanked report, welcome, Court purpose, legal values and attack/support are recorded?
2. What real continuing support types, requested budget, strategy date/report and appropriation limits are stated?
3. Which inquiries progress, which is nearing completion, and what future/conditional roadmap is expected?
4. What disaster affected cooperation/missions, which condolences/support and national proceedings/evidence relationships are described?
5. What document/technical/visa/assistance cooperation, joint missions, future office and ambassador-posting qualifications appear?
6. What victim/witness/community engagement and civil-society guidelines/seminar/exchanges are welcomed?
7. Which serious-crime scope and international/regional/civil-society/third-State/agency/UN support entities are included?
8. What national/regional stability and actual ongoing commitments remain?'''

def main():
    old=ROOT/'data/prepared/source-only-compact-probe-20261007-v1';dest=ROOT/'data/prepared/source-extraction-20261007-v1';assert not dest.exists()
    cases=[copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[0])]
    source=json.loads((old/'sources.json').read_text());criteria=json.loads((old/'criteria.json').read_text())
    held=ROOT/'data/prepared/compact-france-20261007-v1';s=json.loads((held/'sources.json').read_text())['libya']['FRA'];source['libya']={'FRA':s}
    criteria['source_units']['libya']=json.loads((held/'criteria.json').read_text())['source_units']['libya'];criteria['common_units']={}
    text='PUBLIC SOURCE METADATA: S/PV.9469,8 November 2023. Dime Labille speaks nationally for France; Zhang Jun chairs, Khan is Prosecutor; no vote label in selected span. Original French clarifies ambassador posting in Netherlands, not nationality. Attribute source claims to France.\n\nQUESTIONS ONLY, NO ANSWERS PROVIDED:\n'+LIBYA_QUESTIONS+'\n\nCOMPLETE NATIONAL STATEMENT:\n'+s['text']+'\n\nTASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve actors, dates, conditional versus established claims, actual ongoing support, requested-versus-approved budget and future-versus-open office. No slash-list/fused-word shortcut or invented commitment, amount, vote or guarantee.'
    cases.append({'id':'libya-fra-source-only-monitor','country_iso3':'FRA','family':'libya','condition':'separate_source_factual_extraction_monitor','prompt':[cases[0]['prompt'][0],{'role':'user','content':text}]})
    target=json.loads((ROOT/'data/prepared/actual-compact-planner-checked-20261007-v1/checked-plan.json').read_text())['plan'].split('\n\n')[0]
    assert len(target.split())==198 and all(x not in target for x in ['Analytical decisions','Hypothetical implementation'])
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-compression-20261006-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),max_steps=32,training_examples=1,eval_cases=2,
        kind='fresh_one_target_documentary_extraction_chosen_only',baseline_run='runs/aurora-source-extraction-base-20261007-v1',comparison_run='runs/aurora-actual-compact-checked-point8-20261007-v1',preparation='reports/source-extraction-preparation-20261007-v1.json')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids'in c:assert c['input_ids']==ids
        c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    dest.mkdir();write_jsonl(dest/'cases.jsonl',cases);write_json(dest/'sources.json',source);write_json(dest/'criteria.json',criteria)
    shutil.copy2(old/'presentation-criteria.json',dest/'presentation-criteria.json');write_json(dest/'preferred-targets.json',{'targets':{cases[0]['id']:target},'author':'same assistant;198word source-only block from checked original273word plan, all8 source meanings hand-read; no independent teacher'})
    write_json(dest/'provenance.json',{'scope':'One198word factual-extraction target proposed, freshzeroLoRA32updates. Same source-only fittinginput as exposed actual probe; separate Libya source/task outside this fit, already exposed elsewhere. Original8sourcecriteria unchanged, no full14unit/application/persona claim.','old_source_only_manifest_sha256':sha256(old/'manifest.json'),'libya_source_manifest_sha256':sha256(held/'manifest.json'),'target_source_only_block_sha256':digest(target),'task_max_words':210})
    shutil.copy2(__file__,dest/'builder-code.py');write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':1,'eval_cases':2,'source_scope':'Frozen1target/2case extraction draft; no fitting before inspected matching baseline/negative binding.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'read_scope':'NewUkraine selectedsource/page13,198word preferredblock and8questions/criteria fully read; same complete Libya speech/all8sourcecriteria and new factual-only questions/task read. No Q/Z supplied, target doesnot occur in studentinput. Same assistant, independentreview pending.','fitting_ready':False})
    write_json(ROOT/'configs/posttraining/qwen35-source-extraction-20261007-v1.json',cfg)
    base=copy.deepcopy(cfg);base.update(max_steps=0,training_examples=0);write_json(ROOT/'configs/posttraining/qwen35-source-extraction-base-20261007-v1.json',base)
    print(json.dumps({'source_target_words':len(target.split()),'cases':2,'updates_proposed':32,'fit_ready':False}))

if __name__=='__main__':main()
