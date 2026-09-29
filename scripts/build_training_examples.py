"""Build complete, provenance-linked teaching examples; never admit rows to training."""
import copy
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAPERS={
 'centaur':{'name':'Centaur — Nature 2025','url':'https://www.nature.com/articles/s41586-025-09215-4','why':'Learns observed human responses with loss restricted to response tokens. Here the institutional action or authentic answer is the observed target; diplomatic generalization remains untested.'},
 'raft':{'name':'RAFT — Zhang et al., 2024','url':'https://arxiv.org/abs/2403.10131','why':'Teaches answering from relevant documents while ignoring distractors. Our source-grounded examples adapt its evidence-selection idea, not its entire training recipe.'},
 'ca':{'name':'Constitutional AI — Bai et al., 2022','url':'https://arxiv.org/abs/2212.08073','why':'Turns prose principles into critiques and corrected responses. Dated policy clauses can guide revisions, but may not determine a unique action.'},
 'cc':{'name':'Constitutional Classifiers — Sharma et al., 2025','url':'https://arxiv.org/abs/2501.18837','why':'Uses written rules to construct classifier supervision. Our adaptation checks policy support and contradictions; the paper evaluates safety safeguards, not diplomatic choices.'},
 'dpo':{'name':'DPO — Rafailov et al., 2023','url':'https://arxiv.org/abs/2305.18290','why':'Learns from chosen/rejected responses to the same prompt. Preference validity still depends on evidence and review.'},
 'unbench':{'name':'UNBench — Liang et al., AAAI 2026','url':'https://arxiv.org/abs/2502.14122','why':'Separates proposal, voting and statement tasks. These acquired benchmark samples remain evaluation material, not new training examples.'},
 'distill':{'name':'Learning by Distilling Context — Snell et al., 2022','url':'https://arxiv.org/abs/2209.15189','why':'A teacher sees extra context and the student learns its answers without that context. This can test internalizing stable policy; changing facts should remain available at inference.'},
 'dapt':{'name':'Don’t Stop Pretraining — Gururangan et al., ACL 2020','url':'https://arxiv.org/abs/2004.10964','why':'Studies continued domain/task pretraining. Applying text continuation to modern country personas is an optional ablation, not proof of decision fidelity.'}}

def j(x):return json.dumps(x,ensure_ascii=False,indent=2)
def rows(p):return [json.loads(s) for s in (ROOT/p).read_text().splitlines() if s.strip()]
def message(role,content):return {'role':role,'content':content}
def make(title,objective,system,context,question,target,papers,notes,origin='Authored conversion of a real record; review candidate'):
 user=(context+'\n\n' if context else '')+question
 return {'title':title,'objective':objective,'origin':origin,'system':system,'context':context,'question':question,'completion':target,'loss':'Supervise assistant completion only; mask the system instruction and all supplied context.','notes':notes,'papers':papers,'format':{'prompt':[message('system',system),message('user',user)],'completion':[message('assistant',target)],'chat_template_kwargs':{'enable_thinking':False}}}

def metadata(o):
 keys=['id','country_iso3','represented_entity','institution','speaking_capacity','speaker','event_date','date','date_precision','available_date','group_id','group_ids','document_symbols','source_url','quality_flags','split','training_admitted','review_status','recommending_states','reviewed_states','upr_cycle']
 return {k:o[k] for k in keys if k in o}

