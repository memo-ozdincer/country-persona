"""CPU-only diagnostic: training-split majority baselines on held-out UPR response groups."""
from collections import Counter,defaultdict
from country_persona.io import read_jsonl,write_json

rows=[r for r in read_jsonl('data/prepared/pilot/pilot.canonical.jsonl') if r['task']=='upr_response']
labels=['Supported','Noted','Supported/Noted']
results=[]
for country in ('CHN','DEU'):
    train=[r for r in rows if r['country_iso3']==country and r['split']=='train']
    counts=Counter(r['text'] for r in train)
    if not train:continue
    prediction=counts.most_common(1)[0][0]
    for split in ('dev','test'):
        test=[r for r in rows if r['country_iso3']==country and r['split']==split]
        if not test:continue
        truth=Counter(r['text'] for r in test)
        recalls=[];f1s=[]
        for label in labels:
            tp=sum(r['text']==label and prediction==label for r in test)
            fp=sum(r['text']!=label and prediction==label for r in test)
            fn=sum(r['text']==label and prediction!=label for r in test)
            if truth[label]:recalls.append(tp/truth[label])
            f1s.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
        results.append({'country':country,'split':split,'train_rows':len(train),'train_class_counts':dict(counts),
                        'eval_rows':len(test),'eval_groups':len({r['split_group'] for r in test}),
                        'eval_class_counts':dict(truth),'prediction':prediction,
                        'accuracy':truth[prediction]/len(test),'balanced_accuracy_observed_classes':sum(recalls)/len(recalls),
                        'macro_f1_fixed_3_classes':sum(f1s)/len(f1s)})
report={'baseline':'per-country majority response from train only','results':results,
        'limitations':['Retrospective response labels, not a prospective forecast.',
                      'Many recommendations share a small number of country-review events; row counts overstate independence.',
                      'No LLM, training run, or expert persona evaluation was performed.']}
write_json('reports/decision_baselines.json',report)
print(report)
