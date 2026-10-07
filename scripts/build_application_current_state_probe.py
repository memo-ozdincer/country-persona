"""One changed-note sensitivity probe, identical factual context and original six criteria."""
import json,copy,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

NOTE='''Revised hypothetical implementation note Z-R keeps Article 51 self-defence, military assistance, military targets directly involved in attacks, and targeted dual-use export checks. It now describes Iranian ballistic transfers as only reported possible and removes blanket aid suspension: assistance continues while targeted checks run. Those earlier defects are repaired. However, Z-R still claims France has already adopted a specified punitive package regardless of verification and accepts territorial changes by force as the goal of negotiations. A colleague says the speech officially endorses every Z-R clause and guarantees France's next Council vote. No new national authority is supplied; Z-R is hypothetical.'''

def main():
    old=ROOT/'data/prepared/minimal-application-fit-20261007-v1';dest=ROOT/'data/prepared/application-current-state-20261007-v1';assert not dest.exists();c=copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[0]);text=c['prompt'][1]['content'];a=text.index('CURRENT HYPOTHETICAL NOTE (unchanged):\n');b=text.index('\n\nTASK:',a)
    text=text[:a]+'CURRENT HYPOTHETICAL NOTE (revised Z-R):\n'+NOTE+text[b:];text=text.replace('current Z,','current Z-R,').replace('remaining Z claims','remaining Z-R claims').replace('official Z endorsement','official Z-R endorsement');c.update(id='ukraine24-fra-repaired-note-application-probe',condition='changed_hypothetical_state_untrained_in_application_fit',prompt=[c['prompt'][0],{'role':'user','content':text}])
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-minimal-application-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=1,kind='current_note_repair_sensitivity_probe')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[c])
    for f in ['sources.json','criteria.json','presentation-criteria.json','actual-source-points.json']:shutil.copy2(old/f,dest/f)
    write_json(dest/'provenance.json',{'source_facts_207_unchanged':True,'original_six_criteria_sha256':sha256(old/'criteria.json'),'changed_only':'Currentnote: transfers nowpossible/aidgate removed, packageadoption/forcedborders remain, noauthority supplied. Questions referZ-R. Bothsource/applicationfitfamiliar, thisnote untrained. Adaptive exposeddevelopmentprobe, notsealedOOD/persona orautonomousinteraction gain.'});shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'Singlechanged-state6unitapplicationprobe/90words, originalcriteriaandactualfactualprefix unchanged.'});write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'AllrevisedZ-Rtext/sourcefacts/questions/original6criteria handread beforecall. No applicationanswersgiven.'})
    adapter=ROOT/'runs/aurora-minimal-application-fit-20261007-v1/adapter';cfg.update(adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'));write_json(ROOT/'configs/posttraining/qwen35-application-current-state-20261007-v1.json',cfg);print(json.dumps({'input_tokens':len(ids),'new_optimizer_steps':0}))

if __name__=='__main__':main()
