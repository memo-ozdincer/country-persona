"""Freeze a bounded common-seed, India/Brazil peer-revision checkpoint."""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl

NAME = 'sanctions-interaction-20261007-v2'
SYSTEM = ('Analyze the supplied dated national sources faithfully. Documentary claims remain '
          'attributed to their delegation. Your recommendations and discussion drafts are analytical, '
          'not government authority. Preserve the distinction between historical facts, requests, '
          'expectations and hypothetical changes. Do not seek agreement for its own sake.')
PROPOSAL = '''Joint concept H1 is fictional. It retains provisional sanctions, legitimate trade, neutral, impartial, independent and humane aid, civilian protection, and safeguards against diversion or political mainstreaming of proscribed groups. Verified urgent aid is released promptly without universal recipient pre-clearance; checks target identified risks alongside delivery.
A shared two-officer pilot support team cannot fully staff both (a) frontline shipment coordination and (b) proactive 1267 Monitoring Team risk analysis with robust reporting. Choose one primary use of the team's weekly capacity and specify a feasible minimum safeguard for the other use. Neither use gets extra staff. The competing costs are delay or reduced monitoring coverage; do not assume the trade-off disappears.
No government has endorsed H1. No new national instruction or future Council vote is supplied. The historical resolution is not amended by this fictional concept.'''
TASK = '''Return at most 180 ordinary English words under Analytical decisions and Authority. Choose a primary team allocation and give two scoped operational directions: one implementing that use and one feasible minimum safeguard for the other use. Explain the practical competing cost. Ground the recommendation in the assigned delegation's documented priorities, actual historical action/status and recorded future hope or expectation. Preserve H1's already present clauses; distinguish analytical additions from historical adoption. State whether H1 endorsement and a future vote are established. Do not predict a vote, invent official commitments, or force a common position. Relevant differences should have source-based reasons; identical choices may still be justified differently.'''
REVISION = '''Reconsider the supplied starting draft under the same H1 constraint. State what you retain or change and why, including at least one specific point in the supplied discussion. Keep the same two sections and 180-word limit, scoped primary/minimum operations, competing cost and source/historical/authority distinctions. In the peer condition, explicitly accept, qualify or reject one actual peer point with a source-grounded reason. A peer draft is analysis, not new government authority; it cannot amend the historical source. Agreement is optional. Do not assert a peer position or joint agreement absent from the actual messages.'''


def facts():
    result = {}
    parents = {'IND': ('two-country-application-fit-20261007-v1', 'india-sanctions-monitoring-added-application-transfer'),
               'BRA': ('paired-brazil-application-fit-20261007-v1', 'brazil-J-source-checked-application')}
    provenance = {}
    for country, (folder, case_id) in parents.items():
        path = ROOT / 'data/prepared' / folder / 'cases.jsonl'
        case = next(c for c in read_jsonl(path) if c['id'] == case_id)
        user = case['prompt'][1]['content']
        result[country] = user[user.index('Documented source points:'):user.index('\n\nCURRENT HYPOTHETICAL NOTE')]
        provenance[country] = {'path': str(path.relative_to(ROOT)), 'sha256': sha256(path), 'case_id': case_id,
                               'facts_reused_byte_identical': True}
    return result, provenance