def examples(o,task,country):
 meta=metadata(o);text=o.get('text') or o.get('passage') or o.get('claim') or '';ctx=j(meta)
 system='Use the supplied evidence and preserve its attribution, date precision and uncertainty. Do not invent commitments or private motives.'
 if task=='authentic_qa':
  history=o.get('history',[])
  ctx=j({k:v for k,v in meta.items() if k not in ['quality_flags','split','training_admitted','review_status']})
  if history:ctx+='\n\nComplete recorded preceding dialogue:\n'+j(history)
  if o.get('context'):ctx+='\n\nStored context:\n'+o['context']
  return [make('Authentic answer imitation','Response SFT',system,ctx,o['question'],text,['centaur'],['The question and answer are authentic; the wrapper is newly authored. Earlier turns are context, not additional targets.','This imitates a recorded response; it does not establish that the model knows the underlying facts.','All preceding history is included here without truncation. Tokenize before training; long German histories may exceed the model budget.'],'Authentic recorded answer; new illustrative prompt wrapper')]
 if task in ['upr_response','vote_prediction']:
  ctx+=('\n\n'+o['context']) if o.get('context') else ''
  # response labels belong only in completion; metadata whitelist excludes them.
  return [make('Recorded action classification','Action-only SFT / evaluation',system,ctx,o.get('question','Predict the recorded action.'),text,['unbench' if task=='vote_prediction' else 'centaur'],['Target is the observed label. Score class probabilities and minority-class recall, not only accuracy.','UPR record dates may be document dates, not response dates. Support is not implementation.','A benchmark_reserved flag means evaluation only; do not train on this displayed benchmark record.'],'Observed action label; new illustrative wrapper')]
 if task=='upr_recommendation':
  return [make('Retrieve and attribute a recommendation','Grounded extraction SFT',system,ctx+'\n\nRecorded recommendation:\n'+text,'Quote the recorded recommendation, retaining its number and recommending state.',text,['raft'],['This is an open-book extraction example. The source already contains the answer.','Generating a new recommendation requires prior review evidence; the archived recommendation alone does not supply that context.'],'Exact recorded recommendation; authored extraction question')]
 if task=='country_statistics':
  target=j({k:o.get(k) for k in ['country_iso3','indicator','value','unit','reference_year','database_last_updated','missing']})
  return [make('Extract a dated numeric observation','Structured extraction SFT',system,j(o),'Return country_iso3, indicator, value, unit, reference_year, database_last_updated and missing as JSON. Preserve null values.',target,['raft'],['The value is intentionally visible: this teaches extraction, not forecasting or closed-book factual recall.','Database vintage is later than the reference year; do not claim this value was known in that year.'])]
 if task=='policy_applications' and o.get('messages'):
  ms=o['messages'];user=ms[1]['content'];context,sep,question=user.rpartition('Question: ');context=context if sep else '';question=question if sep else user;e=make('Apply policy to a concrete question','Grounded policy SFT',ms[0]['content'],context.strip(),question,ms[-1]['content'],['raft','ca'],o.get('rubric',[]),'Existing authored candidate, not an authentic diplomatic exchange')
  e['format']={'prompt':ms[:-1],'completion':ms[-1:],'chat_template_kwargs':{'enable_thinking':False}};return [e]
 if task=='decision_cases':
  ctx=j({k:o.get(k) for k in ['country_iso3','event_date','proposal_symbol','proposal_summary']})
  action=make('Predict the recorded final vote','Action-only SFT',system,ctx,'Which final vote was recorded? Answer only with the recorded action label.',o['observed_action'],['centaur','unbench'],['Proposal summary is a project paraphrase, not the full draft. Full proposal text is separately linked in the original record.','Observed vote and post-vote explanation are excluded from this prompt. Only two independent events exist.'])
  report=make('Report the decision and its evidence limits','Grounded report SFT',system,j({k:o.get(k) for k in ['country_iso3','event_date','proposal_summary','observed_action','public_explanation','explanation_kind','stated_considerations','conditions_status','missing_context']}),'Return JSON containing observed_action, public_explanation, explanation_kind and conditions_status; preserve missing explanations as null.',j({k:o.get(k) for k in ['observed_action','public_explanation','explanation_kind','conditions_status']}),['raft'],['This is retrospective reporting. The vote is intentionally supplied, so it is not a prediction test.'])
  return [action,report]
 if task=='vote_label_only':
  target=j({k:o.get(k) for k in ['original_vote','amended_vote','decision_topic','decision_mode']})
  return [make('Read the original versus amended vote','Record interpretation SFT',system,j({k:o.get(k) for k in ['country_name','event_date','document_symbols','original_vote','amended_vote','decision_topic','decision_mode']}),'Return original_vote, amended_vote, decision_topic and decision_mode as JSON.',target,['centaur'],['This complete example teaches record interpretation only: the action is already in the context.','Decision-prediction SFT is blocked until the proposal and pre-decision context are joined. An identifier-only prompt would mostly teach memorization.'])]
 if task=='unverified_speech_segment':
  return [make('Recognize unresolved speaker attribution','Evidence triage SFT',system,ctx+'\n\nComplete stored segment:\n'+text,'Can this record be admitted as verified country-specific speech supervision? Return status and reason.',j({'status':'needs_review','reason':'Speaker boundaries and attribution are not verified in this record.'}),['raft'],['Target is derived from the explicit record status, not a new independent speaker judgment.','Resolve speaker boundaries against the primary record before country-voice SFT.'])]
 if task=='press_conference':
  return [make('Keep the conference role distinct','Attribution SFT',system,ctx,'Return the institution and speaking_capacity recorded for this conference. Does this metadata alone provide a selected final answer?',j({'institution':o.get('institution'),'speaking_capacity':o.get('speaking_capacity'),'selected_answer_present':False}),['raft'],['This metadata example explains the container. Use the authentic-Q&A example in this source for actual response SFT.','Do not supervise the whole multi-ministry transcript as one spokesperson answer.'])]
 if task=='statement_reconstruction':
  return [make('Reconstruct the complete attributed statement','Auxiliary statement SFT / reserved evaluation',system,j({k:v for k,v in meta.items() if k not in ['quality_flags','split','training_admitted','review_status']})+('\n\nStored proposal context:\n'+o['context'] if o.get('context') else ''),'Produce the recorded statement for this agenda: '+o.get('title','the recorded meeting')+'.',text,['unbench' if o.get('source_id')=='unbench' else 'centaur'],['Complete original statement is the target; it is not present in the input. The prompt is newly authored.','An agenda/title does not uniquely determine this speech. This is a retrospective imitation proxy, not a realistic forecast; prefer grounded policy applications for transfer.','Reserved benchmark rows and unverified speaker/phase flags remain evaluation/review restrictions.'],'Authentic recorded statement; authored reconstruction instruction')]
 if task=='domain_text':
  return [{'title':'Full-text domain adaptation','objective':'Optional continued pretraining','origin':'Exact complete stored speech','system':'Not used for text-only language modeling.','context':'No separate question or chat prompt.','question':'Not used.','completion':text,'loss':'Next-token loss on the text sequence; no assistant-completion mask.','notes':['This is continued pretraining, not instruction SFT.','Keep complete speech/event families together and validate the historical entity. Language-model loss is not a policy-fidelity score.'],'papers':['dapt'],'format':{'text':text}}]
 if not text:
  text=j({k:v for k,v in o.items() if k in ['public_explanation_summary','original_vote','amended_vote','claim','supports','opposes','unknown']})
 # A complete source-focused quotation task is honest evidence-use supervision; policy applications are added separately where curated.
 paras=[p.strip() for p in text.split('\n\n') if len(p.strip())>=160]
 passage=paras[0] if paras else text
 start=text.find(passage)
 return [make('Extract a source passage with attribution','Grounded evidence SFT',system,ctx+'\n\nSelected complete passage:\n'+passage,'Return a JSON object with record_id, quoted_passage and evidence_scope. Copy the supplied passage exactly; set evidence_scope to "source statement, not independent verification".',j({'record_id':o.get('id'),'quoted_passage':passage,'evidence_scope':'source statement, not independent verification'}),['raft'],[f'The complete selected passage occupies characters {start}–{start+len(passage)} of the stored text. It is a selected span, not the whole document; the complete record is available below.','This teaches extraction and attribution. It does not yet teach novel policy application; use the additional reviewed policy scenarios when available.','Published statements are observed text, not necessarily enduring principles or evidence of implementation.'])]

