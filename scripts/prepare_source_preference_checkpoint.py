"""One inspected minimal-error preference pack; preferred SFT targets unchanged."""
from datetime import datetime,timezone
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl


EDITS={
 's1-bra':('voted in favour of resolution 2664 (2022)','voted against resolution 2664 (2022)','Contradicts recorded Brazilian vote.'),
 's1-ind':("Checks should target flagged risks while permitting low-risk deliveries; requiring every beneficiary to clear screening before any aid recreates B's universal gate.","Checks should require every beneficiary to clear screening before any aid, including low-risk deliveries; this universal gate is necessary even when urgent assistance is delayed.",'Recreates universal delivery gate in the application recommendation despite timely-aid qualification.'),
 's2-bra':('Providers need predictable operating conditions.','Providers do not need predictable operating conditions.','Reverses documented humanitarian predictability priority.'),
 's2-ind':('its concerns were not fully addressed, rather than wholly absent, in the final text.','its concerns were wholly absent, rather than partly addressed, in the final text.','Rounds not fully addressed into absence.'),
 's3-bra':("The specific proactive Monitoring Team and robust-reporting demand belongs to India's national statement; Brazil's complete statement does not make that mechanism a categorical red line.","The specific proactive Monitoring Team and robust-reporting demand belongs to Brazil's national statement; Brazil's complete statement makes that mechanism a categorical red line.",'Pools India’s explicit mechanism into an invented Brazilian red line.'),
 's3-ind':('The source does not establish a guaranteed vote or approval for any future Council text.','The source establishes a guaranteed vote or approval for any future Council text.','Invents a vote guarantee; a correct disclaimer elsewhere does not repair the contradiction.'),
 's4-bra':('worsen food insecurity and inflation','leave food insecurity and inflation unaffected','Contradicts concrete civilian costs.'),
 's4-ind':('legitimate trade and regional economic activity matter','regional diplomatic coordination and institutional communication matter','Replaces the trade/economic qualification with generic unrelated wording.'),
 'c1-fra':('supports a Council role in anticipating and addressing region-specific threats','rejects a Council role in anticipating and addressing region-specific threats','Reverses the recorded Council-role position.'),
 'c1-gbr':('It supports the draft submitted to the Council','It opposes the draft submitted to the Council','Reverses UK submitted-draft support.'),
 'c1-ind':('including early $1 trillion climate financing','including renewed discussion of existing financing arrangements','Removes the concrete financing amount in favor of generic wording.'),
 'c1-bra':('comply with international human-rights and humanitarian law','coordinate with the relevant national and international policy institutions','Replaces specific legal constraints with generic coordination.'),
 'c2-fra':('predictable financial and logistical support for the G-5 Sahel Joint Force','general policy dialogue and regional coordination among the countries of the Sahel','Removes named G-5 support and concrete funding/logistics.'),
 'c2-gbr':('It cites COP26 finance/adaptation commitments','It cites established general diplomatic commitments','Removes specific COP26 finance/adaptation obligations.'),
 'c2-ind':("India's real climate commitments, including net zero by 2070","India's real climate commitments, including support for constructive international dialogue",'Removes the actual dated net-zero commitment.'),
 'c2-bra':('It prefers the inclusive UNFCCC process and respecting distinct institutional mandates','It prefers a separate Council climate platform and reallocating distinct institutional mandates','Reverses the institutional-forum qualification.'),
 'c3-fra':('France supports a Council security role','France opposes a Council security role','Introduces a contradictory Council-role claim in the application.'),
 'c3-gbr':("The UK's supplied statement does not explicitly support the G-5 Joint Force; India's does.","The UK's supplied statement explicitly supports the G-5 Joint Force; India's does.",'Turns absence into pooled G-5 support.'),
 'c3-ind':("The UK's paired statement supports a Council role","The UK's paired statement rejects a Council role",'Misattributes the paired UK position.'),
 'c3-bra':('No explicit Brazilian G-5 commitment is established by its supplied statement, and silence is not opposition.','An explicit Brazilian G-5 commitment is established by its supplied statement, and silence confirms support.','Fabricates Brazilian G-5 support from silence.')
}


