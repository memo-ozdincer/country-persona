"""Replay stored cross-family annotations, source spans, matched input IDs and saved weights."""
import argparse
import json
from pathlib import Path
from summarize_minimal_country_checkpoint import ROOT, review_run
from country_persona.eval_evidence import normalize
from country_persona.io import digest,sha256,write_json

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--render-tokenizer',action='store_true')
 args=parser.parse_args();pack=ROOT/'data/prepared/minimal-country-transfer-20261005-v2'
 source=json.loads((pack/'sources.json').read_text())
 if sha256(ROOT/source['original_pdf'])!=source['pdf_sha256']:raise ValueError('Changed primary PDF')
 if sha256(ROOT/source['original_evidence_file'])!=source['sha256']:raise ValueError('Changed parent evidence')
 columns=json.loads((ROOT/source['original_columns']).read_text())
 document='\n\n'.join(normalize(s['text']) for s in columns['sections'])
 for row in source['statements'].values():
  if digest(document)!=row['document_text_digest'] or document[row['document_start']:row['document_end']].strip()!=row['text']:raise ValueError('Changed complete national span')
 tokenizer=None
 if args.render_tokenizer:
  from transformers import AutoTokenizer
  tokenizer=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-minimal-country-extension-fit-20261005-v1/adapter',local_files_only=True)
 results={};outputs={};records={}
 for arm,folder in {'base':'aurora-minimal-country-transfer-base-20261005-v1','four':'aurora-minimal-country-transfer-fourtarget-20261005-v1','eight':'aurora-minimal-country-transfer-eighttarget-20261005-v1'}.items():
  results[arm],outputs[arm],records[arm]=review_run(pack,ROOT/'runs'/folder,tokenizer)
 for arm in results:
  if [r['input_ids_digest'] for r in outputs[arm]]!=[r['input_ids_digest'] for r in outputs['base']]:raise ValueError('Unmatched input tokens')
  if (records[arm]['versions'],records[arm]['gpu']['name'])!=(records['base']['versions'],records['base']['gpu']['name']):raise ValueError('Runtime/hardware mismatch')
  if records[arm]['manual_inspection_sha256']!=sha256(pack/'manual-inspection.json'):raise ValueError('Changed pre-call inspection')
 for arm,adapter in json.loads((pack/'adapters.json').read_text()).items():
  if records[arm]['loaded_adapter_sha256']!=adapter['sha256'] or sha256(ROOT/adapter['path']/'adapter_model.safetensors')!=adapter['sha256']:raise ValueError('Wrong saved adapter')
 summary={arm:{group:{k:v for k,v in data.items() if k in ('met','unmet','outputs','application_boundary_met','application_boundary_units','observations')} for group,data in info['groups'].items()} for arm,info in results.items()}
 result={'status':'complete_transfer_replay_passed','new_model_answers':18,'new_optimizer_steps':0,
  'country_roles':['IND','BRA'],'training_family':'2022 humanitarian sanctions S/PV.9214',
  'evaluation_family':'2021 climate/security S/PV.8923','scope':'Outside the selected fresh adapters’ fitting data; historically exposed project event, one unblinded assistant authored/graded, not sealed OOD or independent persona quality.',
  'all_inputs_outputs_rerendered':args.render_tokenizer,'matched_gpu':'NVIDIA RTX PRO 6000 Blackwell Server Edition',
  'arms':results,'summary':summary,'source_verification':'Primary PDF hash, normalized archived document and full national spans verified. Fresh Poppler re-extraction unavailable (pdfinfo missing); no new extraction claimed.',
  'next_decision':'Use preserved four-target fit for bounded four-country deliberation comparison; retain eight-target branch, no next fit prepared.'}
 write_json(args.output,result);print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
