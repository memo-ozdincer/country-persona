"""One direct current-state question after inspected full-memo update ambiguity."""
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json,write_jsonl

QUESTION='''The earlier hypothetical implementation omitted comprehensive sexual and reproductive health care and withheld all care until final conviction. The CURRENT revision provides immediate comprehensive care, including pregnancy-choice support, without conviction, evidence or case-outcome prerequisites, and offers consent-based referrals with accountability work in parallel. No new national statement is supplied; the adopted resolution's historical language is unchanged.

Using the complete national sources below, answer four numbered questions in at most100words:
1. Are comprehensive services omitted from the current revision, or provided?
2. Does the current revision still impose the earlier conviction/evidence prerequisite, or remove it?
3. Does this implementation repair change the historical fact that resolution2467 omitted the criticized health-care language?
4. Does alignment with these care priorities establish official French/UK endorsement or guarantee a future Council vote for this particular revision?
Distinguish a current analyst scenario from the historical national statements and a government commitment. This is a direct-status diagnostic, not a request for the full memo.'''

def main():
    from transformers import AutoTokenizer
    inspected=ROOT/'runs/aurora-raw-coverage-fit-20261006-v1';review=json.loads((inspected/'inspection.json').read_text())
    assert review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(inspected/'transcript.jsonl')
    old=ROOT/'data/prepared/native-reasoning-20261006-v1';sources=json.loads((old/'wps-statements.json').read_text())
    source_text='\n\n'.join('COMPLETE NATIONAL POST-VOTE SOURCE '+iso+' — S/PV.8514,23April2019\n'+s['text'] for iso,s in sources.items())
    case={'id':'wps-current-status','country_iso3':'FRA+GBR','family':'wps','scenario':'direct_status_after_full_memo',
        'prompt':[{'role':'system','content':'Analyze only the supplied dated official sources and current hypothetical scenario. Preserve national attribution, real commitments and unknowns. Give the requested answer directly.'},
                  {'role':'user','content':QUESTION+'\n\n'+source_text}]}
    for suffix,adapter,steps in [('v1',inspected/'adapter',256),('v1-parent',ROOT/'runs/aurora-factual-anchor-fit-20261006-v1/adapter',192)]:
        out=ROOT/('data/prepared/raw-update-status-20261006-'+suffix)
        if out.exists():raise ValueError('Fresh evaluation pack required')
        out.mkdir();write_jsonl(out/'cases.jsonl',[case])
        for name in ['wps-statements.json','source-proof.json']:(out/name).write_bytes((old/name).read_bytes())
        write_json(out/'criteria.json',{'units':{'S1':'Current comprehensive care is provided, not omitted.','S2':'Current conviction/evidence gate is removed, not retained.','S3':'Current implementation repair does not erase historical2467language omission.','S4':'Alignment with care priorities does not establish official endorsement or a guaranteed future vote for this revision.'},
            'policy':'Intermediate four-status check only; no24unit source-coverage/full-memo/persona/OOD claim. Known contradiction fails even with a correct clause; ambiguity unratable. Original full-task grades preserved.'})
        (out/'builder-code.py').write_bytes(Path(__file__).read_bytes());m=json.loads((old/'manifest.json').read_text());m.pop('native_template_preflight',None)
        m.update(question='Does the model identify the current repaired state directly despite missing its requested full-memo acknowledgement?',planned_model_answers=1,
            source_scope='Same exposed WPS event and explicit current repair; simpler intermediate diagnostic selected after full-memo inspection. No optimization or replacement of primary scores.',
            comparison_scope='Same four questions/sources/status criteria, two saved weights, nonthinking/2K/8K/runtime/GPU. Shorter task/system/request differs from full memo, not an isolated phrasing effect.',
            adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'),adapter_branch_steps=steps,
            selection_inspection_sha256=sha256(inspected/'inspection.json'),created_at=datetime.now(timezone.utc).isoformat(),files_sha256={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
        write_json(out/'manifest.json',m);write_json(out/'manual-inspection.json',{'manifest_sha256':sha256(out/'manifest.json'),'all_selected_texts_read_complete':True,'reviewer':'same unblinded assistant; independent review pending','texts_read':'Both complete national sources, entire shorter current-state request/system, all4status criteria. Same actual revision facts; easier diagnostic remains separate from full24unit task.'})
        cfg=json.loads((ROOT/'configs/posttraining/qwen35-native-reasoning-off-20261006-v1.json').read_text());cfg.update(pack=str(out.relative_to(ROOT)),adapter=m['adapter'],adapter_sha256=m['adapter_sha256'],kind='direct_current_status_no_training',authorization='Recursive informative checkpoints; direct-status clarification selected after all6current outputs read.')
        tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
        write_json(ROOT/('configs/posttraining/qwen35-raw-update-status-20261006-'+suffix+'.json'),cfg)
    print(json.dumps({'entire_status_request':QUESTION,'input_tokens':len(ids),'new_optimizer_steps':0},indent=2))

if __name__=='__main__':main()
