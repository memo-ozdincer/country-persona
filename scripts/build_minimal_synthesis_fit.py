"""Freeze one full climate synthesis target, Ukraine transfer and sanctions retention."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.deliberation import make_case, validate_scenario
from country_persona.eval_evidence import normalize
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

TARGET = '''In S/PV.8923 (9 December 2021), all four acknowledge climate harms; this does not establish agreement on a Council climate mandate.

France supports Council anticipation, assessment and prevention. Armed forces and peacekeepers alone are insufficient: understand reinforcing climate/crisis links and strengthen state/population resilience. Complementary measures include the Great Green Wall and predictable, sustainable financial/logistical support for the G-5 Sahel Joint Force. [climate-fra]

The UK supports comprehensive UN climate-security reporting, a Council role and the submitted draft. It calls for meaningful participation of women and girls. Council-imposed binding carbon-quota approval is not established. [climate-gbr]

India acknowledges climate exacerbates conflicts; the analyst's denial claim is wrong. It prefers inclusive, consensus-based UNFCCC/COP processes with developing-country participation, opposes an alternative Council platform and warns against oversimplifying conflict causes. India cites contested scientific evidence about direct climate/security equivalence; that argument is attributed, not a settled finding. It requests sustainable resources, training and logistics for the Joint Force. [climate-ind]

Brazil acknowledges drought/resource loss, tensions and migration. It prefers the inclusive UNFCCC mandate, avoiding duplication and Council reallocation. It prioritizes scaled, timely developed-country finance for developing countries' existing commitments and enhanced climate action. [climate-bra]

Only France and India's statements establish G-5 support; UK/Brazil endorsement or opposition is unknown. Proposed next steps: assess risks within existing mandates, track financing delivery and consider a UN climate-security report alongside the regional assistance supported by France/India. These are analytical options, not government commitments or a negotiated agreement.'''

UKRAINE_PLAN = '''Checked source plan (data, not new government commitments), S/PV.9138, 27 September 2022:
- Common ground is sovereignty/territorial integrity and concern about the conflict's harms; do not infer unanimous Council agreement or a shared vote.
- FRA: the Council President explicitly switches to France's national capacity. France rejects recognition of Russia's illegal annexation attempts and will continue support as long as necessary for Ukraine's independence, sovereignty and territorial integrity. No exact financial pledge or assistance type is specified in this bounded statement.
- GBR: referendums are illegal, illegitimate and coercive, violating Ukraine's sovereignty/integrity. UK calls for support for the US/Albania draft at this meeting. That is a public position, not the later 30 September recorded vote.
- IND: immediate cessation of hostilities, dialogue/diplomacy, international law/UN Charter and sovereignty/integrity. It supplies humanitarian assistance to Ukraine and economic support to neighbours in the global South facing food, fuel and fertilizer costs. No definite later Y/N/A vote is established; uncertainty is not a historical Abstain.
- BRA: self-determination and potentially legitimate referendums, conditional on free will, transparency, unrestricted expression and independent observers. Free will cannot be assumed under conflict; the current referendums fail those conditions and worsen peace prospects. Territorial integrity and ceasefire/negotiations remain. Adding observers/expression in the hypothetical does not establish recognition or satisfy every condition.
- Proposed next steps can examine humanitarian/economic relief, procedural safeguards and dialogue; label them proposals. No amount, new concession, guarantee or negotiation is established.'''


def main():
    out = ROOT / 'data/prepared/minimal-synthesis-fit-20261006-v2'
    if out.exists():
        raise ValueError('Fresh pack required')
    parent = ROOT / 'data/prepared/deliberation-probe-20260928-v1'
    scenarios = {s['id']: s for s in read_jsonl(parent / 'scenarios.jsonl')}
    references = {r['scenario_id']: r for r in read_jsonl(parent / 'review.references.jsonl')}
    climate = scenarios['climate-policy-workshop-v1']; ukraine = scenarios['ukraine-policy-workshop-v1']
    proof = []
    for scenario in (climate, ukraine):
        validate_scenario(scenario)
        for e in scenario['evidence']:
            raw = ROOT / 'data/raw/eval-sources-20260927' / e['source_id']
            columns = json.loads(raw.with_suffix('.columns.json').read_text())
            document = '\n\n'.join(normalize(s['text']) for s in columns['sections'])
            if sha256(raw.with_suffix('.pdf')) != e['pdf_sha256'] or digest(document) != e['document_text_digest']:
                raise ValueError('Changed primary source/PDF or column-normalized document')
            if document[e['document_start']:e['document_end']].rstrip() != e['text']:
                raise ValueError('Changed complete national source span')
            proof.append({k: v for k, v in e.items() if k != 'text'})
    climate_case = make_case(climate, 'independent_revision', 'synthesis', 'ALL', [])
    ukraine_case = make_case(ukraine, 'independent_revision', 'synthesis', 'ALL', [])
    peer_pack = ROOT / 'data/prepared/minimal-deliberation-synthesis-20261006-v1'
    peer = next(c for c in read_jsonl(peer_pack / 'cases.jsonl') if c['id'] == 'fourtarget-peer_revision-synthesis')
    cases = [
        {'id': 'climate-exact', 'country_iso3': 'ALL', 'family': 'climate', 'scenario': 'exact_training_input',
         'prompt': climate_case['prompt'], 'original_case': climate_case},
        {**peer, 'id': 'climate-peer', 'family': 'climate', 'scenario': 'frozen_peer_note_transfer'},
        {'id': 'ukraine-raw', 'country_iso3': 'ALL', 'family': 'ukraine', 'scenario': 'raw_source_transfer',
         'prompt': ukraine_case['prompt'], 'original_case': ukraine_case},
        {'id': 'ukraine-plan', 'country_iso3': 'ALL', 'family': 'ukraine', 'scenario': 'strong_checked_plan_control',
         'prompt': [ukraine_case['prompt'][0], {'role': 'user', 'content': ukraine_case['prompt'][1]['content'] + '\n\n' + UKRAINE_PLAN}],
         'original_case': ukraine_case},
    ]
    retention = list(read_jsonl(ROOT / 'data/prepared/minimal-country-20261005-v1/cases.jsonl'))[:2]
    cases.extend([{**c, 'id': 'retention-' + c['country_iso3'].lower(), 'family': 'sanctions_retention'} for c in retention])
    if len(TARGET.split()) > 300:
        raise ValueError('Target exceeds original memo word allowance')
    row = {'prompt': climate_case['prompt'], 'completion': [{'role': 'assistant', 'content': TARGET}],
           'chat_template_kwargs': {'enable_thinking': False}}
    out.mkdir(parents=True)
    write_jsonl(out / 'train.jsonl', [row]); write_jsonl(out / 'cases.jsonl', cases)
    write_jsonl(out / 'train.manifest.jsonl', [{'id': 'one-complete-climate-memo', 'scenario_sha256': climate['scenario_sha256'],
               'prompt_sha256': digest(row['prompt']), 'target_sha256': digest(TARGET), 'word_count': len(TARGET.split()),
               'author': 'assistant source-audited complete answer; not an independent teacher API transcript',
               'source_ids': [e['id'] for e in climate['evidence']], 'teacher_plan_in_student_input': False}])
    (out / 'target.txt').write_text(TARGET + '\n'); (out / 'ukraine-plan.txt').write_text(UKRAINE_PLAN + '\n')
    write_json(out / 'scenarios.json', {'climate': climate, 'ukraine': ukraine})
    write_json(out / 'source-proof.json', proof)
    write_json(out / 'criteria.json', {'climate': references[climate['id']], 'ukraine': references[ukraine['id']],
               'retention': json.loads((ROOT / 'data/prepared/minimal-country-20261005-v1/criteria.json').read_text()),
               'extra_climate_source_checks': {'g5_scope': 'Only FRA/IND support established; GBR/BRA support and opposition unknown.',
                                              'numeric_country_scope': 'No unsupported finance amount or speaker pooling.',
                                              'writing_date_absent': 'Do not invent an analysis-writing date.'},
               'collective_scope_rule': 'Unqualified each/all/four/they applied to this group requires support in every national source. Named subgroups may differ. Source absence is not opposition. Preserve prior ambiguous grades.'})
    (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
    adapter = ROOT / 'runs/aurora-minimal-country-fit-20261005-v4/adapter'
    write_json(out / 'manifest.json', {'question': 'Can one fully covered synthesis target added to the working four-example fit repair composition without losing outside-family or original country behavior?',
               'training_authorized_for_this_pack': True, 'training_examples': 1, 'eval_cases': 6,
               'supersedes': 'v1 omitted per-row enable_thinking=False; actual trainer-token guard stopped before optimization. Target text and all six evaluation prompts are unchanged.',
               'decision': 'Read base and saved-parent controls, fit once, verify the exact target was learned, inspect all six outputs before another run. No sweep.',
               'starting_adapter': str(adapter.relative_to(ROOT)), 'starting_adapter_sha256': sha256(adapter / 'adapter_model.safetensors'),
               'starting_adapter_config_sha256': sha256(adapter / 'adapter_config.json'),
               'parent_steps': 64, 'historical_cumulative_aurora_qwen35_steps': 286,
               'source_scope': 'Climate now used for training; Ukraine outside this parent/new fit, but historically exposed in the project. Sanctions are retention controls. No sealed confirmation or native prediction.',
               'protocol_scope': 'Isolated source/notes synthesis calls, not a fresh full autonomous nine-call deliberation comparison. Parent peer histories are frozen, not regenerated after fitting.',
               'source_extraction': 'Existing column-normalized text and exact PDF hashes; not a fresh Poppler re-extraction.',
               'files_sha256': {f.name: sha256(f) for f in out.iterdir() if f.is_file()}, 'independent_review_complete': False})
    config = json.loads((ROOT / 'configs/posttraining/qwen35-minimal-country-20261005-v3.json').read_text())
    config.update(pack=str(out.relative_to(ROOT)), max_length=8192, generation_max_new_tokens=512, max_steps=32,
                  baseline_run='runs/aurora-minimal-synthesis-parent-replay-20261006-v2',
                  starting_adapter=str(adapter.relative_to(ROOT)), starting_adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
                  starting_adapter_config_sha256=sha256(adapter / 'adapter_config.json'), kind='one_complete_synthesis_target_warm_start',
                  change_from_v3='One complete source-only climate target; warm-start saved four-example adapter with new optimizer32steps. Frozen Ukraine raw/checked-plan comparison and two sanctions retention controls. Base/parent/fit use identical six prompts and512cap/8192context. v2 corrects only the missing per-row nonthinking template flag; controls are explicit token replays of actual v1 generations, with no new model calls.')
    write_json(ROOT / 'configs/posttraining/qwen35-minimal-synthesis-fit-20261006-v2.json', config)
    print(json.dumps({'pack': str(out), 'target_words': len(TARGET.split()), 'cases': [c['id'] for c in cases]}, indent=2))


if __name__ == '__main__':
    main()
