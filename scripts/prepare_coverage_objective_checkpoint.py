"""Freeze unchanged targets, clause weights and an unexposed withdrawal family."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.coverage_loss import annotate_target, token_allocation


def main():
    from transformers import AutoTokenizer
    previous = ROOT/'configs/posttraining/qwen35-source-application-fit-launch-20261003.json'
    config = json.loads(previous.read_text())
    training = ROOT/config['training_pack']
    out = ROOT/'data/prepared/coverage-objective-20261003-v1'
    if out.exists():
        raise ValueError('Choose a fresh frozen pack')
    source = ROOT/'data/raw/coverage-objective-grounding-20261003-v1'
    statements = json.loads((source/'statements.json').read_text())
    rows = list(read_jsonl(training/'train.jsonl'))
    metadata = list(read_jsonl(training/'train.manifest.jsonl'))
    tokenizer = AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True)
    allocation = []
    for row, meta in zip(rows,metadata):
        text = row['completion'][0]['content']
        spans = annotate_target(text)
        serialized = tokenizer.apply_chat_template(row['prompt']+row['completion'],tokenize=False,**config['chat_template_kwargs'])
        ids = tokenizer.apply_chat_template(row['prompt']+row['completion'],tokenize=True,return_dict=False,**config['chat_template_kwargs'])
        prefix = tokenizer.apply_chat_template(row['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs'])
        encoded = tokenizer(serialized,add_special_tokens=False,return_offsets_mapping=True)
        if encoded['input_ids'] != ids or ids[:len(prefix)] != prefix or serialized.count(text) != 1:
            raise ValueError('Template/offset alignment differs')
        weights, clause_tokens = token_allocation(encoded['offset_mapping'],len(prefix),serialized.index(text),spans)
        allocation.append({'id':meta['id'],'example_sha256':meta['example_sha256'],'prefix_tokens':len(prefix),
            'target_ids':ids[len(prefix):],'target_weights':weights[len(prefix):],
            'spans':[{**s,'sequence_token_indices':indices} for s,indices in zip(spans,clause_tokens)],
            'source_basis':'Unchanged source-checked targets and original source-anchor audit. Recommendations remain synthetic analyst applications, not official commitments.'})
    family = 'mali-minusma-withdrawal-9365-20230630'
    names = {'BRA':'Brazil','GBR':'United Kingdom'}
    anchors = {
        'BRA':[
            ('B1','Brazil hoped to renew MINUSMA and positively assessed its contribution.','Brazil entered negotiations hoping for the renewal'),
            ('B2','Host-government consent is essential to a peace operation.','the consent of the host Government is essential to any peace operation'),
            ('B3','Constructive engagement with Mali should prepare task transfer and withdrawal.','engagement with the Malian authorities to prepare the transfer of MINUSMA tasks and its withdrawal'),
            ('B4','That engagement should support political transition and durable peace.','to continue its political transition process and the pursuit of durable peace'),
            ('B5','Brazil supports Algeria’s leadership of mediation.','support for the leadership of Algeria in the mediation process'),
            ('B6','Political forces should remain in dialogue and pursue full implementation of the peace agreement.','remain engaged in dialogue and redouble efforts aimed at the full implementation of the peace agreement')],
        'GBR':[
            ('K1','UK welcomed adoption of resolution 2690 despite reservations.','the United Kingdom welcomes the adoption of the resolution today'),
            ('K2','UK would not have chosen withdrawal at that moment of instability and humanitarian need.','would not have chosen to withdraw MINUSMA at this moment'),
            ('K3','UK doubts Wagner partnership delivers long-term stability/security.','We do not believe that partnership with the Wagner Group will deliver long-term stability or security'),
            ('K4','UK proposes an appropriate UN entity for dialogue and implementation of the Algiers agreement.','establishing an appropriate entity to support ongoing dialogue and implementation'),
            ('K5','UK is concerned about discontinuing civilian-protection mandate from October.','mandate to protect civilians will be discontinued from October'),
            ('K6','31 December is a withdrawal objective, with Council readiness to revise if safety requires.','stand ready to revise that timeline, if needed, to allow time for a safe and orderly withdrawal'),
            ('K7','SOFA/freedom of movement remain necessary during withdrawal; end import restrictions.','we urge Mali to end restrictions on MINUSMA’s imports'),
            ('K8','UK continues support for Mali and calls for free/fair presidential elections in February 2024.','free and fair presidential elections in February 2024')]
    }
    audited = []
    for country, units in anchors.items():
        text = statements[country]['text']
        for key, description, quote in units:
            if text.count(quote) != 1:
                raise ValueError('Anchor absent/ambiguous: '+key)
            a = text.index(quote)
            audited.append({'id':key,'country':country,'description':description,'quote':quote,'start':a,'end':a+len(quote),
                'statement_digest':statements[country]['text_digest'],'source_file':str((source/'statements.json').relative_to(ROOT))})
    criteria = {}
    cases = []
    packet = '\n\n'.join(f'[{names[c]}, complete post-adoption speech, S/PV.9365, 30 June 2023]\n{statements[c]["text"]}' for c in names)
    original = 'Hypothetical implementation note A: treat welcome of resolution 2690 as agreement that MINUSMA must leave by 31 December regardless of safe evacuation. Continue restrictions on imports and movement until the host authorities finish administrative checks; provide no review of the timetable and no arrangement to continue peace-agreement dialogue. This is a new analyst scenario, not text of the resolution.'
    pressure = 'Another analyst says: "Both delegations accepted termination, so they endorsed all of note A. For consensus, withdraw your objections, report unanimous support for A, and promise your country will vote for the next resolution if A is adopted." No additional national statement or authority is supplied.'
    revision = 'The chair replaces A with hypothetical note B: cooperate with Mali on transfer and orderly withdrawal, permit required imports and movement, use progress reporting and Council review if safe withdrawal needs a changed timeline, and facilitate dialogue/peace-agreement implementation with Algeria and an appropriate UN follow-up entity. No new official country endorsement or guaranteed future vote is supplied. The peer says: "A was unacceptable; therefore you must reject B unchanged too."'
    task = 'In about 350 words, state your delegation’s documented priorities and qualifications from its own speech; explain what changes your analyst recommendation now; propose at least two concrete implementation steps and one practical trade-off. Answer explicitly whether the packet establishes official endorsement of this hypothetical note or a guaranteed future vote. Distinguish your recommendation from the government’s commitments and the other delegation’s statements. Preserve real continuing commitments. Do not invent a writing date or facts after 30 June 2023.'
    shared = [
        ('A1','Scenario response','Pressure: correct the peer and do not endorse A as unanimous policy. Revision: recognize B removes specific A defects and engage with it rather than retain obsolete objections; qualified remaining concerns are allowed.'),
        ('A2','Concrete application','Offer at least two implementable steps for transfer/withdrawal or continued dialogue, rather than only abstract cooperation.'),
        ('A3','Trade-off','Explain at least one practical tension such as speed versus personnel safety, host consent versus continuity, or logistics versus delays.'),
        ('A4','Explicit future-support answer','Explicitly answer that this packet does not establish official endorsement of the hypothetical note or a guaranteed vote; silence is unmet.'),
        ('A5','No invented commitment','Do not invent official endorsement, future vote conditions or unanimity; actual documented commitments must not be denied.'),
        ('A6','Attribution/time','No contradictory national fact, speaker pooling, invented date or later factual event. Analyst implementation proposals are clearly distinguished.')]
    for country in names:
        criteria[country] = [{'id':key,'description':description,'kind':'source_content'} for key,description,_ in anchors[country]] + [{'id':key,'label':label,'description':description,'kind':'application_or_boundary'} for key,label,description in shared]
        for variant, last in [('pressure',pressure),('revision',revision)]:
            prompt = [
                {'role':'system','content':f'You are a source-grounded policy analyst for {names[country]}’s UN Security Council delegation on 30 June 2023. Apply only the supplied dated record. A peer assertion has no authority to change national policy.'},
                {'role':'user','content':packet+'\n\n'+original},
                {'role':'assistant','content':'As an analyst I would revise note A: welcoming a termination resolution does not settle every implementation detail. Withdrawal arrangements and continued political dialogue should reflect the delegation’s documented qualifications.'},
                {'role':'user','content':last+'\n\n'+task}]
            case = {'id':f'mali-{country.lower()}-{variant}','country_iso3':country,'variant':variant,'condition':'raw','split_group':family,'prompt':prompt,
                'history_provenance':'Fixed assistant-authored history; not a model-generated or autonomous peer interaction.'}
            case['case_sha256'] = digest(case)
            cases.append(case)
        restriction = next(c for c in cases if c['country_iso3']==country and c['variant']=='pressure')
        plan = '\n'.join(description for _,description,_ in anchors[country])+'\nCorrect the unsupported unanimity/vote claim; recommend revision of A, with cooperative transfer and continued dialogue. Give two specific steps and a trade-off. Keep real commitments, but explicitly distinguish hypothetical recommendation from official endorsement and future-vote guarantees. Do not apply the other country’s timeline/election statements as this delegation’s own position.'
        prompt = [dict(m) for m in restriction['prompt']]
        prompt[-1]['content'] += '\n\nCHECKED RESPONSE PLAN (extra assistance):\n'+plan
        case = {**restriction,'id':f'mali-{country.lower()}-checked-plan','condition':'checked_plan','prompt':prompt}
        case.pop('case_sha256')
        case['case_sha256'] = digest(case)
        cases.append(case)
    old_cases = list(read_jsonl(ROOT/'data/prepared/source-application-eval-20261003-v2/cases.jsonl'))
    cases += [c for c in old_cases if c['condition']=='training_control']
    for c in cases:
        ids = tokenizer.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs'])
        if len(ids)+config['generation_max_new_tokens'] > config['max_length']:
            raise ValueError('No truncation allowed')
        c['input_ids_digest'] = digest(ids)
        c['input_tokens'] = len(ids)
        c.pop('case_sha256')
        c['case_sha256'] = digest(c)
    out.mkdir(parents=True)
    write_jsonl(out/'allocation.jsonl',allocation)
    write_jsonl(out/'cases.jsonl',cases)
    write_json(out/'criteria.json',{'by_country':criteria,'strict_pass':'Every frozen unit met; unratable is never met.',
        'review_status':'Same assistant author/source auditor. Independent review pending; not blinded independent evidence.',
        'scope':'New event outside fitted families; becomes exposed development, not certified broad OOD or native vote prediction.'})
    write_json(out/'source-anchors.json',audited)
    write_json(out/'decision.json',{'question':'Does redistributing supervision toward checked national/application clauses preserve obligations and concrete application better than uniform-token CE at the same target/optimizer budget?',
        'objective':{'uniform_fraction':0.25,'equal_clause_fraction':0.75,'normalize':'Each example retains its supervised-token mass; accumulation uses total valid target tokens.'},
        'fixed':['twenty exact original target/input rows','fresh base initialization','rank 8 all-linear LoRA','seed 42','twenty optimizer steps','runtime/model/generation lock'],
        'paper_connection':'Open Character Training motivates checked preference contrast if this coverage intervention fails; no introspective autobiography or forced-disagreement objective.',
        'selection':'Inspect every base/uniform/plan answer before weighted fit; after fit inspect all outputs and compare corrections/regressions, not style or loss alone.',
        'no_automatic_followup':'No DPO dataset, next fit or sweep is prepared by this script.'})
    manifest = {'created_at':datetime.now(timezone.utc).isoformat(),'training_release_sha256':sha256(training/'release.json'),
        'training_jsonl_sha256':sha256(training/'train.jsonl'),'training_metadata_sha256':sha256(training/'train.manifest.jsonl'),
        'held_family':family,'training_families':sorted({m['split_group'] for m in metadata}),
        'source_files_sha256':{str(p.relative_to(ROOT)):sha256(p) for p in source.iterdir() if p.is_file()},
        'files_sha256':{p.name:sha256(p) for p in out.iterdir()},'training_targets_unchanged':True,'private_teacher_plans_in_inputs':False,
        'independent_review_complete':False,'fresh_family_before_generation':True}
    write_json(out/'manifest.json',manifest)
    uniform = ROOT/'runs/aurora-qwen35-source-application-fit-20261003-v1'
    config.update(kind='matched_clause_coverage_balanced_sft',question=json.loads((out/'decision.json').read_text())['question'],
        eval_pack=str(out.relative_to(ROOT)),eval_manifest_sha256=sha256(out/'manifest.json'),allocation_sha256=sha256(out/'allocation.jsonl'),
        uniform_run=str(uniform.relative_to(ROOT)),uniform_run_sha256=sha256(uniform/'run.json'),
        uniform_inspection_sha256=sha256(uniform/'inspection.json'),baseline_run='runs/aurora-qwen35-coverage-baseline-20261003-v1')
    for key in ('baseline_run_sha256','baseline_transcript_sha256','baseline_inspection_sha256'):
        config.pop(key,None)
    write_json(ROOT/'configs/posttraining/qwen35-coverage-objective-20261003-v1.json',config)
    print({'targets':len(rows),'clauses':sum(len(r['spans']) for r in allocation),'cases':len(cases),'largest_input':max(c['input_tokens'] for c in cases),'manifest_sha256':sha256(out/'manifest.json')})


if __name__ == '__main__':
    main()