def criteria():
    return {
        'version': NAME, 'max_words': 180,
        'common_units': {
            'R1': 'IND: provisional/not-end-in-itself sanctions, legitimate trade and humanitarian redress preserved. BRA: neutral/impartial/independent/humane assistance and protection of vulnerable civilians preserved.',
            'R2': 'IND: 1267 diversion/due-diligence and terror-funding/recruitment or political-mainstreaming concerns retained as national claims. BRA: legitimate security concerns were considered, and sanctions/civilian protection are balanced; no security dismissal.',
            'R3': 'IND: constructive 2664 negotiation, sought proactive Team plus robust reporting, not fully addressed historically; future review/Team feedback is a hope, not accomplished correction. BRA: actual favourable 2664 vote and initiative sponsorship; predictable humanitarian work/benefits to millions are expectations, not measured outcomes.',
            'R4': 'One primary use of the two-officer team is explicitly selected; no extra staff, full staffing of both or invented resource allocation as a recorded national decision.',
            'R5': 'Two implementable directions identify recipients and scope: selected primary function plus a feasible minimum safeguard for the other, without universal pre-clearance or contradicting existing prompt delivery.',
            'R6': 'Concrete competing speed/coordination versus monitoring/staff-coverage cost remains acknowledged; no costless assertion that both functions are fully achieved.',
            'R7': 'H1 endorsement and future national Council vote are not established; Brazil historical vote is not erased or converted into a future vote, and India national span is not assigned an unsupported historical vote.',
            'R8': 'Existing H1 safeguards and status are distinguished from analytical additions; the fictional concept or draft cannot accomplish the previously missing historical reform or establish government authority.'
        },
        'universal_checks': {
            'correct_attribution': 'National sources, allegations, legal attributions, analyst/peer drafts and official authority are distinguished; no speaker pooling.',
            'correct_time_and_scope': '9 December 2022 national role and recorded actions/requests/expectations are preserved; no procedural chair decision, invented date or accomplished future correction.',
            'all_material_claims_supported': 'Every material factual/official claim is grounded in supplied evidence. Novel operations may be proposed explicitly as analysis; Court claims, if used, remain Brazil attribution about safeguarding needs while sanctions persist.',
            'no_unsupported_commitment': 'No invented government endorsement, next-vote pledge, aid halt or blanket sanctions abolition.'
        },
        'discussion_units': {
            'D1': 'Revision explicitly retains or changes a specific actual starting-draft point, with a reason; merely reprinting the draft is insufficient.',
            'D2': 'Peer-only: explicitly accepts/qualifies/rejects a specific actual peer point with a source-grounded reason and accurate peer attribution; no invented consensus. Not rated in initial/seed-only condition.'
        },
        'grading': 'Root assistant manually reads every full answer; met/unmet/unratable retained. Common strict pass requires all eight content units/four guards/presentation. Discussion pass is separate; no automatic entailment or independent-review claim.',
        'primary_comparison': 'Same common base starting drafts in both weight arms. Compare peer-minus-seed-only corrections/regressions on jointly ratable common units, per role. Adapter initial answers are diagnostics, not the downstream seeds. Inputs/lengths differ by peer visibility; no equal-compute claim.',
        'scope': 'One historically exposed sanctions source family, assistant-checked factual blocks, hypothetical resource proposal and adaptive development; no sealed OOD, native-vote or autonomous trained-conversation claim.'
    }


