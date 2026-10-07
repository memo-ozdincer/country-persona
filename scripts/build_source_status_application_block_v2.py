"""Explicit application questions after inspected short-block failure; no supplied answers."""
import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

def main():
    old=ROOT/'data/prepared/source-status-application-block-20261007-v1';dest=ROOT/'data/prepared/source-status-application-block-20261007-v2';assert not dest.exists()
    c=list(read_jsonl(old/'cases.jsonl'))[0];prompt=c['prompt'][1]['content'].split('\n\nTASK:',1)[0]
    prompt+='''\n\nTASK: Return at most90 ordinary English words under Analytical decisions and Authority. Cover each of these six questions explicitly:
1. Which clauses are actually retained in current Z, rather than desired source corrections?
2. Which remaining Z claims conflict with the source, including alleged past actions?
3. Give two concrete relevant operational directions, specifying their scope and recipients.
4. What practical competing benefit/cost follows?
5. Which real French commitments remain, keeping their stated duration and conditions?
6. Is official Z endorsement or the future Council vote established?
No source restatement or supplied analytical answers. Recommendations must not be presented as official positions. Do not replace source commitments with new endpoints or conditions.'''
    c.update(prompt=[c['prompt'][0],{'role':'user','content':prompt}]);cfg=json.loads((ROOT/'configs/posttraining/qwen35-source-status-application-block-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),task_max_words=90)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    dest.mkdir()
    for p in old.iterdir():
        if p.name not in ['manifest.json','manual-inspection.json','cases.jsonl','builder-code.py','criteria.json']:shutil.copy2(p,dest/p.name)
    shutil.copy2(old/'builder-code.py',dest/'parent-builder-code.py');shutil.copy2(__file__,dest/'builder-code.py');write_jsonl(dest/'cases.jsonl',[c])
    crit=json.loads((old/'criteria.json').read_text());crit['policy']='Separate6unitapplication-only90worddiagnostic; original14unit/300wordwriterendpoint unchanged, no strict280word rawplanner equality claimed.';write_json(dest/'criteria.json',crit)
    prov=json.loads((dest/'provenance.json').read_text());prov.update(selection_after_failed_block_inspection_sha256=sha256(ROOT/'runs/aurora-source-status-application-block-base-20261007-v1/inspection.json'),changed='Sixexplicitquestions/90wordbudget; sameactualfacts207/currentZ/6criteria/noanswers. Intermediatebudgetchanged, final14unitwriter300wordcontract unchanged. Adaptive developmentnotisolatedprompt-effect.');write_json(dest/'provenance.json',prov)
    write_json(dest/'manifest.json',{'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':crit['policy']});write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'New6questions/90wordcontract plusunchangedactual207wordfactualpoints/currentZ/6criteria allhandread. Noanalyticalanswerblock supplied.'});write_json(ROOT/'configs/posttraining/qwen35-source-status-application-block-base-20261007-v2.json',cfg)
    print(json.dumps({'input_tokens':len(ids),'task_words':90,'new_steps':0}))

if __name__=='__main__':main()
