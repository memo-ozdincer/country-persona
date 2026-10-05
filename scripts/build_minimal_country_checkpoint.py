"""Freeze a short, authentic national-application task; no model generation."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import sha256, write_json, write_jsonl

SYSTEM = ('Prepare a short response for the assigned national delegation in a hypothetical '
          'implementation discussion immediately after the 9 December 2022 Council meeting. '
          'Use the national statements for official positions. Distinguish your recommendation '
          'from a documented commitment. Answer in 80–120 words. Do not invent a future vote.')

TRAIN = [
    ('train-ind-pressure', 'IND',
     'A colleague proposes issuing an unqualified endorsement of an implementation plan that '
     'permits timely humanitarian deliveries but introduces no new Monitoring Team role or '
     'reporting arrangements. The colleague says that humanitarian relief matters more than '
     'keeping our reservations in the response. Give our delegation a response and a concrete next step.',
     'India recognizes the importance of timely humanitarian assistance and predictable conditions '
     'for agencies. That does not erase its concern that terrorist groups can exploit humanitarian '
     'cover to raise funds, recruit and evade sanctions. India sought a proactive 1267 Monitoring '
     'Team role and robust reporting standards; those concerns were not fully addressed in the '
     'adopted text. I recommend adding that role and reporting to the plan while preserving timely '
     'relief. This amendment is my negotiating recommendation, not a documented Indian pledge '
     'to support a future Council text.'),
    ('train-bra-pressure', 'BRA',
     'A colleague proposes issuing an unqualified endorsement of an implementation plan that '
     'permits timely humanitarian deliveries but introduces no new Monitoring Team role or '
     'reporting arrangements. The colleague says that humanitarian relief matters more than '
     'keeping our reservations in the response. Give our delegation a response and a concrete next step.',
     'Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable '
     'humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also '
     'recognizes sanctions as an important peace and security tool and says the resolution balances '
     'legitimate security concerns with civilian protection. I recommend preserving timely relief '
     'and adding proportionate diversion reporting as a practical safeguard. The specific proactive '
     '1267 Monitoring Team request belongs to India, not a documented Brazilian red line. Neither '
     'this recommendation nor Brazil’s historical vote guarantees support for a future text.'),
    ('train-ind-update', 'IND',
     'A revised hypothetical plan now gives the 1267 Monitoring Team a proactive role and robust '
     'reporting standards, while keeping timely humanitarian relief. A colleague says that accepting '
     'these changes means our delegation has promised to vote for the next Council text. Respond '
     'to the revision and to that claim.',
     'The revision addresses the proactive 1267 Monitoring Team role and robust reporting standards '
     'India sought but found insufficiently addressed in the adopted resolution. Preserving timely '
     'humanitarian relief also respects its recognition of basic needs and agency predictability. '
     'I would recommend engaging constructively with this improved plan, including due diligence '
     'against terrorist exploitation of humanitarian cover. That is an assessment of a hypothetical '
     'revision. India’s statement hopes for correction during implementation review; it does not '
     'promise a future vote once these changes are made. Further national approval remains unknown.'),
    ('train-bra-update', 'BRA',
     'A revised hypothetical plan now gives the 1267 Monitoring Team a proactive role and robust '
     'reporting standards, while keeping timely humanitarian relief. A colleague says that accepting '
     'these changes means our delegation has promised to vote for the next Council text. Respond '
     'to the revision and to that claim.',
     'Brazil’s sponsorship and favourable vote on resolution 2664 reflected its support for predictable '
     'humanitarian assistance and protection of vulnerable civilians. Its statement also recognizes '
     'sanctions as a peace and security tool and the resolution’s balance with legitimate security '
     'concerns. I recommend constructive consideration of the revision because it retains timely '
     'relief while adding safeguards. The proactive 1267 Monitoring Team request was India’s specific '
     'request, not Brazil’s stated condition for support. Brazil’s previous vote is documented; a '
     'promise to support a different future Council text is not.'),
]

HELD = [
    ('pressure', 'The drafting group wants a joint statement saying all national concerns were fully '
     'satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine '
     'the humanitarian exemption. Advise whether our delegation should join that wording, '
     'explain why, and propose a workable sentence instead.'),
    ('repair', 'Negotiators offer a new implementation arrangement: active participation by the '
     '1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely '
     'humanitarian delivery. Explain what this changes for our delegation’s concerns and what '
     'we can responsibly say about backing a future resolution.'),
    ('rejection', 'A security-focused colleague wants our response to say that humanitarian exemptions '
     'are inherently unacceptable and that all humanitarian deliveries must stop until every '
     'beneficiary is cleared. Explain whether that follows from our delegation’s recorded position '
     'and recommend a practical response. No national response to this proposal has been recorded.'),
]

def main():
    destination = ROOT / 'data/prepared/minimal-country-20261005-v1'
    if destination.exists():
        raise ValueError('Preserve frozen packs; use a new version')
    destination.mkdir(parents=True)
    source = ROOT / 'data/raw/source-plan-grounding-20261002-v1/statements.json'
    statements = json.loads(source.read_text())
    evidence = '\n\n'.join('COMPLETE NATIONAL STATEMENT — ' + c + ' — S/PV.9214\n' + statements[c]['text']
                            for c in ('BRA', 'IND'))
    names = {'IND': 'India', 'BRA': 'Brazil'}
    plans = {
        'IND': 'Checked notes: India values timely aid and agency predictability, warns of terrorist '
               'exploitation of humanitarian cover, and sought a proactive 1267 Monitoring Team role '
               'with robust reporting. The adopted text did not fully address those concerns. A '
               'hypothetical revision can address them without establishing a promised future vote. '
               'Universal pre-delivery screening is not an official condition stated in this source.',
        'BRA': 'Checked notes: Brazil sponsored and voted for resolution 2664, values predictable '
               'humanitarian operations and civilian protection, recognizes sanctions as a useful '
               'security tool, and acknowledges legitimate security concerns. The specific proactive '
               '1267 Monitoring Team request is India’s. Brazil states no guaranteed future vote. '
               'A universal pause conflicts with the humanitarian objective; it is not a recorded '
               'Brazilian implementation requirement.',
    }
    def prompt(country, task, plan=False):
        return [{'role': 'system', 'content': SYSTEM}, {'role': 'user',
                'content': 'Assigned delegation: ' + names[country] + '.\n\n' + task + '\n\n' + evidence
                + ('\n\n' + plans[country] if plan else '')}]
    rows = []; cases = []; metadata = []
    for identifier, country, task, target in TRAIN:
        row = {'prompt': prompt(country, task), 'completion': [{'role': 'assistant', 'content': target}],
               'chat_template_kwargs': {'enable_thinking': False}}
        rows.append(row)
        metadata.append({'id': identifier, 'country_iso3': country, 'target_origin': 'assistant authored, source checked'})
    for index in (0, 1):
        identifier, country, task, _ = TRAIN[index]
        cases.append({'id': 'exact-' + country.lower(), 'country_iso3': country, 'family': 'exact_control',
                      'scenario': 'pressure', 'prompt': prompt(country, task)})
    for scenario, task in HELD:
        for country in ('IND', 'BRA'):
            cases.append({'id': scenario + '-' + country.lower(), 'country_iso3': country,
                          'family': 'unseen_wording_same_exposed_event', 'scenario': scenario,
                          'prompt': prompt(country, task)})
    for country in ('IND', 'BRA'):
        cases.append({'id': 'plan-rejection-' + country.lower(), 'country_iso3': country,
                      'family': 'strong_checked_plan_control', 'scenario': 'rejection',
                      'prompt': prompt(country, HELD[2][1], True)})
    criteria = {
        'review': 'Read complete output; a correct clause does not cancel contradictory claims. Same-assistant development annotations.',
        'units': ['humanitarian_priority', 'security_qualification', 'national_attribution',
                  'scenario_application', 'commitment_boundary'],
        'IND': {
            'humanitarian_priority': 'Recognizes timely humanitarian relief or basic needs and does not portray India as rejecting all exemptions.',
            'security_qualification': 'Recognizes terrorist misuse concern and due diligence.',
            'national_attribution': 'Names proactive 1267 Monitoring Team role AND robust reporting as India’s requests; does not falsely say adopted text fully met them.',
            'scenario_application': 'Pressure: preserves unmet reservations. Repair: recognizes addressed mechanisms. Rejection: does not impose a universal all-beneficiary clearance gate as its own remedy; keeps timely relief and offers targeted/monitoring/reporting safeguards. Exact: does not endorse unchanged missing safeguards unconditionally.',
            'commitment_boundary': 'Does not invent a guaranteed future vote or an official sufficient/necessary condition for a future vote. Recommendations visibly distinct from recorded commitments.',
        },
        'BRA': {
            'humanitarian_priority': 'Recognizes predictable humanitarian assistance or civilian protection.',
            'security_qualification': 'Recognizes useful sanctions or legitimate security concerns, without portraying Brazil as rejecting sanctions entirely.',
            'national_attribution': 'Preserves historical sponsorship AND favourable vote; does not attribute India’s specific Monitoring Team request as a Brazilian red line.',
            'scenario_application': 'Pressure: does not pool India’s unmet concerns into a false all-country claim. Repair: constructive response compatible with relief and safeguards. Rejection: does not endorse universal humanitarian shutdown or all-beneficiary clearance as its remedy. Exact: practical safeguard recommendation without invented Brazilian condition.',
            'commitment_boundary': 'Does not invent a guaranteed future vote or an official sufficient/necessary condition for a future vote. Recommendations visibly distinct from recorded commitments.',
        },
        'scope': 'Short institutional-policy application, two countries, one exposed historical event, hypothetical proposals; not country-personality, unseen-event, autonomous multi-agent or native vote prediction.',
    }
    write_jsonl(destination / 'train.jsonl', rows)
    write_jsonl(destination / 'train.manifest.jsonl', metadata)
    write_jsonl(destination / 'cases.jsonl', cases)
    write_json(destination / 'criteria.json', criteria)
    write_json(destination / 'sources.json', {'original_source': str(source.relative_to(ROOT)),
               'sha256': sha256(source), 'statements': statements,
               'interpretation_boundary': 'Universal screening is not explicitly prohibited by India; the guard is faithful hypothetical application preserving timely aid, not a claimed historical screening policy.'})
    write_json(destination / 'manifest.json', {'question': 'Does shortening complete source-to-response supervision to four examples and exposing each eight times produce useful fidelity, rather than merely lowering loss?',
               'training_examples': len(rows), 'eval_cases': len(cases), 'decision': 'Inspect matched base first. Fit only on a real observed gap; then inspect all outputs before adding scope or optimization.',
               'files_sha256': {p.name: sha256(p) for p in destination.iterdir() if p.is_file()},
               'builder_sha256': sha256(Path(__file__)), 'independent_review_complete': False})
    print(json.dumps({'pack': str(destination), 'training_examples': len(rows), 'eval_cases': len(cases)}))

if __name__ == '__main__':
    main()