def public_example(o):
 meta=metadata(o)
 return make('Identify the source and its evidential role','Attribution SFT','Use only the supplied record metadata. Do not infer a policy position from a publisher name.',j(meta),'Return the record ID, represented entity, recorded date, and whether this metadata supplies an observed action or a policy text.',j({'record_id':o.get('id'),'represented_entity':o.get('represented_entity',o.get('country_iso3')),'recorded_date':o.get('event_date',o.get('date')),'text_or_action_supplied':False}),['raft'],['This public example uses metadata only. Complete original-text training examples are in the owner-only research explorer.','This is an attribution exercise, not a substitute for decision or policy training.'])

def policy_extensions(card):
 # Classifier and revision rows are complete derived candidates, not historical observations.
 extra=[]
 for e in card['preference_examples']:
  f=e['format'];prompt=f['prompt'];chosen=f['chosen'][0]['content'];rejected=f['rejected'][0]['content']
  context='Original evidence and task:\n'+j(prompt)
  for label,draft in [('supported',chosen),('contradicted',rejected),('not_established','This passage proves that every stated policy commitment has already been fully implemented.')]:
   v=make('Classify policy consistency: '+label,'Constitutional classifier SFT','Judge the draft against the supplied policy evidence. Use supported, contradicted, or not_established. Return the label only.',context,'Draft to classify:\n'+draft,label,['cc'],['This is a classifier target, not the country’s decision.','Supported/contradicted labels inherit the controlled preference annotation. The not_established case is a newly authored implementation overclaim. All require independent review.'])
   v['provenance']=e['provenance'];extra.append(v)
  v=make('Revise a policy contradiction','Constitution-guided revision SFT','Correct only claims contradicted by the supplied evidence. Preserve qualifications and attribution.',context,'Revise this draft:\n'+rejected,chosen,['ca'],['The flawed draft is input, never a supervised assistant target.','The corrected answer is inherited from the existing authored preference pair.']);v['provenance']=e['provenance'];extra.append(v)
 if card['policy_examples']:
  original=card['policy_examples'][0]
  if original.get('provenance'):
   info=original['provenance']
   context=j({k:info[k] for k in ['country_iso3','countries','represented_entity','event_date','date'] if k in info})
   distilled=make('Internalize a stable policy brief','Context-distillation SFT candidate','Apply the represented institution’s dated public policy. Preserve uncertainty about facts the policy does not establish.',context,original['question'],original['completion'],['distill'],['Teacher receives the complete evidence-conditioned prompt shown below. Student sees only identity/date and the question.','This demonstrates the data transformation using an existing authored target; no teacher model was run and the result has not been validated.','Keep future updates in retrieval. Compare this against supplying the brief at inference; it is not an uncontaminated forecasting task.'])
   distilled['teacher_prompt']=original['format']['prompt'];distilled['provenance']=info;extra.append(distilled)
 card['policy_examples'].extend(extra)


