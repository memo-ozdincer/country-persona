"""Build dated, retrospective decision cases without inferring private bargaining limits."""
import csv
import json
import re
from pathlib import Path
from country_persona.io import sha256, write_json, write_jsonl

RAW=Path('data/raw/decision-cases-20260914')
OUT=Path('data/prepared/decision-cases-20260914')
NAMES={'BRA':'Brazil','CHN':'China','DEU':'Germany','FRA':'France','GBR':'United Kingdom','IND':'India'}

def span(path, start=None, end=None):
    text=Path(path).read_text()
    a=text.index(start) if start else 0
    b=text.index(end,a+len(start)) if end else len(text.rstrip())
    return {'text_file':str(path),'text_sha256':sha256(path),'char_start':a,'char_end':b,
            'pdf_pages':list(range(text[:a].count('\f')+1,text[:b].count('\f')+2))}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources={r['id']:r for r in json.loads((RAW/'collection.json').read_text())}
    for r in sources.values():
        assert sha256(r['raw_file'])==r['sha256']
    rows=[]
    old=list(map(json.loads,Path('data/prepared/country-knowledge-20260914/actions.jsonl').open()))
    for r in old:
        code=r['country_iso3']
        constraints={'BRA':['Brazil warned against reading support as permission for indiscriminate sanctions or arms deployments.'],
                     'IND':['India emphasized evacuation of civilians and humanitarian access.'],
                     'CHN':['China raised consultation, security concerns and diplomatic settlement.']}.get(code,[])
        rows.append({'id':'decision:'+r['id'],'schema_version':'decision-case-1.0','record_type':'decision_case',
            'country_iso3':code,'country_name':NAMES[code],'event_date':r['date'],'issue':'ukraine_territorial_integrity',
            'title':'Aggression against Ukraine — March 2022','proposal_symbol':'A/ES-11/L.1','resolution_symbol':'A/RES/ES-11/1',
            'proposal_summary':'The draft condemns the aggression against Ukraine and demands that Russia end its use of force and withdraw its forces.',
            'proposal_evidence':dict(span(sources['draft1']['text_file']),source_url=sources['draft1']['url']),
            'observed_action':r['original_vote'],'amended_action':r['amended_vote'],
            'vote_evidence':{'source_url':'https://docs.un.org/A/ES-11/PV.5','pdf_pages':[14,15],'bulk_csv_line':r['csv_line'],'primary_roll_call_verified':True},
            'public_explanation':r['public_explanation_summary'],'explanation_kind':'explanation_of_vote' if r['explanation_evidence'] else 'not_acquired',
            'explanation_evidence':dict(r['explanation_evidence'],source_url='https://docs.un.org/A/ES-11/PV.5') if r['explanation_evidence'] else None,
            'stated_considerations':constraints,'requested_changes':[],
            'conditions_for_agreement':None,'conditions_status':'No necessary-and-sufficient bargaining condition established.',
            'material_context':[],'missing_context':['Independently sourced contemporaneous material constraints','Verified necessary conditions for agreement']+([] if r['explanation_evidence'] else ['Attributed explanation']),
            'group_id':'unga:meeting:ES-11:5','related_group_ids':[r['group_id'],'A/ES-11/L.1','A/RES/ES-11/1']})
    transcript=Path(sources['meeting4']['text_file']).read_text()
    anchors={
      'FRA':('Mr. De Rivière (France)','Mr. Geng Shuang (China)', 'pre_vote_statement',
             'France rejected recognition of annexation and urged support for the text as a defence of Charter principles.', ['Non-recognition of annexation and defence of territorial integrity.'],[]),
      'CHN':('Mr. Geng Shuang (China)','Mrs. Thomas-Greenfield', 'pre_vote_statement',
             'China emphasized negotiations, humanitarian relief and limiting spillover harms. This statement is context, not an explicit explanation of its recorded abstention.', ['Diplomatic settlement, civilian protection and effects on developing countries.'],[]),
      'IND':('Mrs. Kamboj (India)','I wish to make one final point', 'explanation_of_vote',
             'India explained its abstention through diplomacy and concerns about food, fuel and fertilizer impacts on developing countries.', ['Avoid measures that further complicate the global economy.'],[]),
      'BRA':('Mr. De Almeida Filho (Brazil)','Mr. Pedroso Cuesta (Cuba)', 'explanation_of_vote',
             'Brazil supported territorial integrity despite omission of its proposed explicit call to cease hostilities and negotiate.', ['Territorial integrity; diplomacy; rejection of nuclear use.'],['Include an explicit call to cease hostilities and engage in peace negotiations.'])}
    # Verify the six labels against the primary roll-call sections, preserving exact bulk labels.
    yes=transcript.split('In favour:',1)[1].split('Against:',1)[0]
    abstain=transcript.split('Abstaining:',1)[1].split('Draft resolution A/ES-11/L.5 was adopted',1)[0]
    with Path('data/raw/unga_dm/votes.csv').open() as f:
      for line,r in enumerate(csv.DictReader(f),2):
        if r['decision_id']!='A/RES/ES-11/4-FP' or r['member_state'] not in NAMES.values():continue
        code=next(k for k,v in NAMES.items() if v==r['member_state'])
        seat=' '.join(r['current_seat_name'].split())
        section=yes if r['original_vote']=='in favor' else abstain
        assert seat in ' '.join(section.split()),(code,r['original_vote'])
        a=anchors.get(code); e=None
        if a:
          e=dict(span(sources['meeting4']['text_file'],a[0],a[1]),source_url=sources['meeting4']['url'])
        rows.append({'id':f'decision:{code}-ES-11-4-20221012','schema_version':'decision-case-1.0','record_type':'decision_case',
          'country_iso3':code,'country_name':NAMES[code],'event_date':r['meeting_date'],'issue':'ukraine_territorial_integrity',
          'title':'Territorial integrity of Ukraine — October 2022','proposal_symbol':'A/ES-11/L.5','resolution_symbol':'A/RES/ES-11/4',
          'proposal_summary':'The draft rejects the referendums and attempted annexation, calls for non-recognition, demands reversal and withdrawal, and supports peaceful resolution.',
          'proposal_evidence':dict(span(sources['draft4']['text_file']),source_url=sources['draft4']['url']),
          'observed_action':r['original_vote'],'amended_action':r['amended_vote'],
          'vote_evidence':{'source_url':sources['meeting4']['url'],'raw_sha256':sources['meeting4']['sha256'],'pdf_pages':[11,12],'bulk_csv_line':line,'primary_roll_call_verified':True},
          'public_explanation':a[3] if a else None,'explanation_kind':a[2] if a else 'not_acquired','explanation_evidence':e,
          'stated_considerations':a[4] if a else [],'requested_changes':a[5] if a else [],
          'conditions_for_agreement':None,'conditions_status':'Brazil voted in favor despite omission: its requested change was not a necessary condition for this vote.' if code=='BRA' else 'No necessary-and-sufficient bargaining condition established.',
          'material_context':[],'missing_context':['Independently sourced contemporaneous material constraints','Verified necessary conditions for agreement']+([] if a else ['Attributed explanation']),
          'group_id':'unga:meeting:ES-11:14','related_group_ids':['unga:decision:'+r['decision_id'],'A/ES-11/L.5','A/RES/ES-11/4']})
    assert len(rows)==12 and len({r['id'] for r in rows})==12
    for r in rows:
        r.update({'language':'en','represented_entity':r['country_name'],'source_url':r['vote_evidence']['source_url'],
          'split':'quarantine','training_admitted':False,'fresh_evaluation_eligible':False,
          'review_status':'source_checked_independent_review_pending','use':'retrospective_reconstruction_only',
          'private_motive':None,'author':'Memo Ozdincer','derivation':'assistant_prepared_source_grounded_paraphrase',
          'source_coverage':'proposal_and_vote_and_attributed_statement' if r['explanation_evidence'] else 'proposal_and_vote_only'})
    write_jsonl(OUT/'cases.jsonl',rows)
    manifest={'sources':list(sources.values()),'cases':len(rows),'events':2,'with_attributed_statement':sum(bool(r['explanation_evidence']) for r in rows),'independent_review_complete':False,'training_admitted':0,'artifact_sha256':sha256(OUT/'cases.jsonl')}
    write_json('data/manifests/decision-cases-20260914.json',manifest)
    print({k:v for k,v in manifest.items() if k!='sources'})
if __name__=='__main__':main()
