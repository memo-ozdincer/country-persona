"""Build small public figure data from stored inventories and measured receipts.

No inference, training, private source bodies, or experiment scheduling.
"""
import hashlib
import json
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


class SampleData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reading = False
        self.raw = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'sample-data':
            self.reading = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.reading = False

    def handle_data(self, text):
        if self.reading:
            self.raw += text


def build():
    paths = [
        'explorer/overview.json', 'explorer/sources.json',
        'reports/open-character-reproduction-20261004.json',
        'reports/eval-pilot-20260926/unbench-audit.json',
        'reports/eval-pilot-20260926/unsc-bench-audit.json',
        'reports/qwen35-source-plan-checkpoint-20261002.json',
    ]
    overview, inventory, humor, unbench, unsc, application = [
        json.loads((ROOT / p).read_text()) for p in paths
    ]
    paths += ['explorer/catalog-summary.json', 'explorer/training-examples.json',
              'explorer/decision-showcase.json', 'explorer/training-samples.html']
    catalog = json.loads((ROOT/paths[6]).read_text())
    examples = json.loads((ROOT/paths[7]).read_text())
    decisions = json.loads((ROOT/paths[8]).read_text())
    parser = SampleData()
    parser.feed((ROOT/paths[9]).read_text())
    sample = json.loads(parser.raw)['samples'][0]
    flag_codes = {'CHN':'cn', 'DEU':'de', 'FRA':'fr', 'GBR':'gb', 'IND':'in', 'BRA':'br'}
    groups = {
        'Press conferences': ['mfa', 'germany_press'],
        'National policy & diplomacy': ['china_mission', 'germany_mission', 'germany_aa',
            'national_policy_documents', 'france_mfa', 'france_elysee', 'france_sgdsn',
            'uk_cabinet_office', 'uk_fcdo', 'uk_desnz', 'india_un_mission', 'india_pib',
            'brazil_funag', 'brazil_mma'],
        'UN speeches': ['unga_speech_corpus', 'ungdc'],
        'UNGA votes': ['unga_dm'],
        'Human-rights records': ['uhri', 'upr_reports'],
        'WTO policy reports': ['wto'],
        'Country statistics': ['world_bank'],
        'Annotations & joined cases': ['curated', 'decision_cases'],
        'Linked task samples': ['unbench'],
    }
    countries = []
    for country in overview['countries']:
        item = inventory['countries'][country['code']]
        sources = {s['id']: s for s in item['sources']}
        grouped = {name: sum(sources[s]['count'] for s in ids if s in sources)
                   for name, ids in groups.items()}
        assert sum(grouped.values()) == item['count'], country['code']
        countries.append(dict(code=country['code'], name=country['name'],
            flag='assets/flags/'+flag_codes[country['code']]+'.svg',
            count=item['count'], source_collections=len(sources),
            languages=country['languages'], kinds=country['counts'], groups=grouped,
            sources=[dict(id=s['id'], count=s['count'], dates=s['date_range'])
                     for s in item['sources']]))
    arms = {key: {condition: dict(n=m['n'], recognized=m['humor_predictions'],
                rate=round(100*m['humor_recall'], 1))
            for condition, m in value['metrics'].items()}
            for key, value in humor['arms'].items()}
    planning = []
    for label, run_index, suffix in [('Raw source', 0, '-raw'),
                                    ('Checked plan', 0, '-checked_plan'),
                                    ('Explicit-boundary plan', 1, '-repair')]:
        ratings = application['runs'][run_index]['ratings']
        condition = {'label': label}
        for field, arm in [('base', 'base'), ('adapter', 'saved_adapter')]:
            rows = [r for r in ratings if r['arm'] == arm and r['id'].endswith(suffix)]
            assert len(rows) == 2
            assert sum(sum(r['counts'].values()) for r in rows) == 24
            condition[field] = sum(r['counts']['met'] for r in rows)
        planning.append(condition)
    def stored(country, source, task):
        item = examples['countries'][country][source]['tasks'][task]
        return dict(record=item['record'], pointer=item['pointer'])

    records = [
        dict(type='Press-conference Q&A', scope='Public metadata projection',
             **stored('CHN','mfa','authentic_qa')),
        dict(type='Diplomatic statement', scope='Exact statement from the published sample viewer',
             record=sample['sources'][0]),
        dict(type='Policy evidence', scope='Public metadata projection',
             **stored('GBR','uk_desnz','policy_evidence')),
        dict(type='Human-rights recommendation', scope='Public metadata projection',
             **stored('IND','uhri','upr_recommendation')),
        dict(type='Vote record', scope='Public metadata projection',
             **stored('BRA','unga_dm','vote_label_only')),
        dict(type='Country statistic', scope='Public metadata projection',
             **stored('FRA','world_bank','country_statistics')),
        dict(type='Joined decision case', scope='Exact stored case, including project annotations',
             record=decisions['cases'][0]),
        dict(type='Supervised training row', scope='Exact saved prompt and completion',
             record=sample['training_row'], metadata=sample['training_metadata']),
    ]
    result = dict(version='research-homepage-v2', editorial_date='October 2026',
        catalog=catalog, record_examples=records,
        policy_examples=[dict(country=c['code'], **c['examples'][0]) for c in overview['countries']],
        countries=countries, groups=list(groups),
        distinct_source_collections=len({s['id'] for c in countries for s in c['sources']}),
        languages=sorted({l for c in countries for l in c['languages']}),
        inventory_definition=inventory['count_definition'],
        inventory_snapshot=inventory['snapshot'],
        humor=dict(model=humor['model'], arms=arms,
            questions=humor['unique_questions'], conditions=humor['variants_per_question'],
            generations=humor['full_generations'], scope=humor['scope'],
            dependence=humor['dependence']),
        benchmarks=dict(unsc=dict(events=unsc['events'],
            adopted=unsc['configs']['adopted']['rows'], vetoed=unsc['configs']['vetoed']['rows'],
            vote_rows=unsc['all_country_vote_rows'],
            targets={k:v['all_years'] for k,v in unsc['target_coverage'].items()}),
            unbench={split:{k:v for k,v in info.items()
                if k in ['rows', 'events', 'labels', 'countries']}
                for split, info in unbench['task2'].items() if split in ['train','test']}),
        planning_control=dict(unit='met atomic content units', total=24, roles=2,
            conditions=planning,
            status='Exposed development; one unblinded assistant authored plans and grades; independent review pending.'),
        provenance=[dict(path=p, sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    # These are the recorded matched results, not a new scoring of transcripts.
    assert application['status']
    output = ROOT / 'explorer/homepage-data.json'
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(dict(output=str(output), countries=len(countries),
        source_collections=result['distinct_source_collections'],
        languages=len(result['languages']), generations=result['humor']['generations'])))


if __name__ == '__main__':
    build()
