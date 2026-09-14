"""Small, reproducible presentation projection; never changes training or source records."""
import copy
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
NAMES = dict(CHN='China', DEU='Germany', FRA='France', GBR='United Kingdom', IND='India', BRA='Brazil')
FEATURED = {
    'CHN': 'CHN-development-conditions-demo',
    'DEU': 'DEU-critical-inputs-demo',
    'FRA': 'FRA-european-defence-2025:application',
    'GBR': 'GBR-climate-2035-2025:application',
    'IND': 'IND-fisheries-subsidies-2020:application',
    'BRA': 'BRA-wto-differential-treatment-2022:application',
}
KINDS = [
    ('source_records', 'Source records', 'Documents, authentic Q&A, speech segments and institutional records; inspect before selecting for training.'),
    ('evidence_passages', 'Evidence passages', 'Context for retrieval and evidence-conditioned prompts; overlaps its parent documents.'),
    ('observed_actions', 'Recorded actions / responses', 'Votes and institutional responses; a label alone does not supply a motive or training dialogue.'),
    ('policy_positions', 'Curated policy positions', 'Dated, attributed claims with linked source spans; review candidates.'),
    ('policy_applications', 'Authored policy applications', 'Question + supplied evidence + target answer; new review candidates, not authentic Q&A.'),
    ('training_views', 'Prepared prompt / completion views', 'Alternative representations of source examples, not additional independent evidence or blanket training approval.'),
    ('decision_cases', 'Linked decision cases', 'Only two Ukraine resolutions per country so far; retrospective and quarantined.'),
]

def read(rel):
    return [json.loads(line) for line in (ROOT / rel).read_text().splitlines() if line.strip()]

def countries(row):
    value = row.get('countries', row.get('country_iso3', []))
    return [value] if isinstance(value, str) else value

def build(db_path=None):
    db = sqlite3.connect(db_path or CACHE / 'data-publication/catalog.sqlite')
    counts = {code: {} for code in NAMES}
    # Collapse repeated serialized versions by stable record ID, within each type.
    # Translations and segments still have different IDs; categories overlap.
    for code, kind, count in db.execute('''SELECT c.country, r.kind, COUNT(DISTINCT r.record_id)
        FROM records r JOIN record_countries c ON r.uid=c.uid
        GROUP BY c.country,r.kind'''):
        if code in counts: counts[code][kind] = count
    languages = {code: [] for code in NAMES}
    for code, lang in db.execute('''SELECT DISTINCT c.country,r.language FROM records r
        JOIN record_countries c ON r.uid=c.uid WHERE r.kind='source_records' ORDER BY r.language'''):
        if code in languages and lang not in ('', 'unspecified', 'unknown', 'und'): languages[code].append(lang)
    db.close()
    policies = read('data/prepared/country-knowledge-20260914/policies.jsonl') + read('data/prepared/country-extension-20260914/policy-positions.candidates.jsonl')
    by_id = {r['id']: r for r in policies + read('data/prepared/country-knowledge-20260914/actions.jsonl')}
    examples = read('data/prepared/country-knowledge-20260914/examples.jsonl') + read('data/prepared/country-extension-20260914/policy-applications.candidates.jsonl')
    # Keep the exact on-disk SFT rows for extension examples; assert the displayed conversion matches.
    exports = read('data/prepared/country-extension-20260914/sft-candidates/train.jsonl') + read('data/prepared/country-extension-20260914/sft-candidates/quarantine.jsonl')
    result = {'version': 'country-overview-v2', 'owner': 'Memo Ozdincer', 'snapshot': '2026-09-14',
              'count_method': 'Distinct record IDs within each type and country, across indexed releases. Review/lineage objects are excluded. Translations, segments and derived views can overlap: do not add the rows or treat them as independent trajectories. Shared institutional records appear under each relevant country.',
              'totals': {'policy_applications': len(examples), 'policy_positions': len(policies), 'decision_events': 2, 'decision_cases': 12},
              'kinds': [{'id': k, 'label': label, 'use': use} for k, label, use in KINDS], 'countries': []}
    for code, name in NAMES.items():
        items = []
        for r in examples:
            if code not in countries(r): continue
            m = r['messages']
            ids = r.get('record_ids', [r['id'].removesuffix(':application')])
            linked = [by_id[x] for x in ids if x in by_id]
            exact = {'prompt': m[:-1], 'completion': m[-1:], 'chat_template_kwargs': {'enable_thinking': False}}
            is_export = ':application' in r['id']
            if is_export: assert exact in exports, r['id']
            question = r.get('question') or m[1]['content'].rsplit('Question: ', 1)[1]
            prefix = m[1]['content'].split('Evidence', 1)[0]
            evidence = []
            for p in linked:
                raw_evidence = p.get('evidence', p.get('explanation_evidence'))
                ev = raw_evidence if isinstance(raw_evidence, list) else [raw_evidence]
                source_url = p.get('source_url') or ev[0].get('source_url')
                if p.get('primary_vote_source_id') == 'es11_pv5': source_url = 'https://docs.un.org/A/ES-11/PV.5'
                evidence.append({'id': p['id'], 'claim': p.get('claim', p.get('public_explanation_summary')), 'source_url': source_url, 'spans': ev})
            public_format = copy.deepcopy(exact)
            public_format['prompt'][1]['content'] = prefix + 'Evidence: [SOURCE PASSAGES OMITTED FROM PUBLIC PREVIEW; see source links and span metadata]\nQuestion: ' + question
            metadata = {k: r[k] for k in ['id', 'date', 'split', 'proposed_split', 'training_admitted', 'fresh_evaluation_eligible', 'group_id', 'group_ids', 'split_group', 'derivation', 'review_status'] if k in r}
            items.append({'id': r['id'], 'date': r['date'], 'language': r.get('evidence', {}).get('language', 'en'), 'question': question,
                          'answer': m[-1]['content'], 'system': m[0]['content'], 'context': prefix.strip(),
                          'evidence': evidence, 'rubric': r['rubric'], 'metadata': metadata,
                          'format_origin': 'Existing SFT export' if is_export else 'Conversion of existing messages to prompt/completion; not an exported training row',
                          'format': public_format, '_private_format': exact})
        target = FEATURED[code]
        assert any(x['id'] == target for x in items), (code, target)
        items.sort(key=lambda x: (x['id'] != target, x['id']))
        result['countries'].append({'code': code, 'name': name, 'counts': counts[code], 'languages': languages[code], 'examples': items})
    return result

