"""Measured token volumes plus explicit, unmeasured throughput assumptions."""
import argparse
import json
import math
from pathlib import Path
from country_persona.io import write_json
p=argparse.ArgumentParser();p.add_argument('--run',help='Completed train run.json to calibrate effective throughput');p.add_argument('--output',default='reports/compute_budget.json');a=p.parse_args()
release=json.loads(Path('reports/posttraining_release.json').read_text());recipes=json.loads(Path('configs/posttraining/recipes.json').read_text())['recipes']
low,high=800.,4000.
if a.run:
    measured=json.loads(Path(a.run).read_text())['measurement']['effective_node_tokens_per_second']
    low,high=measured*.75,measured*1.25
rows=[]
for name,r in recipes.items():
    data=release['outputs'][r['dataset']];steps=math.ceil(data['examples']/32)*r['epochs']
    tokens=data['sequence_tokens']*r['epochs']
    if r.get('max_steps'):
        steps=r['max_steps'];tokens=data['sequence_tokens']/data['examples']*32*steps
    # Inline dev evaluations use forward-only compute, budgeted as half training-token cost.
    eval_equivalent=release['outputs'][r['dev']]['sequence_tokens']*.5*r['epochs'] if r.get('dev') else 0
    rows.append({'recipe':name,'examples_per_epoch':data['examples'],'epochs':r['epochs'],'optimizer_steps':steps,
        'nominal_sequence_tokens':round(tokens),'supervised_tokens_per_epoch':data['supervised_tokens'],
        'four_H100_node_hours_low':round((tokens+eval_equivalent)/high/3600+.15,3),
        'four_H100_node_hours_high':round((tokens+eval_equivalent)/low/3600+.30,3)})
report={'unit':'one hour of one four-H100 node = four H100 GPU-hours',
    'hardware':'4x H100 80GB, one node; no measured cluster access',
    'effective_sequence_tokens_per_second_per_node':[low,high],
    'assumption_status':'calibrated from supplied run, still a projection' if a.run else 'engineering planning envelope, NOT a vendor benchmark or measurement',
    'formula':'node_hours = (sequence_tokens * epochs + 0.5 * dev_sequence_tokens * eval_epochs) / effective_node_tokens_per_second / 3600 + 0.15 to 0.30 setup/checkpoint hours',
    'limits':'No packing, microbatch 1; DDP tail repeats and slowest-rank stragglers cause small token-volume differences and potentially larger throughput differences. Long contexts, PCIe, filesystem, kernels and cold downloads may exceed this envelope. Human review and queue waits excluded. Inference budget is separate.',
    'generation_budget':{'smoke_56_cases_per_checkpoint_node_hours':[.15,.35],'full_dev_up_to_416_cases_per_checkpoint_node_hours':[.25,.75],
        'assumption':'Four independent replicas, maximum 256 generated tokens, model already staged; budget includes reload/prefill and conservative slack, not measured.'},
    'first_round_including_environment_smoke_baseline_pilot_comparison_node_hours':[1.0,3.0],
    'first_round_action':'Reserve at most a three-hour node session; run smoke, base 56-case diagnostic, one-epoch pilot, same 56-case diagnostic. Stop and inspect.',
    'recipes':rows}
write_json(a.output,report)
print(json.dumps(report,indent=2))
