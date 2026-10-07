"""Bind audited long-plan training inputs and prospective Libya realization controls."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

LIBYA_PLANS = {
    'BRA': '''Documented source points:
- França Danese speaks for Brazil at the Council's ICC Libya briefing on 8 November 2023, thanking Khan for his twenty-sixth report and welcoming Libya's representative. Zhang Jun chairs; Khan is the Prosecutor. This national speech supplies no meeting vote.
- Complementarity is central: States have the primary duty to exercise criminal jurisdiction over serious crimes. The ICC acts only when the State concerned is unable or unwilling to perform that duty; cooperation does not erase this national primacy.
- Brazil welcomes stronger Office cooperation with Libyan authorities and a positive trajectory. Resolution 1970 distinguishes non-parties' lack of obligations under the Rome Statute from the Council's Chapter VII requirement that Libyan authorities cooperate fully. It also urges all States and regional and international organizations to cooperate.
- State-party cooperation is vital for this treaty-based Court, which has no enforcement instruments of its own and relies on States. Cooperation requests must be consistent with the Rome Statute and relevant Council resolutions.
- Justice for victims, rather than politicization, should guide accountability. Brazil welcomes empowerment of victims, witnesses and affected communities both inside and outside Libya, and encourages further engagement with victims and their representatives.
- All victims of the most serious crimes deserve equal treatment regardless of the situation investigated, avoiding selective treatment and double standards.
- There have been no judgments in the Libya situation yet. Brazil nonetheless welcomes evidence collection and investigative progress and requests additional transparent information about the four key lines of inquiry.
- Brazil expects justice and accountability under complementarity and hopes fruitful Office–Libya cooperation will foster a culture of justice. Its own speech gives no Tripoli-office opening date, French funding commitment or UN-versus-parties budget split.

Analytical decisions:
- Retain Q's national-justice provision, documentation, visas, technical cooperation and protected victim/community channels as present repairs. Do not describe these as absent.
- Correct the false completed-judgment claim and selective-victim approach. Non-party Statute status cannot cancel the expressly required Libyan cooperation. Brazil's actual cooperation hopes remain; a separate budget approval is not a stated condition for them. Q's already-open Tripoli claim and specific excluded-crime list are not established by this Brazilian span; do not borrow the French particulars.
- Recommend a coordinated national–Office evidence and assistance-request channel consistent with the applicable legal framework, plus protected engagement with victim representatives inside and outside Libya. Seek transparent progress reports on each inquiry, distinguishing evidence, prosecutions and judgments.
- Protective verification and coordination consume staff time and can slow collection compared with unprotected rapid gathering; preserve safe access and equal treatment while managing that cost.

Authority:
- The historical speech does not officially endorse every Q element or guarantee any future Council vote. These operational recommendations are analysis. That absence does not revoke Brazil's real cooperation hopes or commitment to justice.''',
    'FRA': '''Documented source points:
- Dime Labille speaks nationally for France on 8 November 2023, thanking Khan for his twenty-sixth Libya report and welcoming Libya's representative. Zhang Jun chairs, Khan is the Prosecutor, and this briefing supplies no meeting vote. France defends victim justice, the rules-based order and Rome Statute integrity, condemns the cyberattack, and supports the Court and staff.
- France will continue political, operational, human and financial support. It takes note of the Office's requested budget increase to address risks in the April 2022 strategy, introduced in the twenty-third report. No new amount or appropriation is approved by this statement.
- France welcomes progress in four investigative lines. The 2014–2020 operations inquiry is nearing completion; the Office expects a potential roadmap in its next report under resolution 1970. Neither all activities nor Court judgments are declared complete.
- Active national–Court cooperation is essential. September floods affected Office missions; France offers condolences and support while welcoming continued cooperation. Detention and migrant-crime progress includes national arrests and prosecutions assisted by Office information, evidence and guidelines, not completed ICC judgments.
- France encourages document access, technical-authority cooperation, visas and assistance responses, stronger joint-team missions and progress towards a Tripoli liaison office in 2024. The French original places the newly appointed ambassador in the Netherlands; nationality is not established. The office is not described as already operational.
- France welcomes closer engagement with victims, witnesses and affected communities. It highlights a regional civil-society seminar on guidelines for documenting international crimes and human-rights violations, and encourages intensified exchanges.
- All serious crimes since 2011, including Daesh crimes and crimes against migrants and refugees, must be investigated and prosecuted. International, regional and civil-society assistance, coordinated third-State and agency investigations, UNSMIL and the Independent Fact-Finding Mission support that work.
- France urges a sovereign, united, stable and democratic Libya for national and regional stability, retaining real continuing Court support without an invented future-vote promise.

Analytical decisions:
- Retain Q's national-justice, documentation, visa, technical-cooperation and protected-engagement provisions as repairs. Correct its claims of completed judgments/all activities and an already-open Tripoli office. Restore the excluded migrant, refugee and Daesh cases and equal victim coverage. Do not treat national proceedings as ICC verdicts.
- Reject the exception stopping required Libyan cooperation as incompatible with active cooperation. France's own span does not give Brazil's detailed non-party/Chapter VII legal explanation. Keep France's actual continuing support, including financial support, rather than conditioning it on a separate new budget approval.
- Recommend a coordinated document, visa and assistance-request workflow with the Office and national technical authorities, plus protected victim/community evidence channels and civil-society documentation exchanges. Track all four inquiry lines, distinguish their stages and plan the future liaison capacity without claiming it already exists.
- Protected verification, coordination and inclusive coverage require time and resources compared with quickly closing a narrower set of files; manage that cost without sacrificing safety or dropping serious crimes.

Authority:
- No official endorsement of every Q element or guaranteed future Council vote follows. The proposed workflows are analytical recommendations, while France's recorded ongoing Court support remains an actual commitment.''',
}


def main():
    draft = ROOT / 'data/prepared/compression-student-draft-20261006-v2'
    dest = ROOT / 'data/prepared/compression-checkpoint-20261006-v1'
    assert not dest.exists()
    dm = json.loads((draft / 'manifest.json').read_text())
    hand = json.loads((draft / 'manual-inspection.json').read_text())
    assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256'] == sha256(draft / 'manifest.json')
    for name, value in dm['files_sha256'].items():
        assert sha256(draft / name) == value
    prospective_path = ROOT / 'data/curation/compression-libya-prospective-20261006-v1.json'
    prospective = json.loads(prospective_path.read_text())
    raw = ROOT / prospective['source_directory']
    assert sha256(raw / 'statements.json') == prospective['source_sha256']
    assert sha256(raw / 'source-proof.json') == prospective['source_proof_sha256']
    assert sha256(raw / 'ambassador-adjudication.json') == prospective['ambassador_adjudication_sha256']
    source = json.loads((draft / 'sources.json').read_text())
    source['libya'] = json.loads((raw / 'statements.json').read_text())
    criteria = json.loads((draft / 'criteria.json').read_text())
    criteria['source_units']['libya'] = prospective['source_units']
    oldplan = ROOT / 'data/prepared/plan-input-fit-20261006-v1'
    icc_criteria = json.loads((oldplan / 'criteria.json').read_text())
    criteria['source_units']['icc'] = icc_criteria['source_units']['icc']
    source['icc'] = json.loads((oldplan / 'sources.json').read_text())['icc']
    sudan = ROOT / 'data/prepared/question-guided-plan-writer-20261006-v1'
    criteria['source_units']['sudan'] = json.loads((sudan / 'criteria.json').read_text())['source_units']['sudan']
    source['sudan'] = json.loads((sudan / 'source.json').read_text())
    cases = list(read_jsonl(draft / 'cases.jsonl'))
    request = cases[0]['prompt'][1]['content'].split('\n\n')[2]
    contract = cases[0]['prompt'][1]['content'].split('\n\nREALIZATION CONTRACT: ', 1)[1]
    for co, country in [('FRA', 'France'), ('BRA', 'Brazil')]:
        body = f'Assigned delegation: {country}.\n\n' + prospective['current_hypothetical_note'] + '\n\n' + request
        body += ('\n\nPUBLIC SOURCE ROLE METADATA: S/PV.9469, 8 November 2023. '
                 'Zhang Jun (China) chairs. Dime Labille (France) and França Danese (Brazil) speak nationally; '
                 'Khan is the ICC Prosecutor. No meeting vote is supplied. '
                 'French-original adjudication: the ambassador is appointed in the Netherlands; nationality is not stated.')
        body += f'\n\nCOMPLETE NATIONAL STATEMENT — {co}\n' + source['libya'][co]['text']
        for condition in ['raw', 'plan']:
            content = body
            if condition == 'plan':
                content += '\n\nSOURCE-CHECKED PLAN (same assistant assistance, not government authority):\n' + LIBYA_PLANS[co]
                content += '\n\nREALIZATION CONTRACT: ' + contract
            cases.append({'id': f'libya-{co.lower()}-{condition}', 'country_iso3': co, 'family': 'libya',
                          'condition': condition, 'prompt': [{'role': 'system', 'content':
                          f'You are a source-grounded national policy analyst for {country}, using its dated own national statement at the ICC briefing, distinct from prosecutor, chair and other countries.'},
                          {'role': 'user', 'content': content}]})
    ordinary = ROOT / 'data/prepared/ordinary-points-20261006-v2'
    cases.extend(copy.deepcopy(list(read_jsonl(ordinary / 'cases.jsonl'))))
    cases.extend(copy.deepcopy(list(read_jsonl(sudan / 'cases.jsonl'))))
    assert len(cases) == 14
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-plan-input-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    for c in cases:
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        if 'input_ids' in c:
            assert ids == c['input_ids']
        c.update(input_ids=ids, input_ids_digest=digest(ids))
        assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
    dest.mkdir(parents=True)
    for name in ['preferred-targets.json', 'curated-plans.json', 'actual-teacher-provenance.json', 'chosen-token-audit.jsonl']:
        shutil.copy2(draft / name, dest / name)
    write_jsonl(dest / 'cases.jsonl', cases)
    write_json(dest / 'criteria.json', criteria)
    write_json(dest / 'sources.json', source)
    write_json(dest / 'held-plans.json', {'author': 'same assistant; source checked, no independent teacher', 'plans': LIBYA_PLANS})
    shutil.copy2(prospective_path, dest / 'libya-prospective-criteria.json')
    presentation = json.loads((ordinary / 'presentation-criteria.json').read_text())
    presentation['usable_realization_pass'] = 'All case-specific content and universal units met, uncapped, no more than 300 ordinary English words and the three requested sections. Same-assistant annotation; no independent persona result.'
    write_json(dest / 'presentation-criteria.json', presentation)
    write_json(dest / 'provenance.json', {'scope': 'Eight unchanged targets, longer inspected plans; four frozen outside Libya cases plus two exact exposed controls. Fresh256 update comparison, same native chosen tokens. Given-content realization, not native decision prediction/persona/strong OOD.',
        'draft_manifest_sha256': sha256(draft / 'manifest.json'), 'prospective_source_criteria_sha256': sha256(prospective_path),
        'preferred_targets_sha256': sha256(draft / 'preferred-targets.json'), 'pair_ids': [c['id'] for c in cases[:8]],
        'exposed_control_packs': [str(ordinary.relative_to(ROOT)), str(sudan.relative_to(ROOT))],
        'plan_words': {co: len(plan.split()) for co, plan in LIBYA_PLANS.items()}})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {p.name: sha256(p) for p in dest.iterdir() if p.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 8, 'eval_cases': 14,
        'source_scope': 'Frozen compression controls; no fit before inspection of actual matching controls.'})
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='fresh_long_plan_compression_chosen_only',
               baseline_run='runs/aurora-compression-base-20261006-v1', comparison_run='runs/aurora-plan-input-fit-20261006-v1',
               preparation='reports/compression-fit-preparation-20261006-v1.json')
    write_json(ROOT / 'configs/posttraining/qwen35-compression-20261006-v1.json', cfg)
    basecfg = copy.deepcopy(cfg)
    basecfg.update(max_steps=0, training_examples=0)
    write_json(ROOT / 'configs/posttraining/qwen35-compression-base-20261006-v1.json', basecfg)
    print(json.dumps({'cases': len(cases), 'long_plan_words': {co: len(plan.split()) for co, plan in LIBYA_PLANS.items()},
                      'maximum_input_tokens': max(len(c['input_ids']) for c in cases), 'fitting_ready': False}))


if __name__ == '__main__':
    main()
