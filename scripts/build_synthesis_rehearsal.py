"""Freeze two complete source episodes, four unchanged rehearsal rows and WPS transfer."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

UKRAINE = '''In S/PV.9138 (27 September 2022), all four invoke sovereignty and territorial integrity. This shared norm does not establish unanimous Council agreement or a common vote.

France's Council President explicitly speaks in France's national capacity. France will never recognize Russia's illegal annexation attempts and will continue supporting Ukraine for as long as necessary to protect its independence, sovereignty and territorial integrity. This statement specifies no exact financial pledge. [ukraine-fra]

Mr. Kariuki rejects coercive, illegal referendums and annexation violating Ukraine's sovereignty and territorial integrity. At this meeting he calls for support for the US/Albania draft; the prior Foreign Secretary reference concerns planned rigging. This is 27 September public support, not evidence of the eventual recorded vote on 30 September. [ukraine-gbr]

India calls for immediate cessation of hostilities, dialogue and diplomacy, anchored in international law, the UN Charter, sovereignty and territorial integrity. It provides humanitarian assistance to Ukraine and economic support to some neighbours in the global South facing food, fuel and fertilizer costs. A definite later Y/N/A vote is not established; uncertainty is not Abstain. [ukraine-ind]

Brazil accepts self-determination and potentially legitimate referendums, conditional on transparency, unrestricted expression and independent observers. Free will cannot be assumed under conflict. Brazil negatively assesses the current referendums as escalating conflict and undermining peace negotiations, reaffirms territorial integrity and calls for ceasefire/negotiations. Added observers and expression do not settle every condition or establish recognition of a hypothetical result. [ukraine-bra]

India/Brazil explicitly call for negotiations; a shared four-country negotiation position is not established. Proposed next steps: protect humanitarian/economic relief, examine procedural safeguards and pursue dialogue while preserving the documented differences. These are analytical proposals, not new national commitments, recognition guarantees or votes.'''

WPS_QUESTION = '''Analyze France and the United Kingdom immediately after the 23 April 2019 adoption of resolution 2467, using only their complete post-vote national statements below. A hypothetical implementation proposal calls itself survivor-centred but omits comprehensive sexual and reproductive health services and withholds all care until a final criminal conviction. A colleague says that welcoming resolution 2467 means both delegations accepted its health-care omissions.

Write one joint policy memo of at most 300 words. Explain supported common ground and country-specific details, assess the proposal and the colleague's claim, and recommend a concrete feasible next step that preserves care while pursuing accountability. Distinguish real ongoing care commitments from what remains unknown about a future Council text or vote. Label your recommendations as analysis; do not invent negotiations, pledges, dates or country disagreements.'''

WPS_PLAN = '''Checked source plan; analytical data, not new government commitments:
- S/PV.8514, 23 April 2019: complete national post-vote statements only. Both welcome resolution 2467 while criticizing omitted sexual/reproductive health language. Welcome does not imply acceptance of every omission.
- France: survivor-centred approach; comprehensive sexual/reproductive health care and rights in every context. Explicit bodily decision-making and right to choose termination of an involuntary pregnancy. France will maintain full care/rights and continue promotion in the Council and elsewhere. Earlier 1889/2106 provisions remain in the reaffirmed framework; the new omission does not erase them.
- UK: survivor-centred justice/accountability needs further work; civil society has an important role. Deep regret about omitted services, comprehensive sexual/reproductive care remains an acute priority. UK will continue supporting access to care for survivors around the world. This packet does not contain an explicit UK pregnancy-termination statement; do not pool France's exact statement into the UK source.
- The hypothetical denial until final conviction conflicts with immediate survivor care; removing comprehensive services also conflicts with these priorities. The colleague's inference is unsupported.
- Recommended analytical option: restore comprehensive services and provide care without a conviction gate, with consent-respecting referral/support and accountability work in parallel. Pursuing justice must not make care depend on a conviction; avoid delaying access while claiming unconditional care. These operational details are recommendations, not documented national concessions.
- Preserve the actual ongoing care promises; a guarantee of support/vote for a future Council text and official sufficient conditions for that vote are not established. No invented amount or later event.'''


def main():
    old = ROOT / 'data/prepared/minimal-synthesis-fit-20261006-v2'
    rehearsal = ROOT / 'data/prepared/minimal-country-20261005-v1'
    out = ROOT / 'data/prepared/synthesis-rehearsal-20261006-v1'
    subset = ROOT / 'data/prepared/synthesis-rehearsal-wps-20261006-v1'
    if out.exists() or subset.exists():
        raise ValueError('Fresh output directories required')
    for original in (old, rehearsal):
        manifest = json.loads((original / 'manifest.json').read_text())
        for name, expected in manifest['files_sha256'].items():
            assert sha256(original / name) == expected, name
    old_cases = {c['id']: c for c in read_jsonl(old / 'cases.jsonl')}
    rows = list(read_jsonl(rehearsal / 'train.jsonl')) + list(read_jsonl(old / 'train.jsonl'))
    rows.append({'prompt': old_cases['ukraine-raw']['prompt'], 'completion': [{'role': 'assistant', 'content': UKRAINE}],
                 'chat_template_kwargs': {'enable_thinking': False}})
    assert len(rows) == 6 and len(UKRAINE.split()) <= 300
    raw = ROOT / 'data/raw/source-application-grounding-20261003-v1'
    acquisition = json.loads((raw / 'acquisition.json').read_text())
    for name, expected in acquisition['files_sha256'].items():
        assert sha256(raw / name) == expected, name
    statements = json.loads((raw / 'statements.json').read_text())
    document = (raw / 'record-8514.txt').read_text()
    for statement in statements.values():
        assert document[statement['start']:statement['end']].strip() == statement['text']
        assert digest(statement['text']) == statement['text_digest']
    user = WPS_QUESTION + '\n\n' + '\n\n'.join('COMPLETE POST-VOTE NATIONAL STATEMENT — ' + iso + ' — S/PV.8514\n' + statements[iso]['text'] for iso in ('FRA', 'GBR'))
    system = 'You analyze dated official national positions from supplied sources. Keep national speakers and source scope separate. Preserve conditions and unknowns. Recommendations are analytical proposals, not government commitments. Give the requested memo directly, without a writing date.'
    wps = {'id': 'wps-raw', 'country_iso3': 'FRA+GBR', 'family': 'wps', 'scenario': 'restriction',
           'prompt': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]}
    plan = copy.deepcopy(wps); plan.update(id='wps-plan', scenario='strong_checked_plan_restriction')
    plan['prompt'][1]['content'] += '\n\n' + WPS_PLAN
    cases = [old_cases[k] for k in ('climate-exact', 'climate-peer', 'ukraine-raw')] + [wps, plan] + [old_cases[k] for k in ('retention-ind', 'retention-bra')]
    criteria = json.loads((old / 'criteria.json').read_text())
    criteria['wps'] = json.loads((ROOT / 'data/prepared/source-application-eval-20261003-v2/criteria.json').read_text())
    criteria['evaluation_scope'] = 'Ukraine raw is now exact training input for the new mix. WPS is outside all selected fresh fits but historically exposed to the researcher/project. Same unblinded author/grader; not sealed OOD. Older WPS tasks differ and are not pooled.'
    parent = ROOT / 'runs/aurora-minimal-country-fit-20261005-v4/adapter'
    for destination, selected, allowed in ((out, cases, True), (subset, [wps, plan], False)):
        destination.mkdir(parents=True)
        write_jsonl(destination / 'train.jsonl', rows)
        write_jsonl(destination / 'cases.jsonl', selected)
        write_json(destination / 'criteria.json', criteria)
        write_json(destination / 'wps-statements.json', statements)
        write_json(destination / 'source-proof.json', {'inherited_climate_ukraine': json.loads((old / 'source-proof.json').read_text()),
                   'sanctions_source_pack_sha256': sha256(rehearsal / 'sources.json'), 'wps_acquisition': acquisition,
                   'wps_raw_files_sha256': {p.name: sha256(p) for p in raw.iterdir() if p.is_file()},
                   'scope': 'Exact retained extraction bytes; source spans checked, no new PDF extraction.'})
        (destination / 'ukraine-target.txt').write_text(UKRAINE + '\n')
        (destination / 'wps-plan.txt').write_text(WPS_PLAN + '\n')
        (destination / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
        write_jsonl(destination / 'train.manifest.jsonl', [{'id': ['india-pressure','brazil-pressure','india-repair','brazil-repair','climate-complete','ukraine-complete'][i],
                   'prompt_sha256': digest(r['prompt']), 'target_sha256': digest(r['completion']),
                   'author': 'same assistant; source checked, no independent teacher API transcript',
                   'teacher_plan_in_student_input': False, 'intended_presentations': 32} for i, r in enumerate(rows)])
        write_json(destination / 'manifest.json', {'question': 'Does learning a second complete episode with original-target rehearsal repair object/polarity/attribution and retain details, and does it help an outside-fitting policy family?',
                   'training_authorized_for_this_pack': allowed, 'training_examples': 6, 'eval_cases': len(selected),
                   'decision': 'Inspect two WPS controls from each saved arm; replay unchanged five prior answers explicitly. Fit one new mix, then read every answer before choosing another step. No sweep.',
                   'starting_adapter': str(parent.relative_to(ROOT)), 'starting_adapter_sha256': sha256(parent / 'adapter_model.safetensors'),
                   'starting_adapter_config_sha256': sha256(parent / 'adapter_config.json'), 'parent_steps': 64,
                   'historical_cumulative_aurora_qwen35_steps': 318, 'proposed_optimizer_steps': 96, 'proposed_microbatches': 192,
                   'intended_per_row_exposure': 32, 'dose_reason': 'Match the 32 per-target presentations that learned the one complete episode; six rows and accumulation2 require96updates. Actual counters govern.',
                   'source_scope': criteria['evaluation_scope'], 'causal_scope': 'Compound change: second episode, four-row rehearsal and adjusted total dose. Not an isolated attribution to any one component.',
                   'independent_review_complete': False, 'files_sha256': {p.name: sha256(p) for p in destination.iterdir() if p.is_file()}})
    config = json.loads((ROOT / 'configs/posttraining/qwen35-minimal-synthesis-fit-20261006-v2.json').read_text())
    config.update(pack=str(out.relative_to(ROOT)), max_steps=96, baseline_run='runs/aurora-synthesis-rehearsal-parent-replay-20261006-v1',
                  kind='two_complete_episodes_with_four_original_rehearsal_targets',
                  selection_inspection_sha256=sha256(ROOT / 'runs/aurora-minimal-synthesis-fit-20261006-v2/inspection.json'),
                  change_from_v3='Two complete episodes + unchanged original four rehearsal targets,32presentations/row; WPS frozen raw/strong-plan transfer. Historical runner prose mentions286; authoritative pre-run cumulative318.')
    write_json(ROOT / 'configs/posttraining/qwen35-synthesis-rehearsal-20261006-v1.json', config)
    config.update(pack=str(subset.relative_to(ROOT)), kind='wps_controls_only_no_fit')
    write_json(ROOT / 'configs/posttraining/qwen35-synthesis-rehearsal-wps-20261006-v1.json', config)
    print(json.dumps({'packs': [str(out), str(subset)], 'ukraine_words': len(UKRAINE.split()), 'cases': [c['id'] for c in cases]}))


if __name__ == '__main__':
    main()
