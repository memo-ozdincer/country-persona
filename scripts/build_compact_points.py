"""One hand-audited, readable compact plan; three existing-weight controls, zero fitting."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

COMPACT = '''Documented source points:
- Brazil's national speaker França Danese, 8 November 2023, thanks Khan's twenty-sixth Libya report and welcomes Libya's representative; no meeting vote.
- States have primary criminal jurisdiction; ICC acts when States are unable or unwilling.
- Brazil welcomes improved Office–Libya cooperation. Non-parties lack Statute obligations; resolution 1970 requires full Libyan cooperation under Chapter VII and urges all States and regional and international organizations to cooperate.
- Treaty Court needs State-party cooperation, lacks enforcement, relies on States; requests must meet Rome Statute and Council resolutions.
- Justice for victims over politicization; empower victims, witnesses and communities inside and outside Libya; engage victim representatives.
- Treat all serious-crime victims equally across situations; avoid selectivity and double standards.
- No Libya judgments yet; welcome evidence and investigative progress; seek transparent information on four inquiries.
- Expect justice and accountability under complementarity; hope fruitful Office–Libya cooperation builds justice culture. Own speech gives no Tripoli opening date, French funding commitment or UN versus parties funding split.

Analytical decisions:
- Retain Q's national justice, documents, visas, technical cooperation and protected channels. Correct false judgments and completion, selective victims and non-party cooperation exception. Real cooperation hope remains; no new budget-approval condition.
- Q's office and crime particulars are unestablished by own source; avoid French pooling.
- Recommend coordinated national–Office evidence and assistance workflow under applicable law, protected victim-representative engagement inside and outside Libya, and transparent progress reports distinguishing evidence, prosecutions and judgments.
- Verification, protection and coordination consume staff time and slow collection versus unprotected gathering; preserve safe access and equal treatment.

Authority:
- No official all-Q endorsement or future-vote guarantee. Recommendations are analysis; real justice and cooperation hopes remain.'''


def main():
    parent = ROOT / 'data/prepared/compression-points-only-20261007-v1'
    dest = ROOT / 'data/prepared/compact-points-20261007-v2'
    assert not dest.exists() and len(COMPACT.split()) <= 280
    case = copy.deepcopy(next(c for c in read_jsonl(parent / 'cases.jsonl') if c['country_iso3'] == 'BRA'))
    original = json.loads((parent / 'held-plans.json').read_text())['plans']['BRA']
    content = case['prompt'][1]['content']
    assert content.count(original) == 1
    case['prompt'][1]['content'] = content.replace(original, COMPACT)
    case.update(id='libya-bra-compact-points', condition='readable_compact_checked_points')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compression-points-only-base-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    case.update(input_ids=ids, input_ids_digest=digest(ids))
    assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
    dest.mkdir()
    for name in ['sources.json', 'criteria.json', 'presentation-criteria.json']:
        shutil.copy2(parent / name, dest / name)
    write_jsonl(dest / 'cases.jsonl', [case])
    write_json(dest / 'checked-plan.json', {'plan': COMPACT, 'words': len(COMPACT.split()),
        'author': 'same root assistant; hand compressed and checked against original source/all14 frozen meanings, no independent teacher',
        'ordinary_readable_word_boundaries': True, 'all_source_application_authority_meanings_audited': True})
    write_json(dest / 'provenance.json', {'scope': 'One exposed Brazil/Libya complete-meaning compact-point realization diagnostic. No optimization, no new family. Source/Q/metadata/request/contract/criteria unchanged from points-only pack; only plan representation changes.',
        'parent_manifest_sha256': sha256(parent / 'manifest.json'), 'original_plan_sha256': digest(original),
        'old_plan_words': len(original.split()), 'new_plan_words': len(COMPACT.split())})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {p.name: sha256(p) for p in dest.iterdir() if p.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1,
        'source_scope': 'Frozen readable compact-point development diagnostic; no fitting.'})
    write_json(dest / 'manual-inspection.json', {'manifest_sha256': sha256(dest / 'manifest.json'),
        'all_selected_texts_read_complete': True,
        'read_scope': 'Complete Brazil source and all14 source/application compounds reread; every compact bullet hand inspected for polarity, actors, non-party/ChapterVII scope, inquiry stages, real hopes, known repairs, concrete operations/cost and unknown authority. Ordinary spaced text; standard acronyms/hyphenation, no fused-word count shortcut. Older source/Q/metadata/request/contract/criteria identical.'})
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=1)
    write_json(ROOT / 'configs/posttraining/qwen35-compact-points-base-20261007-v2.json', cfg)
    for arm, run in [('point8', 'aurora-plan-input-fit-20261006-v1'), ('compression8', 'aurora-compression-fit-20261006-v1')]:
        new = copy.deepcopy(cfg)
        adapter = ROOT / 'runs' / run / 'adapter'
        new.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
                   adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
        write_json(ROOT / f'configs/posttraining/qwen35-compact-points-{arm}-20261007-v2.json', new)
    runner = (ROOT / 'scripts/run_compression_controls.py').read_text()
    runner = runner.replace('Owned fourteen-case compression baseline', 'Owned one-case compact-points control; no optimization').replace("cfg['eval_cases']==14", "cfg['eval_cases']==1")
    (ROOT / 'scripts/run_compact_points.py').write_text(runner)
    print(json.dumps({'compact_plan_words': len(COMPACT.split()), 'input_tokens': len(ids), 'three_calls': True, 'optimizer_steps': 0}))


if __name__ == '__main__':
    main()
