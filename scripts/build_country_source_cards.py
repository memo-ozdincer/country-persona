"""Freeze an intermediate source-card diagnostic before choosing another fit/synthesis."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl

REQUEST = '''Prepare two compact, separate source cards: France and the United Kingdom, immediately after the 23 April 2019 adoption of resolution 2467. Use only each delegation's complete post-vote statement below. The hypothetical implementation proposal calls itself survivor-centred but omits comprehensive sexual and reproductive health services and withholds all care until final criminal conviction. A colleague says welcoming resolution 2467 means accepting its health-care omissions.

For EACH country, give these seven labeled fields:
1. Speaker, national role and source date.
2. Resolution welcome and criticism: distinguish adoption from acceptance of omissions.
3. Care priority and what makes the approach survivor-centred.
4. Country-specific details: what this speaker says about pregnancy/bodily decisions, earlier resolutions and their continuing framework, civil society, and remaining justice/accountability work. If a detail is absent from this national statement, say it is not stated; do not borrow the other country's statement or treat absence as opposition.
5. Actual ongoing care/support/promotion commitment: retain its source scope and a short exact quote. Do not call every future commitment unknown.
6. Unknown future Council text/vote: separate absence of a guarantee from the real commitment in field5.
7. Application and proposed next step: assess both the current care-restriction proposal and the colleague's claim, then recommend a concrete feasible way to preserve care while pursuing accountability, without a conviction gate. Mark this as analytical recommendation, not a recorded national concession or vote condition.

Finish with two short lines identifying supported common ground and any source-supported differences. Do not invent disagreements, commitments, dates or negotiations. Return the cards directly; no word counting or joint memo is needed.'''

def main():
    from transformers import AutoTokenizer
    old = ROOT / 'data/prepared/native-reasoning-20261006-v1'
    out = ROOT / 'data/prepared/country-source-cards-20261006-v1'
    if out.exists(): raise ValueError('Fresh pack required')
    manifest = json.loads((old / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items(): assert sha256(old / name) == expected
    original = list(read_jsonl(old / 'cases.jsonl'))[0]
    source = original['prompt'][1]['content'].split('COMPLETE POST-VOTE NATIONAL STATEMENT', 1)[1]
    case = {**original, 'id': 'country-source-cards', 'scenario': 'explicit_per_country_extraction_application',
            'prompt': [original['prompt'][0], {'role': 'user', 'content': REQUEST + '\n\nCOMPLETE POST-VOTE NATIONAL STATEMENT' + source}]}
    out.mkdir()
    write_jsonl(out / 'cases.jsonl', [case])
    for name in ('criteria.json', 'wps-statements.json', 'source-proof.json'): (out / name).write_bytes((old / name).read_bytes())
    (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
    config = json.loads((ROOT / 'configs/posttraining/qwen35-native-reasoning-off-20261006-v1.json').read_text())
    tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
    ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
    assert len(ids) + 2048 <= config['max_length']
    new = {**manifest, 'question': 'Does explicit per-country source extraction/application preserve facts, attribution and real/unknown commitments before prose aggregation?',
           'decision': 'One base card answer, hand inspect, then matching saved adapter. Only after both inspections choose bridge synthesis, a minimal repair or another objective. No fit/sweep.',
           'planned_model_answers': 2, 'comparison_scope': 'Intermediate skill diagnostic: card layout plus explicit coverage questions and removal of300word memo quota. Not an isolated format effect or improvement on the original memo task.',
           'source_scope': 'Same exposed WPS event and unchanged complete national sources/24criteria. Outside selected fitting episodes, historically exposed; no sealed OOD.',
           'source_prompt_bytes_unchanged': True, 'preflight_input_tokens': len(ids),
           'selection_inspection_sha256': sha256(ROOT / 'runs/aurora-native-sampling-adapter-20261006-v2/inspection.json'),
           'files_sha256': {p.name: sha256(p) for p in out.iterdir() if p.is_file()}}
    new.pop('native_template_preflight', None)
    write_json(out / 'manifest.json', new)
    write_json(out / 'manual-inspection.json', {'manifest_sha256': sha256(out / 'manifest.json'), 'all_selected_texts_read_complete': True,
               'reviewed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': 'same unblinded assistant; independent review pending',
               'texts_read': 'Both full post-vote national sources, entire seven-field request/common-ground instruction, all24original national criteria/four source guards/five synthesis checks. No targets or teacher plans.',
               'comparison_read': 'Country cards explicitly request details, quotes and true-care/unknown-vote distinction; task changes are disclosed. Same model/runtime, nonthinking greedy2048cap.'})
    config.update(pack=str(out.relative_to(ROOT)), kind='intermediate_country_source_cards_no_training')
    write_json(ROOT / 'configs/posttraining/qwen35-country-source-cards-20261006-v1.json', config)
    print({'input_tokens': len(ids), 'new_training_steps': 0, 'case': case['id']})

if __name__ == '__main__': main()
