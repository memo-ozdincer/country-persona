"""Replay sixteen actual teacher outputs, curated long/short pairs and new primary sources."""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from verify_two_context_country import exited

def main():
    runs = ['aurora-compression-teacher-20261006-v2', 'aurora-compression-teacher-probe-20261006-v2', 'aurora-compression-teacher-remaining-20261006-v1']
    from transformers import AutoTokenizer
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compression-teacher-20261006-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    records, resources, tokens, seconds = [], [], 0, 0
    for name, count in zip(runs, [8, 1, 7], strict=True):
        directory = ROOT / 'runs' / name
        r = json.loads((directory / 'run.json').read_text()); i = json.loads((directory / 'inspection.json').read_text())
        pack = ROOT / r['config']['pack']; m = json.loads((pack / 'manifest.json').read_text()); h = json.loads((pack / 'manual-inspection.json').read_text())
        cases, rows = list(read_jsonl(pack / 'cases.jsonl')), list(read_jsonl(directory / 'transcript.jsonl'))
        assert r['status'] == 'completed' and r['optimizer_steps'] == 0 and exited(r['identity'])
        assert len(cases) == len(rows) == len(i['reviews']) == count and i['all_outputs_read_complete']
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert r['pack_manifest_sha256'] == h['manifest_sha256'] == sha256(pack / 'manifest.json') and h['all_selected_texts_read_complete']
        for file, expected in m['files_sha256'].items(): assert sha256(pack / file) == expected
        for file, expected in r['source_code_sha256'].items(): assert sha256(directory / Path(file).name) == expected
        assert r['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        assert r['versions'] == cfg['runtime_pins'] and r['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model', 'revision', 'seed', 'max_length', 'chat_template_kwargs', 'generation_max_new_tokens']:
            assert r['config'][key] == cfg[key]
        prev = r['previous_inspected_run']; assert sha256(ROOT / prev['run'] / 'inspection.json') == prev['inspection_sha256']
        for c, row, review in zip(cases, rows, i['reviews'], strict=True):
            assert c['id'] == row['id'] == review['id'] and c['input_ids'] == row['input_ids']
            assert tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False) == c['input_ids']
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output'] and not row['at_output_cap']
            assert review['all_output_read_complete'] and review['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest()
            assert review['words'] == len(row['output'].split())
            tokens += row['generated_tokens']; seconds += row['generation_seconds']
        resources.append({'run': str(directory.relative_to(ROOT)), 'identity': r['identity'], 'gpu': r['gpu'], 'exited': True})
        records.append({'run': str(directory.relative_to(ROOT)), 'outputs': count, 'word_counts': {v['id']: len(v['output'].split()) for v in rows}, 'transcript_sha256': sha256(directory / 'transcript.jsonl'), 'inspection_sha256': sha256(directory / 'inspection.json')})
    draft = ROOT / 'data/prepared/compression-student-draft-20261006-v2'
    m = json.loads((draft / 'manifest.json').read_text()); h = json.loads((draft / 'manual-inspection.json').read_text())
    assert not m['training_authorized_for_this_pack'] and not h['fitting_ready'] and h['all_selected_texts_read_complete'] and h['manifest_sha256'] == sha256(draft / 'manifest.json')
    for file, expected in m['files_sha256'].items(): assert sha256(draft / file) == expected
    curated = json.loads((draft / 'curated-plans.json').read_text()); assert curated['all_selected_corrected_texts_read_complete']
    target = json.loads((draft / 'preferred-targets.json').read_text())['targets']; cases = list(read_jsonl(draft / 'cases.jsonl')); audits = list(read_jsonl(draft / 'chosen-token-audit.jsonl'))
    old = ROOT / 'data/prepared/diverse-country-fit-20261006-v2'; point = ROOT / 'data/prepared/plan-input-fit-20261006-v1'
    assert sha256(draft / 'preferred-targets.json') == sha256(old / 'preferred-targets.json')
    prior = list(read_jsonl(point / 'cases.jsonl'))[:8]; priorplans = json.loads((point / 'teacher-plans.json').read_text())['fitting_plans']
    for c, a, p in zip(cases, audits, prior, strict=True):
        id = c['id']; plan = curated['plans'][id]
        assert c['prompt'][0] == p['prompt'][0] and c['prompt'][1]['content'].replace(plan, priorplans[id]) == p['prompt'][1]['content']
        assert plan in c['prompt'][1]['content'] and target[id] not in c['prompt'][1]['content']
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        full = tok.apply_chat_template(c['prompt'] + [{'role': 'assistant', 'content': target[id]}], tokenize=True, return_dict=False, enable_thinking=False)
        oa = next(v for v in read_jsonl(old / 'pair-audit.jsonl') if v['id'] == id)
        assert ids == c['input_ids'] == a['prompt_ids'] and full[:len(ids)] == ids and full[len(ids):] == a['chosen_ids'] == oa['chosen_ids']
        assert a['long_plan_words'] == len(plan.split()) > 300 and a['short_target_words'] == len(target[id].split()) <= 300
    raw = ROOT / 'data/raw/compression-libya-grounding-20261006-v1'; proof = json.loads((raw / 'source-proof.json').read_text()); doc = (raw / 'record-9469.txt').read_text()
    assert proof['pdf_sha256'] == sha256(raw / 'record-9469.pdf') and proof['document_text_digest'] == digest(doc)
    assert proof['columns_sha256'] == sha256(raw / 'columns.json') and proof['source_hand_read_complete'] and proof['body_word_counters_equal'] and proof['english_cover_verified']
    assert proof['selected_pdf_pages_viewed'] == [11, 12, 13, 14]
    sources = json.loads((raw / 'statements.json').read_text())
    for co, s in sources.items():
        assert doc[s['start']:s['end']].strip() == s['raw_text']
        assert re.sub(r'(?<=\w)-\s+(?=\w)', '-', s['raw_text']) == s['text']
        assert digest(s['raw_text']) == s['raw_text_digest'] and digest(s['text']) == s['text_digest']
        assert [s['start'], s['end']] == proof['source_span_boundaries'][co]
    adj = json.loads((raw / 'ambassador-adjudication.json').read_text())
    assert adj['french_pdf_sha256'] == sha256(raw / 'record-9469-FR.pdf') and adj['primary_french_page_viewed']
    prospective = json.loads((ROOT / 'data/curation/compression-libya-prospective-20261006-v1.json').read_text())
    assert prospective['source_sha256'] == sha256(raw / 'statements.json') and prospective['source_proof_sha256'] == sha256(raw / 'source-proof.json')
    assert prospective['ambassador_adjudication_sha256'] == sha256(raw / 'ambassador-adjudication.json')
    assert prospective['new_libya_model_calls'] == prospective['new_optimizer_steps'] == 0 and not prospective['fit_prepared']
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': 16, 'new_optimizer_steps': 0,
        'cumulative_qwen35_steps': 2270, 'reference_qwen25_steps': 582, 'all_sixteen_full_uncapped_teacher_outputs_read': True,
        'teacher_records': records, 'resources': resources, 'all_three_owned_gpu_identities_exited': True,
        'teacher_outputs_approved_unchanged': 0, 'curated_pairs': 8, 'curated_pair_word_counts': {a['id']: {'plan': a['long_plan_words'], 'target': a['short_target_words']} for a in audits},
        'chosen_completion_tokens_exact_to_raw8_and_point8': True, 'student_fit_authorized': False, 'student_model_quality_outputs': 0,
        'generated_tokens': tokens, 'generation_seconds': seconds, 'fresh_primary_source': {'symbol': 'S/PV.9469', 'date': '2023-11-08', 'countries': ['BRA', 'FRA'], 'pdf_sha256': proof['pdf_sha256'], 'english_selected_pages_viewed': [11, 12, 13, 14], 'french_ambassador_posting_adjudicated': True, 'libya_writer_calls': 0},
        'independent_review_complete': False, 'scope': 'Actual4Bteacher drafts extensivelycorrected/rewritten bysameassistant intoexactcontent longer inputs. Dataquality/preparation evidence, not student/persona/nativeprediction/multiagent/strongOOD gain. Two safeoccupiedGPU guardstops beforeownership, one missing-review CPU preparation failure and one nonPDF acquisition failure preserved, zero extra calls/updates.',
        'next_decision': 'Finish checkedLibya raw/longplan control inputs and freezeprospective presentation checks, then matching inspectedbase controls/actualzero-gradient negatives. Bind one fresh8target256update comparison withunchangednativechosen tokens; inspect savedpoint8 andnewfit onidentical outsideinputs before anyscaleup. No studentfit/queue/sweep authorized orprepared now.'}
    write_json(ROOT / 'reports/compression-preparation-20261006-v1.json', receipt)
    print(json.dumps({k: receipt[k] for k in ['status', 'new_model_outputs', 'curated_pair_word_counts', 'student_fit_authorized', 'fresh_primary_source']}, indent=2))

if __name__ == '__main__':
    main()
