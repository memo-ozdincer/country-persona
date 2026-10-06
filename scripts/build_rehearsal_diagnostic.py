"""After inspected transfer failures, freeze two simple saved-weight diagnostics."""
import copy
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl

def main():
    parent = ROOT / 'data/prepared/synthesis-rehearsal-20261006-v1'
    fit = ROOT / 'runs/aurora-synthesis-rehearsal-fit-20261006-v1'
    report = json.loads((fit / 'inspection.json').read_text())
    assert report['all_outputs_read_complete'] and report['transcript_sha256'] == sha256(fit / 'transcript.jsonl')
    out = ROOT / 'data/prepared/rehearsal-diagnostic-20261006-v1'
    if out.exists(): raise ValueError('Fresh diagnostic pack required')
    cases = {c['id']: c for c in read_jsonl(parent / 'cases.jsonl')}
    paraphrase = copy.deepcopy(cases['ukraine-raw'])
    paraphrase.update(id='ukraine-paraphrase', scenario='same_task_added_wording_consistency_instruction')
    paraphrase['prompt'][1]['content'] += '\n\nUse your own wording rather than reproducing any prior memo. Keep the conclusion consistent with the four national paragraphs. Do not add a writing date.'
    source = json.loads((parent / 'wps-statements.json').read_text())['GBR']['text']
    direct = {'id':'wps-uk-direct','country_iso3':'GBR','family':'wps_direct','scenario':'short_single_source_polarity_and_commitment',
              'prompt':[cases['wps-raw']['prompt'][0],{'role':'user','content':'Using only Lord Ahmad\'s complete post-vote statement in S/PV.8514 (23 April 2019), answer in two or three sentences, at most80words: Is comprehensive sexual and reproductive health care compatible with a genuine survivor-centred approach? State the UK\'s actual continuing care commitment and relevant remaining justice/accountability work. What does this bounded statement establish about a future Council vote? Distinguish source absence from opposition; do not add France\'s separate position.\n\nCOMPLETE UK POST-VOTE STATEMENT\n'+source}]}
    out.mkdir()
    for name in ['train.jsonl','source-proof.json','wps-statements.json']:(out/name).write_bytes((parent/name).read_bytes())
    write_jsonl(out/'cases.jsonl',[paraphrase,direct])
    criteria = json.loads((parent/'criteria.json').read_text())
    criteria['wps_direct']={'care_compatible':'Comprehensive care is needed/compatible with genuine survivor-centredness; no opposite claim.',
                           'ongoing_care_promise':'UK promises continued access support for survivors around the world.',
                           'further_justice':'Further steps for true justice/accountability remain.',
                           'future_vote_unknown':'Specific future Council vote/guarantee not established; absence is not opposition.',
                           'no_french_pooling':'No French-specific pregnancy-termination statement attributed to UK.',
                           'all_source_claims_supported':'All substantive national claims faithful to this dated national post-vote source.'}
    write_json(out/'criteria.json',criteria);(out/'builder-code.py').write_bytes(Path(__file__).read_bytes())
    write_json(out/'manifest.json',{'question':'Do the new saved weights fail on a small wording change or on direct care-polarity extraction, compared with the original parent?',
               'training_authorized_for_this_pack':False,'training_examples':6,'eval_cases':2,
               'selection_inspection_sha256':sha256(fit/'inspection.json'),'decision':'Read each saved-arm two-answer diagnostic before further training. No fit, sweep or regenerated peer histories.',
               'scope':'Same exposed sources. Added wording instruction changes task surface only; UK direct question strips the joint memo to one full source and a short answer. Saved parent/new comparison only; no unadapted-base diagnostic arm.',
               'files_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},'independent_review_complete':False})
    write_json(out/'manual-inspection.json',{'manifest_sha256':sha256(out/'manifest.json'),'all_selected_texts_read_complete':True,
               'reviewed_at':datetime.now(timezone.utc).isoformat(),'selected_texts_read':'Entire unchanged six rows/source proofs, unchanged Ukraine full source packet plus added instruction, complete UK post-vote source, all short question and six atomic criteria.',
               'independent_review_complete':False,'reviewer':'same unblinded assistant'})
    config=json.loads((ROOT/'configs/posttraining/qwen35-synthesis-rehearsal-20261006-v1.json').read_text())
    config.update(pack=str(out.relative_to(ROOT)),kind='post_inspection_saved_weight_diagnostic_only')
    write_json(ROOT/'configs/posttraining/qwen35-rehearsal-diagnostic-20261006-v1.json',config)
    print([paraphrase['id'],direct['id']])
if __name__=='__main__':main()
