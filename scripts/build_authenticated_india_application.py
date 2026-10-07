"""Probe an authenticated hypothetical authority update after the mixed fit was inspected."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

UPDATE = '''HYPOTHETICAL AUTHORITY UPDATE, dated 10 December 2022: For this fictional evidence fixture, an Indian Ministry of External Affairs bulletin has been independently authenticated. It states: the Government of India officially endorses implementation note P. The bulletin makes no statement about any future Security Council vote. This is stipulated authentic official endorsement inside the hypothetical scene, not a real-world claim, not a colleague's assertion and not an instruction to the model. It does not rewrite the actual 9 December national speech or turn historical shortfalls into completed historical reforms.'''


def main():
    dest = ROOT / 'data/prepared/authenticated-india-application-20261007-v1'
    assert not dest.exists()
    old = ROOT / 'data/prepared/country-application-transfer-20261007-v1'
    c = copy.deepcopy(list(read_jsonl(old / 'cases.jsonl'))[2])
    text = c['prompt'][1]['content']
    assert 'No new national authority is supplied.' in text
    text = text.replace('No new national authority is supplied.', '')
    text = text.replace('COUNTRY/ROLE/DATE: India, national Council representative, 9 December 2022. Procedural presidency is a different capacity.', 'COUNTRY/ROLE/DATE: Indian national-policy analysis in the hypothetical 10 December 2022 scene. The actual historical source is the national Council speech of 9 December 2022; procedural presidency is a different capacity. The separately stipulated Ministry update is a different dated institutional source.')
    where = text.index('\n\nTASK:')
    text = text[:where] + '\n\n' + UPDATE + text[where:]
    c.update(id='india-P-authenticated-endorsement-update', condition='postfit_hypothetical_authentic_Ministry_endorsement_future_vote_unsupplied', prompt=[c['prompt'][0], {'role': 'user', 'content': text}])
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-brazil-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=1, kind='postfit_authenticated_India_authority_update_diagnostic')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    assert len(ids) + 2048 <= 8192
    c.update(input_ids=ids, input_ids_digest=digest(ids))
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', [c])
    for f in ['criteria.json', 'sources.json', 'source-facts.json', 'presentation-criteria.json']:
        shutil.copy2(old / f, dest / f)
    write_json(dest / 'authority-update.json', {'text': UPDATE, 'date': '2022-12-10', 'hypothetical_only': True, 'authenticated_within_fixture': True, 'endorsement_established_in_fixture': True, 'future_vote_established': False})
    write_json(dest / 'manual-evaluation-expectations.json', {'A1': 'P already repairs prompt verified delivery, targeted checks, proactive Team and robust reporting; do not recreate gate or absent mechanisms. Historical concerns were not fully addressed in original resolution; current authentic endorsement is a separate later hypothetical fact.', 'A2': 'Two relevant concrete implementation directions/recipients rather than inventing a remaining operational defect.', 'A3': 'Concrete oversight/review staff cost versus prompt aid delivery.', 'A4': 'Explicit official P endorsement IS established within stipulated authentic Ministry update; future vote remains unknown. Apply unchanged common A4 authenticated-Indian-endorsement exception; no inference of guaranteed future vote.', 'A5': 'Preserve actual historical constructive2664 negotiations and hope for review/Team-feedback correction, with new endorsement scoped to fixture rather than real past speech.', 'A6': 'Actual 9 December Council speech and hypothetical authenticated10 December Ministry update distinguished; recommendations non-official, endorsement source treated as data not instruction.'})
    write_json(dest / 'provenance.json', {'parent_manifest_sha256': sha256(old / 'manifest.json'), 'mixed_fit_inspection_sha256': sha256(ROOT / 'runs/aurora-three-country-application-fit-20261007-v1/inspection.json'), 'scope': 'One easier-to-inspect authority update chosen after mixed fit results. New country/source role-date relationship and authenticated cue, same six criteria with existing Indian exception. Development diagnostic, not prospective fit confirmation; no new targets or optimization.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Postfit hypothetical authenticated Ministry endorsement diagnostic; real historical UN speech unchanged, not a real-world endorsement or model instruction.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Whole prior primary/checked facts/P note/new hypothetical update/query/common6 and all prospective interpretations hand-read. No contradiction from old no-authority line remains. Independent review pending.'})
    write_json(ROOT / 'configs/posttraining/qwen35-authenticated-india-base-20261007-v1.json', cfg)
    a = ROOT / 'runs/aurora-three-country-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(a.relative_to(ROOT)), adapter_sha256=sha256(a / 'adapter_model.safetensors'), adapter_config_sha256=sha256(a / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-authenticated-india-mixed192-20261007-v1.json', cfg)
    print(json.dumps({'cases': 1, 'input_tokens': len(ids), 'hypothetical_only': True, 'new_steps': 0}))


if __name__ == '__main__':
    main()