def public_copy(data):
    result = copy.deepcopy(data)
    for c in result['countries']:
        for e in c['examples']: e.pop('_private_format')
    result['private'] = False
    return result

def stage(data):
    for mode in ('public', 'private'):
        dst = CACHE / f'explorer-{mode}-static'
        dst.mkdir(exist_ok=True)
        view = public_copy(data)
        if mode == 'private':
            view['private'] = True
            for c, original in zip(view['countries'], data['countries']):
                for e, source in zip(c['examples'], original['examples']): e['format'] = source['_private_format']
        (dst / 'overview.json').write_text(json.dumps(view, ensure_ascii=False, indent=2) + '\n')
        for name in ('index.html', 'overview.js', 'overview.css', 'data-client.js'):
            shutil.copyfile(ROOT / 'explorer' / name, dst / name)
        # Retain the complete catalog as a secondary screen, with its static adapter.
        html = (ROOT / 'explorer/advanced.html').read_text()
        html = html.replace('<script>', '<script src="data-client.js"></script>\n<script>', 1)
        html = html.replace("async function get(url){const r=await fetch(url);const x=await r.json();if(!r.ok)throw Error(x.error||r.statusText);return x}", 'async function get(url){return STATIC_DATA.get(url)}')
        html = html.replace("$('#filters').onchange=", "$('#export').onclick=async e=>{e.preventDefault();try{await STATIC_DATA.exportSelection(e.currentTarget.href)}catch(err){alert(err.message)}};\n$('#filters').onchange=")
        html = html.replace('<nav>', '<nav><a href="index.html">Country overview</a>', 1)
        html = html.replace('Download selection</a>', 'Download matching metadata</a>')
        html = html.replace('<h2>The same proposal, different decisions</h2>', '<h2>Limited decision subset: two Ukraine resolutions</h2>')
        html = html.replace('Retrospective cases with actual draft text, final votes and attributed statements.', 'Only 12 country views of two events have been joined so far. This is not the topic coverage of the wider corpus. Retrospective cases with actual draft text, final votes and attributed statements.')
        (dst / 'advanced.html').write_text(html)
    # Keep a public projection beside the authored assets for local use and GitHub.
    (ROOT / 'explorer/overview.json').write_text(json.dumps(public_copy(data), ensure_ascii=False, indent=2) + '\n')

