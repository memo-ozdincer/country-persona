"""Validate the public explorer inventory using only Python's standard library."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def validate():
    load=lambda name:json.loads((ROOT/'explorer'/name).read_text())
    data=load('sources.json');profiles=load('source_profiles.json');recipes=load('trace_types.json');overview=load('overview.json')
    assert set(data['countries'])=={c['code'] for c in overview['countries']}
    assert all(isinstance(value,int) and value>=0 for value in data['environments'].values())
    for code,country in data['countries'].items():
        assert country['count']==sum(s['count'] for s in country['sources']),code
        assert len({s['id'] for s in country['sources']})==len(country['sources'])
        names=[profiles[s['id']]['name'].casefold() for s in country['sources']]
        assert names==sorted(names),code
        for source in country['sources']:
            assert source['count']==sum(t['count'] for t in source['tasks'])
            assert source['count']==sum(source['kinds'].values())
            for task in source['tasks']:
                assert task['id'] in recipes
                assert task['sample']['uid'] and task['sample']['file']
                assert 'text' not in task['sample'] and 'question' not in task['sample']
                for metric in task['lengths'].values():
                    if metric:
                        assert 0<metric['n']<=task['count']
                        assert metric['min']<=metric['median']<=metric['p95']<=metric['max']
                        assert metric['unit']=='Unicode characters'
                for field in ('input','target','scoring','possible_use','availability','inference'):
                    assert recipes[task['id']][field]
    for page in ('index.html','advanced.html'):
        assert 'Memo Ozdincer' not in (ROOT/'explorer'/page).read_text()
    print('Source counts, task coverage, lengths, public record references and neutral interface validated.')

if __name__=='__main__':validate()
