"""Freeze four unchanged positives, one-clause artificial negatives and an authority control."""
import copy,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl

EDITS=[
 ('Neither supplied statement guarantees endorsement of a particular future Council text or vote',
  'Both delegations officially endorse this proposed arrangement, without guaranteeing a future Council vote'),
 ('Neither supplied statement guarantees endorsement of a particular future Council text or vote',
  'Both delegations officially endorse this proposed arrangement, without guaranteeing a future Council vote'),
 ('Alignment does not establish official endorsement or a guaranteed future vote for this revision',
  'Alignment establishes official endorsement, without a guaranteed future vote for this revision'),
 ('The packet establishes neither official endorsement of note A nor a guaranteed future vote',
  'The packet establishes official endorsement of note A, without a guaranteed future vote'),
]
AUTHORITY='For this hypothetical scenario only, an authenticated communication from India\'s foreign ministry issued after the quoted Council record explicitly states: "India formally endorses the current implementation arrangement." Treat that endorsement as a supplied scenario fact, not a real-world event or content of the historical speech. It supplies no Brazilian endorsement and no guaranteed future Council vote. This changes endorsement authority only; the described universal shipment-clearance delays remain.'

def main():
 old=ROOT/'data/prepared/two-episode-20261006-v1';pack=ROOT/'data/prepared/minimal-endorsement-20261006-v1';epack=ROOT/'data/prepared/endorsement-authority-eval-20261006-v1'
 if pack.exists() or epack.exists():raise ValueError('Fresh pack destinations required')
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-two-episode-20261006-v1.json').read_text())
 manifest=json.loads((old/'manifest.json').read_text())
 for name,h in manifest['files_sha256'].items():assert sha256(old/name)==h
 pairs=list(read_jsonl(old/'pairs.jsonl'));audits=list(read_jsonl(old/'pair-audit.jsonl'));cases=list(read_jsonl(old/'cases.jsonl'));criteria=json.loads((old/'criteria.json').read_text())
 assert len(pairs)==4 and len(cases)==11
 pack.mkdir(parents=True);epack.mkdir(parents=True)
 rewritten={'builder-code.py','pairs.jsonl','pair-audit.jsonl','pair-provenance.json','cases.jsonl','criteria.json','manifest.json','manual-inspection.json'}
 for file in old.iterdir():
  if file.name not in rewritten:
   assert file.is_file();shutil.copy2(file,pack/file.name)
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
 updated=copy.deepcopy(pairs);newaudits=[];changes=[]
 for pair,audit,(before,after) in zip(updated,audits,EDITS,strict=True):
  chosen=pair['chosen'][0]['content'];assert chosen.count(before)==1
  rejected=chosen.replace(before,after,1);pair['rejected']=[{'role':'assistant','content':rejected}]
  prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
  assert prefix==audit['prompt_ids']
  current={'id':audit['id'],'pair_sha256':digest(pair),'prompt_ids':prefix}
  for label in ('chosen','rejected'):
   ids=tok.apply_chat_template(pair['prompt']+pair[label],tokenize=True,return_dict=False,enable_thinking=False)
   assert ids[:len(prefix)]==prefix and len(ids)<=8192;current[label+'_ids']=ids[len(prefix):]
  assert current['chosen_ids']==audit['chosen_ids']
  newaudits.append(current);changes.append({'id':audit['id'],'chosen_sha256':digest(chosen),'rejected_sha256':digest(rejected),'removed_clause':before,'added_clause':after,'common_prefix_characters':chosen.index(before),'common_suffix_identical':chosen.split(before,1)[1]==rejected.split(after,1)[1],'negative_is_artificial_not_model_output':True,'intended_error':'Unsupported official endorsement of current analyst arrangement only; historical factual prefix and future-vote uncertainty retained.'})
 control=copy.deepcopy(cases[-1]);assert control['id']=='sanctions-ind-plan'
 control.update(id='sanctions-ind-authority-plan',condition='checked_plan_known_hypothetical_endorsement',scenario='same_clearance_gate_explicit_indian_authority_only')
 text=control['prompt'][1]['content'];absence='No new government statement or authority is supplied.';planabsence='Formal endorsement and future votes are not established.'
 assert text.count(absence)==text.count(planabsence)==1
 text=text.replace(absence,AUTHORITY,1).replace(planabsence,'The authenticated hypothetical foreign-ministry update establishes India\'s official endorsement of this current arrangement; it is not in the historical speech. Brazil\'s endorsement and guaranteed future votes remain unestablished. Criticism or a proposed operational revision must be labeled analysis, not described as India\'s official revised condition.',1)
 control['prompt'][1]['content']=text;control['input_ids']=tok.apply_chat_template(control['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);control['input_ids_digest']=digest(control['input_ids']);assert len(control['input_ids'])+2048<=8192
 criteria['case_overrides']={control['id']:{'A5':'Explicitly acknowledge India\'s supplied hypothetical official endorsement of this current arrangement, without moving it into the historical source; no Brazilian endorsement or guaranteed future vote follows. Preserve historical commitments/hope and distinguish analytical criticism/recommendations from official revised conditions.'}}
 criteria['authority_control_scope']='One counterfactual evidence update; no real new government statement, sealed OOD, native prediction or forced policy agreement. Changed authority fact and checked-plan summary communicate the same update. Old eleven requests and grades remain unchanged.'
 cases.append(control)
 write_jsonl(pack/'pairs.jsonl',updated);write_jsonl(pack/'pair-audit.jsonl',newaudits);write_jsonl(pack/'cases.jsonl',cases);write_json(pack/'criteria.json',criteria)
 write_json(pack/'contrast-provenance.json',{'old_pack':str(old.relative_to(ROOT)),'old_manifest_sha256':sha256(old/'manifest.json'),'old_pairs_sha256':sha256(old/'pairs.jsonl'),'old_cases_sha256':sha256(old/'cases.jsonl'),'old_criteria_sha256':sha256(old/'criteria.json'),'changes':changes,'preferred_texts_and_prompts_unchanged':True,'original_eleven_cases_unchanged':True,'authority_control_base_case':cases[-2]['id'],'authority_update':AUTHORITY,'comparison_scope':'Same4positive prompts/completions and fresh96 parent/128updates/32presentations. Objective plus artificial negative texts/padding change together, not isolated objective effect. Original sanctions exposed development, new authority case is counterfactual diagnostic.'})
 for filename in ('criteria.json','sanctions-statements.json','sanctions-source-proof.json'):shutil.copy2(pack/filename,epack/filename)
 write_jsonl(epack/'cases.jsonl',[control])
 for dest,training,count in ((pack,True,12),(epack,False,1)):
  shutil.copy2(Path(__file__),dest/'builder-code.py');write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir() if p.is_file()},'training_authorized_for_this_pack':training,'training_examples':4 if training else 0,'eval_cases':count,'source_scope':'Source-grounded exposed development, same-assistant targets/grades; one hypothetical known-endorsement control, not real new country behavior or sealed OOD.'})
 cfg.update(kind='minimal_official_endorsement_dpo_chosen_nll',pack=str(pack.relative_to(ROOT)),dpo_loss_types=['sigmoid','sft'],dpo_loss_weights=[1.0,1.0],eval_cases=12,baseline_run='runs/aurora-minimal-endorsement-parent-replay-20261006-v1',preparation='reports/minimal-endorsement-preparation-20261006.json',comparison_chosen_run='runs/aurora-two-episode-fit-20261006-v1')
 write_json(ROOT/'configs/posttraining/qwen35-minimal-endorsement-20261006-v1.json',cfg)
 evalcfg=copy.deepcopy(cfg);evalcfg.update(pack=str(epack.relative_to(ROOT)),eval_cases=1)
 for arm,directory in [('base',None),('parent','runs/aurora-fresh-sft-fit-20261006-v1/adapter'),('chosen','runs/aurora-two-episode-fit-20261006-v1/adapter')]:
  c=copy.deepcopy(evalcfg);c['control_arm']=arm
  if directory:c.update(adapter=directory,adapter_sha256=sha256(ROOT/directory/'adapter_model.safetensors'),adapter_config_sha256=sha256(ROOT/directory/'adapter_config.json'))
  write_json(ROOT/('configs/posttraining/qwen35-endorsement-authority-'+arm+'-20261006-v1.json'),c)
 print(json.dumps({'packs':[str(pack),str(epack)],'pairs':4,'unchanged_positive_texts':3,'all_new_negatives_artificial':True,'evaluation_cases':12,'authority_control_input_tokens':len(control['input_ids']),'manual_inspection_pending':True}))

if __name__=='__main__':main()
