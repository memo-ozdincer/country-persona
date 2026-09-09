"""Build the human-readable inventory from measured pipeline outputs."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from country_persona.io import read_jsonl,write_json

root=Path('.')
normal=json.load(open('reports/normalization.json'))
build=json.load(open('reports/build_report.json'))
audit=json.load(open('reports/pilot_audit.json'))
uhri=json.load(open('reports/uhri_raw_audit.json'))
unga_dm=json.load(open('reports/unga_dm_raw_audit.json'))
lines=['# Acquired data and prepared pilot','', 'Snapshot: 9 September 2026. Counts below were measured from downloaded files and executed parsers; they are not the source-registry estimates.','',
       '## What is on disk','', '| Source | Acquired source material | Parsed output |', '|---|---|---|']
for source in ['mfa','germany_press','china_mission','germany_mission','ungdc']:
    listing=json.load(open('data/manifests/'+source+'.json'))
    n=normal[source];tasks=', '.join(f"{v:,} {k}" for k,v in n['tasks'].items())
    lines.append(f"| {source} | {len(listing['documents']):,} pages | {tasks} |")
lines += [f"| Speaking Volumes UNGA corpus | 32,366 source segments, 203 source country labels, 1992–2018 | {normal['unga_speech_corpus']['parsed_records']:,} originals + speaker-span derivatives |",
          f"| OHCHR/UHRI | {uhri['counts']['total']:,} records, including {uhri['counts']['- UPR']:,} UPR | {normal['uhri']['parsed_records']:,} focus-related records/derivatives |",
          f"| UNGA-DM | {unga_dm['rows']:,} country-decision observations, {unga_dm['decisions']:,} decisions | {normal['unga_dm']['parsed_records']:,} China/German historical-entity vote rows |",
          '| UNBench GitHub sample | 30 vote rows plus 34 nested statements; 41 pinned files | 64 benchmark records; the sample contains no China/Germany vote rows |','',
          'Counts include different units and derivatives. Do not add the table rows and describe the total as independent training examples. Complete OHCHR, UNGA-DM and Speaking Volumes source releases are retained locally; the official archives are snapshots of their discovered indexes, not a claim to cover every statement ever published.','',
          '## Prepared country/task pools','',f"The focused canonical pool contains **{build['pilot_records']:,} records**. There are **{sum(build['candidates'].values()):,} SFT-format candidates** after the implemented selection rules. These are candidates, not an expert-adjudicated or universally rights-cleared training release.",'',
          '| Country | Task | Train | Dev | Test |','|---|---|---:|---:|---:|']
long_report=Path('data/prepared/long-context/build_report.json')
if long_report.exists():
    long=json.loads(long_report.read_text())
    lines.insert(lines.index('## Prepared country/task pools')+2, f"A second, longer-context export is available at `data/prepared/long-context/`: **{sum(long['candidates'].values()):,} candidates**, retaining all 1,541 parsed German Foreign Office answers with their full prior histories. These are alternative views of the same records, not additional independent data. Tokenizer checks remain necessary.\n")
by=defaultdict(Counter)
for key,n in build['candidates'].items():
    country,task,split=key.split('/');by[(country,task)][split]=n
for (country,task),counts in sorted(by.items()):lines.append(f"| {country} | {task} | {counts['train']:,} | {counts['dev']:,} | {counts['test']:,} |")
lines += ['', 'Calendar policy: train through 2025, dev January–June 2026, test July–September 2026. UPR cycles 1–2 train, cycle 3 dev, cycle 4 test; the more restrictive group assignment wins. Benchmark groups remain test. Unknown/future dates and incompatible historical entities are quarantined. Parent records, exact long-text mirrors, symbols and supplied families are grouped before export.','',
          'Separate candidate files live under `data/prepared/pilot/candidates/CHN/` and `.../DEU/`. Full targets and histories excluded by the short-context character budget remain in canonical data. No missing examples are replaced by invented dialogue.','',
          '## Selection and quality','', '| Exclusion | Records |','|---|---:|']
for k,v in build['excluded'].items():lines.append(f'| {k} | {v:,} |')
lines += ['',f"{build['duplicate_records']:,} duplicate candidates are marked with their retained counterpart. Audit errors: **{len(audit['errors'])}**. Raw files whose hashes were checked: **{audit['verified_raw_files']:,}**.",'',
          'The audit covers schema validity, IDs, exact text/group leakage and byte provenance. It does not prove semantic independence, resolve recurring-resolution families, or eliminate base-model pretraining contamination.','',
          'Parsing exceptions are retained in `reports/normalization.json`. Linked ministerial pages in the Chinese mission index need separate institutional attribution; a German joint-statement page links its content rather than providing an extractable speech body. They stay raw and are not silently trained as national mission statements.','',
          '## Important findings','',
          '- Chinese MFA archive migrations separate the original conference date from a later publication date. Both are retained.',
          '- All authentic QA targets are checked against source HTML after whitespace normalization; see `source_span_audit.json`. This checks literal grounding, not political interpretation.',
          '- German Foreign Office targets are selected by the `(AA)` speaker label. Other ministries remain prior context.',
          '- Mission coalition statements and historical governments are not silently turned into modern national supervision.',
          '- Speaking Volumes contains chair text, occasional other speakers and non-ISO country codes. Originals and extracted speaker spans remain separate; available UNGA-DM meeting dates are joined with provenance.',
          '- UPR labels include Supported/Noted. A supported recommendation is not evidence of implementation.',
          '- UNGA-DM retains original/amended votes, absences and suspended non-voting. Missing proposal text keeps this pool out of SFT vote prediction.',
          '- The small UNBench sample cannot supply a China/Germany voting benchmark. The full release and a proposal-text join remain acquisition priorities.','',
          '## First empirical diagnostic','']
p=Path('reports/decision_baselines.json')
if p.exists():
    baseline=json.load(open(p));lines+=['| Country | Split | Rows / groups | Majority prediction | Accuracy | Balanced accuracy |','|---|---|---:|---|---:|---:|']
    for r in baseline['results']:
        lines.append(f"| {r['country']} | {r['split']} | {r['eval_rows']} / {r['eval_groups']} | {r['prediction']} | {r['accuracy']:.3f} | {r['balanced_accuracy_observed_classes']:.3f} |")
    lines+=['','These are CPU-only majority baselines learned from the train split, not LLM results. High accuracy can coexist with poor class balance. A small number of review events limits what thousands of recommendation rows can establish.']
lines+=['','## Remaining work before model-quality claims','',
         'Source-level use decisions, expert samples of role/position fidelity, recurring-family adjudication, model-specific token preflight and the first GPU smoke run remain. The repository supplies a multi-GPU LoRA starter and a paper-based experiment plan. It does not contain a trained country model, a synthetic preference corpus or a multi-agent simulator.','',
         'See `docs/RESEARCH_STRATEGY.md`, `docs/TRAINING_WORKFLOWS.md`, `docs/DATA_DICTIONARY.md`, and `data/source_registry.json`.']
Path('reports/DATA_REPORT.md').write_text('\n'.join(lines)+'\n')