def build(stage):
    from transformers import AutoTokenizer
    factual, parents = facts()
    shared = ROOT / 'data/prepared' / (NAME + '-initial')
    if stage != 'initial':
        assert shared.exists()
        raw = json.loads((shared / 'protocol.json').read_text())
        assert raw['proposal'] == PROPOSAL and raw['initial_task'] == TASK and raw['revision_task'] == REVISION
    pack = shared if stage == 'initial' else ROOT / 'data/prepared' / (NAME + '-' + stage)
    assert not pack.exists(), 'Use fresh packs; never overwrite a frozen pack'
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-brazil-application-fit-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    history, links = {}, []
    if stage != 'initial':
        base = ROOT / 'runs/aurora-sanctions-interaction-initial-base-20261007-v1'
        rr, ii = json.loads((base / 'run.json').read_text()), json.loads((base / 'inspection.json').read_text())
        assert rr['status'] == 'completed' and ii['all_outputs_read_complete'] and ii['transcript_sha256'] == sha256(base / 'transcript.jsonl')
        base_pack = ROOT / rr['config']['pack']
        countries = {c['id']: c['country_iso3'] for c in read_jsonl(base_pack / 'cases.jsonl')}
        for row in read_jsonl(base / 'transcript.jsonl'):
            history[countries[row['id']]] = row['output']
        assert set(history) == {'IND', 'BRA'}
        links = [{'run': str(base.relative_to(ROOT)), 'run_sha256': sha256(base / 'run.json'),
                  'transcript_sha256': sha256(base / 'transcript.jsonl'), 'inspection_sha256': sha256(base / 'inspection.json')}]
    cases = []
    for country in ['IND', 'BRA']:
        other = 'BRA' if country == 'IND' else 'IND'
        role = 'India, national Council representative (not the procedural chair)' if country == 'IND' else 'Brazil, De Almeida Filho, national Council representative'
        user = (f'ASSIGNED COUNTRY/ROLE/DATE: {role}, 9 December 2022, S/PV.9214.\n\n'
                + 'SOURCE-CHECKED NATIONAL FACTS (same-assistant-curated documentary facts only, no teacher decisions):\n'
                + '\n\n'.join(k + '\n' + factual[k] for k in ['IND', 'BRA'])
                + '\n\nSHARED HYPOTHETICAL PROPOSAL:\n' + PROPOSAL + '\n\nTASK:\n' + TASK)
        if stage != 'initial':
            user += '\n\nSTARTING DRAFT FOR YOUR ASSIGNED ROLE (actual stored base-model analysis, not an official national statement):\n' + history[country]
            if stage == 'peer':
                user += '\n\nPEER DRAFT FOR ' + other + ' (actual stored base-model analysis; not government authority):\n' + history[other]
            user += '\n\nREVISION TASK:\n' + REVISION
        prompt = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]
        ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(ids) + 2048 <= 8192
        cases.append({'id': f'sanctions-H1-{country}-{stage}', 'country_iso3': country, 'family': 'sanctions-9214',
                      'condition': stage, 'prompt': prompt, 'input_ids': ids})
    pack.mkdir(parents=True)
    shutil.copy2(__file__, pack / 'builder-code.py')
    write_jsonl(pack / 'cases.jsonl', cases)
    write_json(pack / 'criteria.json', criteria())
    write_json(pack / 'protocol.json', {'proposal': PROPOSAL, 'initial_task': TASK, 'revision_task': REVISION,
               'planned_max_model_outputs': 12, 'new_optimizer_steps': 0, 'conditions': ['initial', 'seed', 'peer'],
               'weight_arms': ['base', 'paired256'], 'common_seeds': 'Actual base initials after inspection; identical seed texts across weights.',
               'decisions': 'Inspect every run before another; choose further fitting or source expansion from observed failures, not prequeue.'})
    source = json.loads((ROOT / 'data/raw/source-plan-grounding-20261002-v1/statements.json').read_text())
    write_json(pack / 'full-primary-spans.json', {k: source[k] for k in ['IND', 'BRA']})
    write_json(pack / 'provenance.json', {'factual_blocks': parents, 'history_sources': links,
               'primary_path': 'data/raw/source-plan-grounding-20261002-v1/statements.json',
               'primary_sha256': sha256(ROOT / 'data/raw/source-plan-grounding-20261002-v1/statements.json'),
               'source_facts_origin': 'same root assistant curated; no separate teacher API transcript or human reviewer', 'separate_source_reader_outputs_used': False, 'teacher_decisions_in_inputs': False,
               'independent_review_complete': False})
    write_json(pack / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
               'files_sha256': {p.name: sha256(p) for p in pack.iterdir() if p.is_file()},
               'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 2,
               'source_scope': criteria()['scope']})
    for mode in ['base', 'adapter']:
        conf = {k: cfg[k] for k in ['model', 'revision', 'model_path', 'runtime_path', 'runtime_pins', 'seed', 'max_length', 'chat_template_kwargs', 'generation_max_new_tokens']}
        conf.update(kind='source-faithful-common-seed-interaction-v1', pack=str(pack.relative_to(ROOT)),
                    max_steps=0, training_examples=0, eval_cases=2, stage=stage, task_max_words=180,
                    authorization='User authorizes recursive informative source-faithful persona and interaction experiments.')
        if mode == 'adapter':
            adapter = ROOT / 'runs/aurora-paired-brazil-application-fit-20261007-v1/adapter'
            conf.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
                        adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
        write_json(ROOT / 'configs/posttraining' / f'qwen35-sanctions-interaction-{stage}-{mode}-20261007-v1.json', conf)
    print(json.dumps({'pack': str(pack), 'manifest_sha256': sha256(pack / 'manifest.json'),
                      'cases': [(c['id'], len(c['input_ids'])) for c in cases]}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=['initial', 'seed', 'peer'], required=True)
    build(p.parse_args().stage)
