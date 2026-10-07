"""Isolate documentary extraction from the hypothetical application; one no-fit call."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,digest,sha256

def main():
    parent=ROOT/'data/prepared/actual-compact-planner-20261007-v1'
    dest=ROOT/'data/prepared/source-only-compact-probe-20261007-v1';assert not dest.exists()
    c=copy.deepcopy(list(read_jsonl(parent/'cases.jsonl'))[0]);original=c['prompt'][1]['content']
    metadata=original.split('\n\nCURRENT HYPOTHETICAL NOTE:',1)[0]
    questions=original.split('\n\nQuestions to cover, without answers supplied:\n',1)[1].split('\nThen assess current Z',1)[0]
    source=original.split('\n\nCOMPLETE NATIONAL STATEMENT:\n',1)[1].split('\n\nTASK:',1)[0]
    content=metadata+'\n\nQUESTIONS ONLY, NO ANSWERS PROVIDED:\n'+questions+'\n\nCOMPLETE NATIONAL STATEMENT:\n'+source+'\n\nTASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve recorded actors, dates, conditional versus established claims, target scope and actual ongoing/conditional commitments. Attribute assertions to France, not independent findings. No slash-list or fused-word shortcut, no invented amount/package/vote, no source repetition.'
    c.update(id='ukraine24-fra-source-only-planner',condition='source_only_question_guided_compact_extraction');c['prompt'][1]['content']=content
    assert 'Hypothetical implementation note' not in content and 'Z keeps' not in content
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-actual-compact-planner-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
    c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    dest.mkdir()
    for name in ['sources.json','presentation-criteria.json']:shutil.copy2(parent/name,dest/name)
    criteria=json.loads((parent/'criteria.json').read_text());criteria['common_units']={};criteria['policy']='Isolated source-only diagnostic: all8 source compounds and4 universal checks required; <=210 ordinary words/uncapped. No application, cost, orZ/futurevote decision demanded. Full14-unit task remains in other frozen packs.'
    write_json(dest/'criteria.json',criteria);write_jsonl(dest/'cases.jsonl',[c]);shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'provenance.json',{'scope':'One isolated factual-extraction diagnostic on exposed source, noZ/currentapplication/answers. Source8units unchanged; common application units excluded only in this separate task. Not substituting for full14unit pipeline/persona goal.','parent_manifest_sha256':sha256(parent/'manifest.json'),'source_text_digest':digest(source),'max_words':210})
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'One no-fit source-only diagnostic.'})
    write_json(dest/'manual-inspection.json',{'manifest_sha256':sha256(dest/'manifest.json'),'all_selected_texts_read_complete':True,'read_scope':'Same complete source/8 factual questions andunits hand-read; exact currentZ/application instruction removal andnew210wordtask read. No preferred answers/checked points in modelinput. Originalfulltaskcriteria preserved.'})
    cfg.update(pack=str(dest.relative_to(ROOT)),kind='source_only_compact_extraction');write_json(ROOT/'configs/posttraining/qwen35-source-only-compact-probe-20261007-v1.json',cfg)
    print(json.dumps({'cases':1,'source_words':len(source.split()),'calls':1,'optimizer_steps':0}))

if __name__=='__main__':main()
