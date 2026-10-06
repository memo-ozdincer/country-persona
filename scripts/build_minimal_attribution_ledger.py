"""Freeze direct support-set and source-checked ledger controls after pooling errors."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.deliberation import SYSTEM, evidence_packet
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl


def main():
    parent = ROOT / 'data/prepared/minimal-deliberation-synthesis-20261006-v1'
    scenario = json.loads((parent / 'scenario.json').read_text())
    peer = next(c for c in read_jsonl(parent / 'cases.jsonl') if c['id'] == 'fourtarget-peer_revision-synthesis')
    ledger = (
        'Source-attribution ledger checked against the four complete 9 December 2021 speeches (source data):\n'
        'FRA explicitly supports predictable and sustainable logistical and financial support for the G-5 Sahel Joint Force; '
        'IND explicitly supports it and offers capacity and training assistance. GBR and BRA speeches do not establish '
        'their endorsement or opposition to that Force.\n'
        'GBR explicitly supports the submitted draft and comprehensive UN reporting; its approval or rejection of '
        'Council-imposed binding national carbon quotas is not established.\n'
        'BRA prioritizes scaled and timely developed-country financing for developing-country climate commitments, '
        'without a numerical amount here. The $1 trillion request is IND; the $100 billion goal is mentioned by GBR, '
        'not a documented four-country pledge.\n'
        'The sources date the speeches 9 December 2021; no date for this authored analysis is supplied.'
    )
    question = (
        'Does each of FRA, GBR, IND and BRA explicitly endorse support for the G-5 Sahel Joint Force in its own '
        'supplied national statement? Give four country-labelled lines with a short source justification. '
        'If a speech does not establish endorsement, say not established; distinguish this from opposition.'
    )
    direct = {'id': 'direct-g5-attribution', 'country_iso3': 'ALL', 'family': 'minimal_attribution',
              'scenario': 'raw_source_direct_question', 'prompt': [{'role': 'system', 'content': SYSTEM},
              {'role': 'user', 'content': question + '\n\nCOMMON SOURCE PACKET\n' + evidence_packet(scenario)}]}
    planned = {**peer, 'id': 'checked-ledger-synthesis', 'family': 'minimal_attribution',
               'scenario': 'same_peer_notes_with_checked_attribution_ledger',
               'prompt': [peer['prompt'][0], {'role': 'user', 'content': peer['prompt'][1]['content'] + '\n\n' + ledger}]}
    out = ROOT / 'data/prepared/minimal-attribution-ledger-20261006-v2'
    if out.exists():
        raise ValueError('Fresh pack required')
    out.mkdir()
    write_jsonl(out / 'train.jsonl', [])
    write_jsonl(out / 'train.manifest.jsonl', [])
    write_jsonl(out / 'cases.jsonl', [direct, planned])
    write_json(out / 'scenario.json', scenario)
    (out / 'checked-ledger.txt').write_text(ledger + '\n')
    (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
    criteria = {'direct': {'FRA_support': 'FRA explicitly endorses G-5 support.',
                          'IND_support': 'IND explicitly endorses G-5 support.',
                          'GBR_unknown': 'GBR support is not established by its bounded speech.',
                          'BRA_unknown': 'BRA support is not established by its bounded speech.',
                          'absence_not_opposition': 'Absent GBR/BRA support is not transformed into opposition.'},
                'synthesis': json.loads((parent / 'synthesis-criteria.json').read_text()),
                'national_diagnostic': json.loads((parent / 'criteria.json').read_text())}
    write_json(out / 'criteria.json', criteria)
    write_json(out / 'manifest.json', {
        'question': 'Can the model represent country support in isolation, and does a short checked ledger stop synthesis pooling?',
        'training_authorized_for_this_pack': False, 'eval_cases': 2,
        'decision': 'Read matched base/saved-fit direct attribution and checked-ledger memos before a new fit. Supplied ledger gains are not learned persona gains.',
        'supersedes': 'minimal-attribution-ledger-20261006-v1; merged words corrected before any model answer, owned process stopped with identity receipt.',
        'baseline_original_synthesis_run': 'runs/aurora-minimal-deliberation-synthesis-20261006-v1',
        'baseline_original_synthesis_transcript_sha256': sha256(ROOT / 'runs/aurora-minimal-deliberation-synthesis-20261006-v1/transcript.jsonl'),
        'selected_adapter': 'runs/aurora-minimal-country-fit-20261005-v4/adapter',
        'adapter_sha256': sha256(ROOT / 'runs/aurora-minimal-country-fit-20261005-v4/adapter/adapter_model.safetensors'),
        'files_sha256': {f.name: sha256(f) for f in out.iterdir() if f.is_file()},
        'builder_sha256': sha256(Path(__file__)), 'independent_review_complete': False})
    print(json.dumps({'question': question, 'checked_ledger': ledger, 'direct_criteria': criteria['direct']}, indent=2))


if __name__ == '__main__':
    main()