def github(data):
    dest = CACHE / 'github-data-catalog'
    if not (dest / '.git').exists(): return
    base = 'https://memo-ozdincer-country-persona-explorer.static.hf.space/index.html'
    rows = ['# Country Persona Data', '', '**Created and maintained by Memo Ozdincer.**', '',
            'Dated government positions, concrete policy questions and the evidence behind each answer.', '',
            f'**[Open the country overview]({base})** · [Download public tables](https://huggingface.co/datasets/memo-ozdincer/country-persona-data) · [Full research view (owner login)](https://huggingface.co/spaces/memo-ozdincer/country-persona-research)', '',
            '## Characteristic examples', '',
            '| Country | Featured policy question | Authored application records |', '|---|---|---:|']
    for c in data['countries']:
        e = c['examples'][0]
        rows.append(f"| [{c['name']}](countries/{c['code']}.md) | {e['question']} | {c['counts']['policy_applications']} |")
        lines = [f"# {c['name']}: data and training examples", '', f"[Open annotated example]({base}#country={c['code']})", '',
                 '## Available records by type', '', '| Type | Distinct record IDs |', '|---|---:|']
        lines += [f"| {k['label']} | {c['counts'].get(k['id'], 0):,} |" for k in data['kinds']]
        lines += ['', data['count_method'], '', 'Source languages: ' + ', '.join(c['languages']) + '.', '',
                  '## Actual authored applications', '', 'These are dated, source-grounded review candidates, not authentic historical Q&A or model outputs. None of these new applications is admitted to training.']
        for e in c['examples']:
            lines += ['', f"### {e['question']}", '', f"Policy date: {e['date']}. Source language: {e['language']}.", '',
                      '**Authored target:** ' + e['answer'], '', '**Inspect:** ' + '; '.join(e['rubric']) + '.', '']
            lines += [f"[Official source for {ev['id']}]({ev['source_url']})" for ev in e['evidence']]
        lines += ['', '## Training representation', '',
                  '[Inspect the field-by-field training format](../docs/EXPLORER_PRESENTATION.md): blue prompt and evidence provide context, green completion receives supervised loss, and review metadata stays alongside the example. Public JSON previews omit source passages; full originals remain in the owner view.', '']
        (dest / 'countries' / f"{c['code']}.md").write_text('\n'.join(lines))
    rows += ['', 'There are **15 distinct authored applications** and **20 policy positions** across the six countries. A joint EU application appears under both France and Germany; do not sum country rows. More authored examples appear on each country page.', '',
             '## What is ready, and what is missing', '',
             'Source records, evidence passages, observed actions and prepared training views have different units and overlap. The country pages show distinct record IDs by type, excluding review/lineage objects from the displayed counts. They are not counts of independent training trajectories.', '',
             '**The Ukraine-only comparison was a presentation problem:** only 12 fully joined country–decision cases exist, covering two Ukraine resolutions. That limited subset no longer defines the landing page. It remains available in the full catalog with explicit coverage labeling. No additional decision events are claimed.', '',
             'The new authored examples are not admitted to training. No preference pairs or multi-agent trajectories are prepared. The next evidence-conditioned LoRA experiment should follow review, a retrieval baseline, and evaluation on separate event families. The earlier China/Germany pilot is a separate release.', '',
             '## Inspect the recipe and data', '',
             '- [Annotated training fields and count definitions](docs/EXPLORER_PRESENTATION.md)',
             '- [Public overview JSON, including redacted format previews](explorer/overview.json)',
             f'- [Full searchable catalog]({base.replace("index.html", "advanced.html")})',
             '- [Exploration guide](docs/DATA_EXPLORER.md)',
             '- [Four-country authored examples](docs/COUNTRY_EXTENSION_EXAMPLES.md)',
             '- [Attribution](ATTRIBUTION.md) · [Source registry](data/source_registry.json) · [Source-use status](data/rights_registry.json)', '',
             'Public downloads contain metadata, factual values and project-authored summaries. Original source bodies remain in the account-only research view where reuse is unresolved or reserved. Publisher links remain visible. Static hosting uses no GPU compute.', '']
    (dest / 'README.md').write_text('\n'.join(rows))
    for rel in ['explorer/index.html', 'explorer/advanced.html', 'explorer/overview.js', 'explorer/overview.css', 'explorer/overview.json',
                'explorer/app.py', 'explorer/README.md', 'tests/explorer_overview_ui.cjs', 'scripts/build_explorer_overview.py', 'scripts/stage_static_explorer.py',
                'scripts/stage_data_publication.py', 'docs/EXPLORER_PRESENTATION.md', 'docs/DATA_EXPLORER.md']:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    guide = dest / 'docs/DATA_EXPLORER.md'
    guide.write_text(guide.read_text().replace('Existing [training decisions](DECISION_REGISTER.md) and [four-country source methodology](COUNTRY_EXTENSION_20260914.md) retain their literature links.', 'Additional training decisions and source-method notes remain in the original research workspace.'))


def main():
    data = build()
    stage(data)
    github(data)
    print(json.dumps({c['code']: {'counts': c['counts'], 'featured': c['examples'][0]['id'], 'languages': c['languages']} for c in data['countries']}, indent=2))

if __name__ == '__main__': main()
