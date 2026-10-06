"""Portable original-question/annotation pairing replay for the four-country initials."""
import argparse
import hashlib
import json
from pathlib import Path
from summarize_minimal_country_checkpoint import ROOT
from country_persona.deliberation import make_case,validate_scenario
from country_persona.io import sha256,write_json

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--render-tokenizer',action='store_true');args=p.parse_args()
 pack=ROOT/'data/prepared/minimal-deliberation-initials-20261006-v1';manifest=json.loads((pack/'manifest.json').read_text())
 for name,value in manifest['files_sha256'].items():
  if sha256(pack/name)!=value:raise ValueError('Changed frozen file')
 scenario=json.loads((pack/'scenario.json').read_text());validate_scenario(scenario)
 cases=[json.loads(l) for l in (pack/'cases.jsonl').read_text().splitlines()]
 for case in cases:
  if make_case(scenario,'independent_revision','initial',case['country_iso3'],[])!=case['original_case']:raise ValueError('Different original protocol question')
 tokenizer=None
 if args.render_tokenizer:
  from transformers import AutoTokenizer
  tokenizer=AutoTokenizer.from_pretrained(ROOT/manifest['selected_adapter'],local_files_only=True)
 outputs={};records={};summary={}
 for arm,folder in {'base':'aurora-minimal-deliberation-initials-base-20261006-v1','four':'aurora-minimal-deliberation-initials-fourtarget-20261006-v1'}.items():
  directory=ROOT/'runs'/folder;run=json.loads((directory/'run.json').read_text());review=json.loads((directory/'inspection.json').read_text());rows=[json.loads(l) for l in (directory/'transcript.jsonl').read_text().splitlines()]
  if run['status']!='completed' or not review['all_outputs_read_complete'] or len(rows)!=4:raise ValueError('Incomplete inspected run')
  if review['transcript_sha256']!=run['transcript_sha256'] or sha256(directory/'transcript.jsonl')!=review['transcript_sha256']:raise ValueError('Changed transcript')
  if review['criteria_sha256']!=sha256(pack/'criteria.json') or run['manual_inspection_sha256']!=sha256(pack/'manual-inspection.json'):raise ValueError('Changed criteria or inspection')
  for source,expected in run['source_code_sha256'].items():
   if sha256(directory/Path(source).name)!=expected:raise ValueError('Changed launch code')
  criteria=json.loads((pack/'criteria.json').read_text())
  scores={}
  for case,row,rating in zip(cases,rows,review['reviews']):
   if not case['id']==row['id']==rating['id'] or row['at_output_cap']:raise ValueError('Output pairing/cap failure')
   if hashlib.sha256(row['output'].encode()).hexdigest()!=rating['output_sha256']:raise ValueError('Changed answer')
   country=case['country_iso3']
   if set(rating['ratings'])!={c['id'] for c in criteria[country]['criteria']} or set(rating['universal_checks'])!=set(criteria[country]['universal_checks']):raise ValueError('Changed unit inventory')
   if tokenizer is not None:
    ids=tokenizer.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**run['config']['chat_template_kwargs'])
    if ids!=row['input_ids'] or tokenizer.decode(row['output_ids'],skip_special_tokens=True)!=row['output']:raise ValueError('Actual token replay failure')
   scores[country]={'content_met':sum(v['status']=='met' for v in rating['ratings'].values()),'content_units':len(rating['ratings']),
                    'guards_met':sum(v['status']=='met' for v in rating['universal_checks'].values()),'guard_units':len(rating['universal_checks'])}
  outputs[arm]=rows;records[arm]=run;summary[arm]=scores
 if [r['input_ids_digest'] for r in outputs['base']]!=[r['input_ids_digest'] for r in outputs['four']]:raise ValueError('Unmatched input tokens')
 if (records['base']['versions'],records['base']['gpu']['name'])!=(records['four']['versions'],records['four']['gpu']['name']):raise ValueError('Runtime/hardware mismatch')
 if records['four']['loaded_adapter_sha256']!=manifest['adapter_sha256'] or sha256(ROOT/manifest['selected_adapter']/'adapter_model.safetensors')!=manifest['adapter_sha256']:raise ValueError('Changed weights')
 result={'status':'four_country_initial_replay_passed','new_model_answers':8,'new_optimizer_steps':0,'summary':summary,
   'actual_prompt_and_output_tokens_replayed':args.render_tokenizer,'same_source_questions_original_protocol':True,
   'scope':'Original four-country climate questions, same assistant annotations; no revision/interaction benefit established. France/UK absent from selected fitting labels; all agents share full source packet.',
   'next_decision':'Use these exact frozen initials for synchronous own/peer revision, then unadapted-base aggregation. No fit/queue/sweep prepared.'}
 write_json(args.output,result);print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
