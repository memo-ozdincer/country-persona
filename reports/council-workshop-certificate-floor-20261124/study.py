"""Replay the checked Iraq prefix and give its queued delegate the floor."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'research/council_workshop'))

from codex_runner import CodexRunner
from held_suite import metrics
from recording import Recording, decision_request
from replay import replay
from run import pretty, simulate

MATRIX = HERE.parent / 'council-workshop-all-sol-matrix-20261123'
SOURCE = MATRIX / 'iraq-uae-impasse'
EXTENDED = MATRIX / 'iraq-uae-impasse-one-more-call'
REUSED = 53


def read(path):
    return json.loads(path.read_text())


def events(path):
    return list(map(json.loads, path.read_text().splitlines()))


def evaluate(respond):
    settings = read(SOURCE / 'settings.json')
    previous = Recording(SOURCE)
    reused = 0
    new = []

    def decide(seat, prompt, schema):
        nonlocal reused
        request = decision_request(settings, seat, prompt, schema)
        if reused < REUSED:
            answer = previous.take(request)
            assert answer is not None
            reused += 1
            return answer
        reply = respond(request)
        new.append({'seat': seat, 'reply': reply})
        return reply

    result = simulate(settings['case'], settings['countries'], settings['mode'], settings['turn_cap'],
                      settings['vote'], decide, call_cap=settings['call_cap'], skip_poll_after_certificate=True)
    assert reused == REUSED and result['calls'] == reused + len(new)
    assert result.get('certificate_source') is None
    assert result['history'][:15] == replay(SOURCE)['history']
    return metrics(result, settings['case']) | {'reused_calls': reused, 'new_decisions': new}


def plan():
    original = replay(SOURCE)
    extended = replay(EXTENDED)
    before = events(SOURCE / 'calls.jsonl')
    after = events(EXTENDED / 'calls.jsonl')
    assert original['status'] == 'call_cap' and original['calls'] == 55 and len(original['exclusions']) == 4
    assert extended['status'] == 'certified_impasse' and extended['calls'] == 56
    for left, right in zip(before, after, strict=False):
        assert {key: value for key, value in left.items() if key != 'reused'} == {
            key: value for key, value in right.items() if key != 'reused'
        }
    discarded = before[2 * REUSED:]
    assert [event['country'] for event in discarded[::2]] == ['FRA', 'GBR']
    assert all(reply['answer'] == {'action': 'pass'} for reply in discarded[1::2])
    target, reply = after[-2:]
    assert target['country'] == 'BRA' and reply['answer']['action'] == 'declare_impasse'

    def reuse(request):
        assert request == target
        return reply['answer']

    result = evaluate(reuse)
    assert result['calls'] == 54 and result['status'] == 'certified_impasse'
    return {'call_cap': 55, 'reused_calls': REUSED, 'skipped_passes': ['FRA', 'GBR'], 'target': target,
            'archived_reply_replay': result}


def live(design):
    settings = read(SOURCE / 'settings.json')
    runner = CodexRunner(settings['model'], timeout=settings['call_timeout'])
    with (HERE / 'live.jsonl').open('x') as log:
        def write(event):
            print(json.dumps(event, ensure_ascii=False), file=log, flush=True)

        def respond(request):
            if log.tell() == 0:
                assert request == design['target']
            write(request)
            try:
                reply = runner(request['prompt'], request['schema'])
            except (OSError, TimeoutError, ValueError, RuntimeError) as error:
                write({'event': 'error', 'message': str(error)})
                raise
            write({'event': 'response', 'answer': reply})
            return reply

        return evaluate(respond)


def reproduce(design):
    saved = events(HERE / 'live.jsonl')
    assert saved[0] == design['target']
    stream = iter(saved)

    def respond(request):
        assert next(stream) == request
        reply = next(stream)
        assert reply['event'] == 'response'
        return reply['answer']

    result = evaluate(respond)
    assert next(stream, None) is None
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'live', 'replay'))
    args = parser.parse_args()
    design = plan()
    if args.command == 'plan':
        print(pretty(design))
    else:
        assert design == read(HERE / 'plan.json')
        print(pretty((live if args.command == 'live' else reproduce)(design)))