def build():
 inv=json.loads((ROOT/'explorer/sources.json').read_text());profiles=json.loads((ROOT/'explorer/source_profiles.json').read_text());db=sqlite3.connect(ROOT/'.cache/data-publication/catalog.sqlite')
 policy=rows('data/prepared/country-extension-20260914/policy-applications.candidates.jsonl')+rows('data/prepared/country-knowledge-20260914/examples.jsonl')
 workshop=rows('data/prepared/policy-workshop-20260916/preference.dpo.jsonl');wm=rows('data/prepared/policy-workshop-20260916/preference.dpo.manifest.jsonl')
 private={'version':1,'visibility':'owner-only','papers':PAPERS,'countries':{}};public={'version':1,'visibility':'public','papers':PAPERS,'countries':{}}
 total=0
 for country,iv in inv['countries'].items():
  private['countries'][country]={};public['countries'][country]={}
  for s in iv['sources']:
   card={'composition':profiles[s['id']]['description'],'count_note':'Counts are record IDs, not independent events. Translations, passages and alternate task views can overlap.','tasks':{}}
   pc=copy.deepcopy(card)
   for t in s['tasks']:
    uid=t['sample']['uid'];loc=json.loads(db.execute('select locations from records where uid=?',(uid,)).fetchone()[0])[0]
    with (ROOT/loc['path']).open('rb') as f:f.seek(loc['offset']);o=json.loads(f.read(loc['length']))
    assert hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==uid
    es=examples(o,t['id'],country)
    card['tasks'][t['id']]={'record':o,'pointer':t['sample'],'examples':es,'recorded_groups':t.get('recorded_group_count'), 'missing_inputs':t.get('missing_input_fields')}
    pc['tasks'][t['id']]={'record':metadata(o),'pointer':t['sample'],'examples':[public_example(o)],'recorded_groups':t.get('recorded_group_count'),'missing_inputs':t.get('missing_input_fields')}
    total+=len(es)
   card['policy_examples']=[];pc['policy_examples']=[]
   custom={
    'france_mfa':('Nation européenne et de l’Indopacifique','La stratégie indopacifique de la France, multidimensionnelle', 'Would dividing the Indo-Pacific into exclusive spheres of influence match the strategy’s stated approach?', 'No. The strategy rejects bloc logic and division into spheres of influence, and favors partnerships and a non-confrontational approach while defending French interests. This does not determine France’s action on every specific dispute.'),
    'france_elysee':('La France sera attentive','L’exigence de la France', 'Does this passage promise an embassy in Palestine immediately and without conditions?', 'No. The speaker places a possible embassy decision in the negotiation framework and links it to release of all hostages held in Gaza and establishment of a ceasefire. It does not promise an unconditional immediate opening.'),
    'uk_fcdo':('There can be no answer except for the hostages out','Friends, we stand with Palestine', 'Does this stated position require choosing between hostage release and humanitarian access?', 'No. The speech calls for immediate hostage release, aid access and a ceasefire together, and envisages two states living side by side in peace and security. The passage does not establish an exclusive choice between these demands.'),
    'india_un_mission':('Central to the erosion of UN’s credibility','Madam President,', 'Would adding only non-permanent Security Council seats satisfy all the reforms requested in this passage?', 'No. The statement requests expansion of both permanent and non-permanent membership and a truly representative Council, including redress of the historical injustice to Africa. Adding only non-permanent seats would not cover the full stated request.'),
    'germany_aa':('Um diesen Punkt zu erreichen','Denn was uns', 'Does the speaker present pressure on Russia and NATO cohesion as alternatives?', 'No. The speaker advocates both greater pressure on Russia and continued NATO unity, presenting cohesion as especially important. These are the speaker’s stated priorities, not independent evidence that the measures will achieve their objective.')
   }
   if s['id'] in custom:
    begin,end,question,answer=custom[s['id']]
    originals=[v['record'] for v in card['tasks'].values()]
    for original in reversed(originals):
     body=original.get('text','');start=body.find(begin);stop=body.find(end,start+len(begin))
     if start<0 or stop<0:continue
     passage=body[start:stop].strip()
     ce=make('Apply the published position to a concrete proposal','Grounded policy-application SFT','Apply the supplied dated source. Attribute the position and retain conditions; do not invent a definite real-world decision.',j(metadata(original))+'\n\nComplete selected source passage:\n'+passage,question,answer,['raft','ca'],['New project-authored application, not an authentic answer or an admitted training row.',f'Exact selected source span: characters {start}–{start+len(passage)}. English answer is an authored paraphrase; original language is preserved in context.'])
     ce['provenance']=metadata(original);card['policy_examples'].append(ce)
     cp=make(ce['title'],ce['objective'],ce['system'],'Project-authored source summary:\n'+answer,question,answer,['raft','ca'],['Complete public example built from an authored source summary. This is interpretation practice, not an independent forecast.']);cp['provenance']=metadata(original);pc['policy_examples'].append(cp)
     break

   for p in policy:
    codes=p.get('countries',p.get('country_iso3'));codes=[codes] if isinstance(codes,str) else codes
    if country not in codes:continue
    ev=p.get('evidence',{});doc=ev.get('document_id','') if isinstance(ev,dict) else ''
    match=any(doc.startswith(a+':') for a in profiles[s['id']]['aliases']) or s['id']=='curated' or (s['id'] in ['national_policy_documents','germany_aa'] and not doc)
    if not match:continue
    e=examples(p,'policy_applications',country)[0];e['provenance']=metadata(p);card['policy_examples'].append(e)
    # Full authored policy claim context already published in the overview; no original source excerpts added publicly.
    claims=[]
    overview=json.loads((ROOT/'explorer/overview.json').read_text())
    for c in overview['countries']:
     for ex in c['examples']:
      if ex['id']==p['id']:claims=[v['claim'] for v in ex['evidence']]
    if claims:
     pub=make(e['title'],e['objective'],e['system'],'Project-authored source summaries:\n'+'\n'.join(claims),p.get('question') or p['messages'][1]['content'].rsplit('Question: ',1)[-1],e['completion'],e['papers'],['Complete worked example using published project paraphrases, not verbatim source passages.']+e['notes']);pub['provenance']=metadata(p);pc['policy_examples'].append(pub)
   # Existing DPO examples have source-specific identifiers in the aligned manifests.
   card['preference_examples']=[];pc['preference_examples']=[]
   for w,m in zip(workshop,wm):
    if country not in json.dumps(m):continue
    # Match case IDs to the applications attached to this card; curated collection includes all country cases.
    ids=[e.get('provenance',{}).get('id','').replace(':application','') for e in card['policy_examples']]
    if s['id']!='curated' and not any(i and i in json.dumps(m) for i in ids):continue
    pe={'title':'Grounded preference pair','objective':'DPO candidate','origin':'Existing authored chosen/rejected pair; not a sampled model failure','format':w,'notes':['Chosen and rejected answer the identical prompt. Rejected contains a controlled semantic error.','Ten underlying workshop cases only. Compare DPO with correction-SFT on the same cases; preserve connected source splits.'],'papers':['dpo','ca'],'provenance':m}
    card['preference_examples'].append(pe)
   # Public comparisons use complete project-authored factual summaries, not omitted passages.
   for pe in card['preference_examples']:
    f=pe['format'];pub=copy.deepcopy(pe)
    evidence=f['chosen'][0]['content']
    pub['origin']='New complete demonstration using project-authored policy summary; derived from existing controlled pair'
    pub['format']['prompt']=[message('system','Check the briefing against the supplied attributed policy summary. Preserve its qualifications.'),message('user','Project-authored summary of the source policy:\n'+evidence+'\n\nTask: Write a faithful briefing sentence from this summary.')]
    pub['notes'].append('The public evidence summary deliberately states the relevant facts; this tests fidelity, not hidden knowledge or forecasting.')
    pc['preference_examples'].append(pub)
   policy_extensions(card);policy_extensions(pc)
   private['countries'][country][s['id']]=card;public['countries'][country][s['id']]=pc
 for mode,data in [('private',private),('public',public)]:
  folder=ROOT/'.cache'/f'explorer-{mode}-static';folder.mkdir(exist_ok=True)
  (folder/'training-examples.json').write_text(j(data)+'\n')
 (ROOT/'explorer/training-examples.json').write_text(j(public)+'\n')
 (ROOT/'reports/training-examples-build.json').write_text(j({'countries':len(inv['countries']),'source_cards':sum(len(x['sources']) for x in inv['countries'].values()),'task_examples':total,'source_hashes_verified':True,'training_admission_changed':False})+'\n')
 print((ROOT/'reports/training-examples-build.json').read_text())

if __name__=='__main__':build()
