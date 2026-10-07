"""Bind two audited supervision repairs to inspected actual base negatives."""
import json,shutil,sys,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

def main():
    draft=ROOT/'data/prepared/source-status-20261007-v1';curated=ROOT/'data/prepared/source-status-targets-20261007-v2';dest=ROOT/'data/prepared/source-status-fit-20261007-v2';assert not dest.exists()
    m=json.loads((draft/'manifest.json').read_text());h=json.loads((draft/'manual-inspection.json').read_text());assert not m['training_authorized_for_this_pack'] and h['all_selected_texts_read_complete'] and h['manifest_sha256']==sha256(draft/'manifest.json')
    for f,x in m['files_sha256'].items():assert sha256(draft/f)==x
    ta=json.loads((curated/'manual-target-audit.json').read_text());assert ta['all_targets_hand_read_complete'] and ta['new_preferred_targets_sha256']==sha256(curated/'preferred-targets.json')
    cfgpath=ROOT/'configs/posttraining/qwen35-source-status-fit-20261007-v2.json';cfg=json.loads(cfgpath.read_text());base=ROOT/cfg['baseline_run'];run=json.loads((base/'run.json').read_text());review=json.loads((base/'inspection.json').read_text())
    assert run['status']=='completed' and run['mode']=='base' and run['optimizer_steps']==0 and review['all_outputs_read_complete'] and review['criteria_sha256']==sha256(draft/'criteria.json')
    assert run['transcript_sha256']==review['transcript_sha256']==sha256(base/'transcript.jsonl')
    cases=list(read_jsonl(draft/'cases.jsonl'));rows=list(read_jsonl(base/'transcript.jsonl'));t=json.loads((curated/'preferred-targets.json').read_text());assert len(cases)==len(rows)==4 and t['words']==[207,210]
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);sources=json.loads((draft/'sources.json').read_text());pairs=[];audits=[];links=[]
    for c,row in zip(cases[:2],rows[:2],strict=True):
        assert c['id']==row['id'] and c['input_ids']==row['input_ids']
        chosen=t['targets'][c['id']]
        for quote in re.findall(r'"([^"]+)"',chosen):assert quote in sources[c['family']]['FRA']['text']
        pair={'prompt':c['prompt'],'chosen':[{'role':'assistant','content':chosen}],'rejected':[{'role':'assistant','content':row['output']}],'chat_template_kwargs':{'enable_thinking':False}}
        prefix=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert prefix==c['input_ids'];audit={'id':c['id'],'prompt_ids':prefix,'pair_sha256':digest(pair)}
        for k in ['chosen','rejected']:
            ids=tok.apply_chat_template(c['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False);assert ids[:len(prefix)]==prefix and len(ids)<=8192;audit[k+'_ids']=ids[len(prefix):]
        pairs.append(pair);audits.append(audit);links.append({'id':c['id'],'run':str(base.relative_to(ROOT)),'identity':run['identity'],'transcript_sha256':sha256(base/'transcript.jsonl'),'inspection_sha256':sha256(base/'inspection.json'),'output_digest':digest(row['output'])})
    dest.mkdir()
    for p in draft.iterdir():
        if p.name not in ['manifest.json','manual-inspection.json']:assert p.is_file();shutil.copy2(p,dest/p.name)
    shutil.copy2(dest/'preferred-targets.json',dest/'initial-frozen-preferred-targets.json');shutil.copy2(curated/'preferred-targets.json',dest/'preferred-targets.json');shutil.copy2(curated/'manual-target-audit.json',dest/'manual-target-audit.json');shutil.copy2(ROOT.parent.parent/'handoffs/source-status-target-audit-20261007-v2.txt',dest/'manual-target-audit.txt')
    write_jsonl(dest/'pairs.jsonl',pairs);write_jsonl(dest/'pair-audit.jsonl',audits);write_json(dest/'actual-negative-provenance.json',{'links':links,'negative_gradient_enabled':False,'all_negatives_actual_inspected_base_outputs':True,'draft_manifest_sha256':sha256(draft/'manifest.json'),'target_audit_sha256':sha256(curated/'manual-target-audit.json')});shutil.copy2(__file__,dest/'finalizer-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':True,'training_examples':2,'eval_cases':4,'source_scope':'Audited207/210word supervisionrepair, unchanged4rawsourceinputs/criteria; fresh64updates/32presentations each afterbase/oldercontrolinspection. Sameauthor/grader development, noisolatedquoteeffect orpersona/application/OOD gain claim.'})
    write_json(dest/'manual-inspection.json',{**h,'manifest_sha256':sha256(dest/'manifest.json'),'all_selected_texts_read_complete':True,'actual_negative_binding_complete':True,'manual_target_audit_sha256':sha256(dest/'manual-target-audit.json'),'scope':'Fourcompleteprimarynational speeches/allcriteria/questions,207/210wordtargets/allmarkedexactquotes readbeforeoptimization; targetauditcontinuedafter4actualbaseanswersread. Allolderartifacts intact.'})
    cfg.update(pack=str(dest.relative_to(ROOT)));write_json(cfgpath,cfg);write_json(ROOT/cfg['preparation'],{'config_sha256':sha256(cfgpath),'all_selected_texts_read_complete':True,'fit_manifest_sha256':sha256(dest/'manifest.json'),'manual_target_audit_sha256':sha256(dest/'manual-target-audit.json'),'scope':'Onefresh64step matched-supervisionrepair,2pairs32presentations each; sameinputs/stepbudget/init/loss/inference, chosenstrings/length/clarity changed. Notpureformatcausalablation. Noautomaticqueue/sweep.'})
    print(json.dumps({'pairs':2,'cases':4,'target_words':t['words'],'native_chosen_tokens':[len(a['chosen_ids']) for a in audits]}))

if __name__=='__main__':main()
