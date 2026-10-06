"""Freeze one actual-error preference pair and five inspected writer checks."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

TARGET = '''France's Mr. Delattre and the UK's Lord Ahmad welcomed resolution 2467 on 23 April 2019 while criticizing the omitted sexual and reproductive health language. Welcoming adoption does not endorse those omissions. Both prioritize survivor-centred access to comprehensive sexual and reproductive health care.

France explicitly defends women's bodily autonomy and the right to terminate pregnancies resulting from conflict-related sexual violence that women and girls did not choose. France will maintain full care and rights in every context and continue promoting this approach in the Council, other UN bodies and elsewhere. It condemns veto threats and says the reproductive-health provisions in paragraph 10 of resolution 1889 and paragraph 19 of resolution 2106 remain within the reaffirmed framework for collective action.

The UK recognizes civil society's important role and the disproportionate impact on women and girls. It says further steps are needed for true justice and accountability and promises continuing support for survivors' sexual and reproductive health care worldwide. That specific further-work assessment belongs to the UK statement; France's explicit pregnancy-termination statement is not explicit in the bounded UK speech. These distinctions do not establish opposing care policies.

Analytical assessment: the hypothetical conviction gate and omitted comprehensive services conflict with these care priorities. Revise the proposal to provide care immediately, including pregnancy-choice support, while arranging consent-based referrals and accountability work in parallel. This avoids withholding care while investigations and proceedings take time, without abandoning accountability. These are proposed implementation steps, not recorded national concessions or new official conditions. Neither supplied statement guarantees endorsement of a particular future Council text or vote; that uncertainty does not erase the real continuing-care promises.'''

def main():
    from transformers import AutoTokenizer
    out = ROOT / 'data/prepared/factual-anchor-20261006-v1'
    if out.exists(): raise ValueError('Fresh pack required')
    bridge = ROOT / 'data/prepared/country-source-bridge-20261006-v1'
    selected = ROOT / 'runs/aurora-country-source-bridge-adapter-20261006-v1'
    review = json.loads((selected / 'inspection.json').read_text())
    assert review['all_outputs_read_complete'] and review['transcript_sha256'] == sha256(selected / 'transcript.jsonl')
    exact = list(read_jsonl(bridge / 'cases.jsonl'))[0]
    raw = list(read_jsonl(ROOT / 'data/prepared/native-reasoning-20261006-v1/cases.jsonl'))[0]
    changed = {**exact, 'id': 'wps-card-reworded', 'scenario': 'same_event_changed_instruction',
               'prompt': [*exact['prompt'][:-1], {**exact['prompt'][-1], 'content': exact['prompt'][-1]['content'] + '\n\nExpress the analysis in your own wording. Keep country-specific facts assigned to their original speaker, and preserve the distinction between a continuing care promise, an analytical proposal and an unknown future vote.'}]}
    mali = {r['id']: r for r in read_jsonl(ROOT / 'data/prepared/coverage-objective-20261003-v1/cases.jsonl')}
    cases = [{**exact, 'id': 'wps-card-exact', 'family': 'wps', 'condition': 'exact_fitting_input'},
             {**raw, 'family': 'wps', 'condition': 'same_event_without_card'},
             {**changed, 'family': 'wps', 'condition': 'changed_wording'},
             *[{**mali[k], 'family': 'mali', 'condition': condition} for k, condition in
               [('mali-gbr-pressure', 'outside_fitting_raw'), ('mali-gbr-checked-plan', 'outside_fitting_checked_plan')]]]
    negative = list(read_jsonl(selected / 'transcript.jsonl'))[0]['output']
    pair = {'prompt': exact['prompt'], 'chosen': [{'role': 'assistant', 'content': TARGET}],
            'rejected': [{'role': 'assistant', 'content': negative}], 'chat_template_kwargs': {'enable_thinking': False}}
    config = json.loads((ROOT / 'configs/posttraining/qwen35-country-source-bridge-20261006-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
    prefix = tok.apply_chat_template(pair['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **pair['chat_template_kwargs'])
    audit = {'id': 'wps-card-pair', 'pair_sha256': digest(pair), 'prompt_ids': prefix}
    for key in ('chosen', 'rejected'):
        full = tok.apply_chat_template(pair['prompt'] + pair[key], tokenize=True, return_dict=False, **pair['chat_template_kwargs'])
        assert full[:len(prefix)] == prefix and len(full) <= config['max_length']
        audit[key + '_ids'] = full[len(prefix):]
    assert len(TARGET.split()) <= 300 and negative != TARGET
    for c in cases:
        c['input_ids'] = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
        assert len(c['input_ids']) + config['generation_max_new_tokens'] <= config['max_length']
    out.mkdir()
    write_jsonl(out / 'pairs.jsonl', [pair]); write_jsonl(out / 'pair-audit.jsonl', [audit]); write_jsonl(out / 'cases.jsonl', cases)
    for name in ('wps-statements.json', 'source-proof.json', 'selected-card.txt', 'repairs.json'):
        (out / name).write_bytes((bridge / name).read_bytes())
    mali_raw = ROOT / 'data/raw/coverage-objective-grounding-20261003-v1'
    (out / 'mali-statements.json').write_bytes((mali_raw / 'statements.json').read_bytes())
    criteria = json.loads((bridge / 'criteria.json').read_text())
    criteria['mali'] = json.loads((ROOT / 'data/prepared/coverage-objective-20261003-v1/criteria.json').read_text())['by_country']['GBR']
    write_json(out / 'criteria.json', criteria)
    proof = {f.name: sha256(f) for f in mali_raw.iterdir() if f.is_file()}
    write_json(out / 'mali-source-proof.json', {'raw_directory': str(mali_raw.relative_to(ROOT)), 'files_sha256': proof})
    (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
    write_json(out / 'target-audit.json', {'source_scope': 'Complete post-vote FRA/GBR speeches only; analyst scenario remains hypothetical.',
        'preferred_text': TARGET, 'words': len(TARGET.split()), 'author': 'same unblinded assistant; independent review pending',
        'national_units_checked': 24, 'source_guards_checked': 4, 'synthesis_checks_checked': 5,
        'checks': ['All required units present, no borrowed national claim.', 'Actual care promises retained with scope.',
                   'No office guessing, invented date, binding obligation or vote condition.', 'Specific pregnancy/framework facts attributed to France, justice/civil society to UK.',
                   'Care and accountability application labeled analysis; no evidence/conviction access gate.'],
        'negative_provenance': {'run': str(selected.relative_to(ROOT)), 'transcript_sha256': sha256(selected / 'transcript.jsonl'), 'inspection_sha256': sha256(selected / 'inspection.json')},
        'pair_difference_scope': 'Complete faithful answer versus actual19/24 writer error, not a single-span edit or isolated attribution-only contrast.',
        'all_selected_texts_read_complete': True})
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'question': 'Does one actual-error preference pair with chosen-NLL anchor repair given-card writing and transfer beyond that input?',
        'training_examples': 1, 'eval_cases': 5, 'parent_steps': 160, 'cumulative_steps_before': 414, 'training_authorized_for_this_pack': True,
        'decision': 'Inspect matched base/parent outputs, fit one32step DPO+chosen-NLL comparison, read all5answers before selecting any continuation. No sweep.',
        'source_scope': 'WPS now fitted; wording/raw tests are same-event development. Mali outside selected160step branch and this pair, historically exposed project development, not sealed OOD.',
        'files_sha256': {p.name: sha256(p) for p in out.iterdir() if p.is_file()}}
    write_json(out / 'manifest.json', manifest)
    write_json(out / 'manual-inspection.json', {'manifest_sha256': sha256(out / 'manifest.json'), 'all_selected_texts_read_complete': True,
        'reviewed_at': datetime.now(timezone.utc).isoformat(), 'texts_read': 'Both complete WPS sources and both complete Mali sources, complete edited card and10repairs, entire chosen/actual rejected answer, all5prompts and24WPS/14UKMali/source/synthesis criteria; repeated source bytes checked.',
        'reviewer': 'same unblinded assistant; independent review pending'})
    config.update(pack=str(out.relative_to(ROOT)), kind='one_actual_writer_error_dpo_with_chosen_nll', starting_adapter=config.pop('adapter'),
        starting_adapter_sha256=config.pop('adapter_sha256'), max_steps=32, gradient_accumulation_steps=1, learning_rate=5e-5,
        dpo_beta=0.1, dpo_loss_types=['sigmoid', 'sft'], dpo_loss_weights=[1.0, 1.0], disable_dropout=True,
        baseline_run='runs/aurora-factual-anchor-parent-20261006-v1',
        authorization='User requests recursive informative minimal country experiments, fully inspected data and results before scaling.')
    write_json(ROOT / 'configs/posttraining/qwen35-factual-anchor-20261006-v1.json', config)
    print(json.dumps({'target': TARGET, 'rejected_actual': negative, 'words': len(TARGET.split()),
        'pair_tokens': {k: len(v) for k,v in audit.items() if k.endswith('_ids')}, 'cases': [(c['id'],len(c['input_ids'])) for c in cases]}, indent=2))

if __name__ == '__main__': main()