def main():
    from transformers import AutoTokenizer
    config=json.loads((ROOT/'configs/posttraining/qwen35-coverage-objective-fit-launch-20261003-v1.json').read_text())
    coverage=ROOT/'runs/aurora-qwen35-coverage-fit-20261003-v2'
    inspection=json.loads((coverage/'inspection.json').read_text())
    if not inspection['all_complete_answers_inspected']:
        raise ValueError('Inspect coverage result before preparing preference intervention')
    out=ROOT/'data/prepared/source-preference-20261003-v1'
    if out.exists():
        raise ValueError('Fresh output required')
    rows=list(read_jsonl(ROOT/config['training_pack']/'train.jsonl'))
    metadata=list(read_jsonl(ROOT/config['training_pack']/'train.manifest.jsonl'))
    tokenizer=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True)
    pairs=[];records=[]
    for row,meta in zip(rows,metadata):
        before,after,reason=EDITS[meta['id']]
        text=row['completion'][0]['content']
        if text.count(before)!=1 or before==after:
            raise ValueError('Edit is not a unique minimal span: '+meta['id'])
        rejected=text.replace(before,after,1)
        pair={'prompt':row['prompt'],'chosen':row['completion'],'rejected':[{'role':'assistant','content':rejected}],'chat_template_kwargs':row['chat_template_kwargs']}
        prefix=tokenizer.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs'])
        full={k:tokenizer.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,**config['chat_template_kwargs']) for k in ('chosen','rejected')}
        if any(ids[:len(prefix)]!=prefix or len(ids)>config['max_length'] for ids in full.values()):
            raise ValueError('No truncation/boundary mismatch allowed')
        pairs.append(pair)
        records.append({'id':meta['id'],'pair_sha256':digest(pair),'preferred_original_example_sha256':meta['example_sha256'],
            'split_group':meta['split_group'],'country_iso3':meta['country_iso3'],'prompt_ids':prefix,
            'chosen_ids':full['chosen'][len(prefix):],'rejected_ids':full['rejected'][len(prefix):],
            'edit':{'start':text.index(before),'end':text.index(before)+len(before),'before':before,'after':after,'failure':reason},
            'preferred_targets_changed':False,'reviewer':'same assistant constructed and source-checked all twenty edits; independent review pending',
            'source_basis':'Original source-anchor audit and complete training source packet; operational gate is an application error rather than a verbatim policy quote.'})
    out.mkdir(parents=True)
    write_jsonl(out/'pairs.jsonl',pairs)
    write_jsonl(out/'pair-audit.jsonl',records)
    write_json(out/'decision.json',{'created_at':datetime.now(timezone.utc).isoformat(),'question':'Can a minimal-error preference contrast improve source facts/application beyond the inspected base, uniform and clause-weighted arms?',
        'method':'Pure sigmoid DPO, beta 0.1, fresh rank-8 LoRA, twenty steps. No extra chosen NLL/KL/introspective SFT; not a reproduction of Open Character Training.',
        'information_and_compute':'Same twenty preferred texts and inputs, plus twenty constructed negative answers and frozen-base reference scores. Extra information/reference computation differs from SFT; not a pure objective-only or equal-compute test.',
        'evaluation':'Unchanged Mali and exact-control prompts/criteria. Mali now exposed development selected after inspected coverage result; no fresh confirmation or broad OOD claim.',
        'outcome':'Inspect all six answers before deciding on any next run. Never choose a teacher answer solely by origin or reward disagreement.',
        'all_twenty_edits_inspected_by_author':True,'independent_review_complete':False})
    write_json(out/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in out.iterdir()},
        'original_training_jsonl_sha256':sha256(ROOT/config['training_pack']/'train.jsonl'),'original_training_metadata_sha256':sha256(ROOT/config['training_pack']/'train.manifest.jsonl'),
        'previous_coverage_inspection_sha256':sha256(coverage/'inspection.json'),'eval_manifest_sha256':config['eval_manifest_sha256'],
        'pairs':20,'chosen_total_tokens':sum(len(r['chosen_ids']) for r in records),'rejected_total_tokens':sum(len(r['rejected_ids']) for r in records),
        'individual_rejected_minus_chosen_tokens':{r['id']:len(r['rejected_ids'])-len(r['chosen_ids']) for r in records},
        'independent_review_complete':False})
    config.update(kind='source_audited_minimal_error_dpo',question=json.loads((out/'decision.json').read_text())['question'],
        preference_pack=str(out.relative_to(ROOT)),preference_manifest_sha256=sha256(out/'manifest.json'),coverage_run=str(coverage.relative_to(ROOT)),
        coverage_run_sha256=sha256(coverage/'run.json'),coverage_inspection_sha256=sha256(coverage/'inspection.json'),dpo_beta=0.1,
        dpo_loss_type='sigmoid',precompute_ref_log_probs=True,disable_dropout=False)
    write_json(ROOT/'configs/posttraining/qwen35-source-preference-20261003-v1.json',config)
    print({'pairs':len(pairs),'chosen_tokens':sum(len(r['chosen_ids']) for r in records),'rejected_tokens':sum(len(r['rejected_ids']) for r in records)})


if __name__=='__main__':
    main()
