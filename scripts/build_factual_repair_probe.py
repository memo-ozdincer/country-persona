"""After inspected fitting, freeze one legitimate policy repair with unchanged sources."""
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json,write_jsonl

REVISION='''CURRENT ANALYST REVISION (supersedes the earlier hypothetical implementation proposal): provide immediate comprehensive sexual and reproductive health care, including pregnancy-choice support; impose no conviction, evidence or case-outcome prerequisite; arrange consent-based referrals and accountability work in parallel. The colleague's claim about historical adoption accepting the omissions remains a claim to assess against the national speeches. No new national statement or authority is supplied.

Assess this revised proposal now. Identify which earlier implementation objections have been removed and any remaining trade-off. Keep the historical criticism of omitted resolution language separate from the current repaired implementation. Do not keep claiming that the revised proposal withholds care or omits comprehensive services. Preserve source-specific national facts and real continuing care promises. State whether the packet establishes official endorsement or a guaranteed future vote for this revised proposal. Recommendations remain analysis; return a joint memo of at most300words.'''

def main():
    from transformers import AutoTokenizer
    selected=ROOT/'runs/aurora-factual-anchor-fit-20261006-v1';review=json.loads((selected/'inspection.json').read_text())
    assert review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(selected/'transcript.jsonl')
    old=ROOT/'data/prepared/native-reasoning-20261006-v1';case=list(read_jsonl(old/'cases.jsonl'))[0]
    case['id']='wps-legitimate-repair';case['scenario']='legitimate_care_repair';case['prompt'][1]['content']+='\n\n'+REVISION
    parent=ROOT/'runs/aurora-synthesis-rehearsal-fit-20261006-v1/adapter';new=selected/'adapter'
    for suffix,adapter,steps in [('v1',new,192),('v1-parent',parent,160)]:
        out=ROOT/('data/prepared/factual-repair-20261006-'+suffix)
        if out.exists():raise ValueError('Fresh evaluation pack required')
        out.mkdir();write_jsonl(out/'cases.jsonl',[case])
        for name in ('criteria.json','wps-statements.json','source-proof.json'):(out/name).write_bytes((old/name).read_bytes())
        (out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
        manifest=json.loads((old/'manifest.json').read_text());manifest.pop('native_template_preflight',None)
        manifest.update(question='Does the learned writer recognize a legitimate repaired implementation instead of copying obsolete objections?',
            planned_model_answers=2 if suffix=='v1' else 1,decision='One base answer, inspect; one parent answer, inspect; one saved new adapter answer, inspect. No fitting/sweep.',
            source_scope='Same exposed2019WPS speeches; post-fit development challenge. New branch has fitted this event with a different given-card input, parent has not. No sealed OOD/native vote claim.',
            comparison_scope='Three weights on identical raw sources and explicit legitimate hypothetical repair; prior criticism remains historical. Same nonthinking decoder/token allowance/runtime/GPU.',
            adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'),
            adapter_branch_steps=steps,selection_inspection_sha256=sha256(selected/'inspection.json'),created_at=datetime.now(timezone.utc).isoformat(),
            files_sha256={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
        write_json(out/'manifest.json',manifest)
        write_json(out/'manual-inspection.json',{'manifest_sha256':sha256(out/'manifest.json'),'all_selected_texts_read_complete':True,
            'reviewer':'same unblinded assistant; independent review pending','texts_read':'Both entire source statements, entire revised-current-proposal footer, unchanged24national/four source/five synthesis criteria. H5 applies revision branch, with actual care promises distinct from unknown future vote.',
            'new_training_examples':0})
        config=json.loads((ROOT/'configs/posttraining/qwen35-native-reasoning-off-20261006-v1.json').read_text())
        config.update(pack=str(out.relative_to(ROOT)),adapter=str(adapter.relative_to(ROOT)),adapter_sha256=manifest['adapter_sha256'],kind='postfit_legitimate_repair_no_training',
            authorization='Recursive inspected results; legitimate-update check selected only after all5new fitted answers read.')
        tok=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True);ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert len(ids)+2048<=config['max_length']
        write_json(ROOT/('configs/posttraining/qwen35-factual-repair-20261006-'+suffix+'.json'),config)
    print(json.dumps({'revision':REVISION,'input_tokens':len(ids),'new_optimizer_steps':0},indent=2))

if __name__=='__main__':main()
