"""Offline model-specific token lengths and completion-boundary checks for candidates."""
import argparse
import json
from pathlib import Path
from transformers import AutoTokenizer
from validate_policy_workshop import ROOT, validate, rows, sha, check


def preflight(output,lock_path,max_length):
    validation=validate(output)
    lock=json.loads(lock_path.read_text())
    for receipt in lock['files']:
        check(sha(ROOT/receipt['path'])==receipt['sha256'],'Tokenizer receipt mismatch')
    tokenizer=AutoTokenizer.from_pretrained(ROOT/lock['tokenizer_path'],local_files_only=True)
    report=json.loads((output/'build-report.json').read_text())
    summaries={}
    for name in report['formats']:
        measured=[]
        for row in rows(output/(name+'.jsonl')):
            options=row['chat_template_kwargs']
            prefix=tokenizer.apply_chat_template(row['prompt'],tokenize=True,add_generation_prompt=True,**options)
            for field in ('chosen','rejected') if name.endswith('dpo') else ('completion',):
                full=tokenizer.apply_chat_template(row['prompt']+row[field],tokenize=True,add_generation_prompt=False,**options)
                check(full[:len(prefix)]==prefix and len(full)>len(prefix),'Completion boundary mismatch')
                check(len(full)<=max_length,'Context length exceeded; no truncation allowed')
                measured.append((len(full),len(full)-len(prefix)))
        summaries[name]={'sequences':len(measured),'max_sequence_tokens':max(n for n,_ in measured),
                         'min_completion_tokens':min(n for _,n in measured),'max_completion_tokens':max(n for _,n in measured),
                         'total_completion_tokens':sum(n for _,n in measured)}
    return dict(status='passed',model=lock['model'],revision=lock['revision'],max_length=max_length,
                tokenizer_lock_sha256=sha(lock_path),build_report_sha256=sha(output/'build-report.json'),
                enable_thinking=False,completion_boundaries_verified=True,truncation_used=False,
                formats=summaries,structural_validation=validation,
                scope='Tokenizer preflight only; not trainer integration, training admission or model quality evaluation.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--lock',type=Path,default=ROOT/'configs/posttraining/qwen3-8b.lock.json')
    parser.add_argument('--max-length',type=int,default=4096)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    result=preflight(args.output,args.lock,args.max_length)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
