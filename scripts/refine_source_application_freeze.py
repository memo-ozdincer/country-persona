"""Preserve first preparation and freeze clearer atomic criteria/provenance before calls."""
from pathlib import Path
import sys,json,shutil
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import sha256,digest,write_json,write_jsonl,read_jsonl

def main():
 old=ROOT/'data/prepared/source-application-sft-20261003-v1';out=ROOT/'data/prepared/source-application-sft-20261003-v2';oe=ROOT/'data/prepared/source-application-eval-20261003-v1';ev=ROOT/'data/prepared/source-application-eval-20261003-v2'
 if out.exists() or ev.exists():raise ValueError('Fresh revised preparation required')
 shutil.copytree(old,out);shutil.copytree(oe,ev)
 teachers=list(read_jsonl(out/'teacher-records.jsonl'))
 for t in teachers:
  t['teacher_authoring_context_specification']=t.pop('teacher_input');t['provenance']='Reconstructed source-plus-private-plan authoring specification; synthetic target authored by this session assistant. Not an API transcript or a captured standalone model call.'
 write_jsonl(out/'teacher-records.jsonl',teachers)
 # Machine-check exact source anchors; author checked complete targets separately.
 san=json.loads((ROOT/'data/raw/source-plan-grounding-20261002-v1/statements.json').read_text());clim={r['id'].split('-')[-1].upper():r for r in read_jsonl(ROOT/'data/prepared/evidence-format-20260928-v1/evidence.jsonl') if r['id'].startswith('climate-')}
 quotes={
 'san-BRA':['Brazil’s vote in favour','disproportionately affect vulnerable populations','worsen food insecurity, increase inflation','more predictable conditions','important tool for the maintenance of international peace and security','legitimate security concerns'],
 'san-IND':['provisional in nature and not permanent','legitimate trade and economic activities','timely delivery of humanitarian assistance','raise funds and recruit fighters','mainstreaming of terror entities in the political space','proactive role for the 1267 Monitoring Team','robust reporting standards and mechanisms','not fully addressed'],
 'clim-FRA':['appropriate for the Security Council','better allocation of natural resources','predictable and sustainable logistical and financial support','region by region','France’s full and complete commitment'],
 'clim-GBR':['multiplier of the threats','existential threat','Counter-Terrorism Committee Executive Directorate','support the draft resolution submitted','women and girls'],
 'clim-IND':['inclusive process of decision-making','$1 trillion','net zero by the year 2070','G-5 Sahel Joint Force','Any action in the Security Council ignoring'],
 'clim-BRA':['Terrorism is not directly linked to climate change','international human rights law and international humanitarian law','inclusive and balanced manner','timely delivery of financing','cautious stance']}
 anchors=[]
 for key,qs in quotes.items():
  family,c=key.split('-');s=(san if family=='san' else clim)[c]['text']
  for q in qs:
   a=s.find(q)
   if a<0:raise ValueError('Source anchor missing: '+q)
   anchors.append({'family':family,'country':c,'quote':q,'start':a,'end':a+len(q),'source_text_digest':digest(s)})
 write_json(out/'source-anchor-audit.json',{'anchors':anchors,'negative_checks':'Complete Brazil sanctions speech lacks categorical 1267 demand; UK/Brazil climate speeches lack explicit G-5 support. These are bounded absences, not national opposition.','all_20_actual_complete_targets_read':True,'reviewer':'same assistant; no independent semantic certification','separate_family_evaluation_material_in_optimization':False})
 for pack in [out,ev]:shutil.copy2(__file__,pack/'refinement.py')
 r=json.loads((out/'release.json').read_text());r.update(created_utc=datetime.now(timezone.utc).isoformat(),supersedes_preparation=str(old.relative_to(ROOT)),refinement='Clarify reconstructed teacher authoring specification; add exact source anchors after full target inspection; training rows unchanged.',files_sha256={p.name:sha256(p) for p in out.iterdir() if p.name!='release.json'});write_json(out/'release.json',r)
 criteria=json.loads((ev/'criteria.json').read_text());updates={'H1':'Recognize historical welcome/support for adoption of resolution 2467.','H4':'Preserve the national criticism of health-care-language omissions despite adoption; do not equate adoption/support with accepting every omission.'}
 criteria['common']=[[u,updates.get(u,d)] for u,d in criteria['common']];write_json(ev/'criteria.json',criteria)
 cases=list(read_jsonl(ev/'cases.jsonl'))
 for c in cases:
  c['units']=[[u,updates.get(u,d)] for u,d in c['units']];c['case_sha256']=digest({k:v for k,v in c.items() if k!='case_sha256'})
 write_jsonl(ev/'cases.jsonl',cases)
 held=json.loads((ROOT/'data/raw/source-application-grounding-20261003-v1/statements.json').read_text());qa={'FRA':['France welcomes the adoption','approach focused on the survivors','full access to sexual and reproductive health care and rights in every context','omission is unacceptable','continue to support and promote that approach','right to decide to terminate their pregnancies','including paragraph 19 of resolution 2106'], 'GBR':['successful outcome to resolution 2467','recognition of the survivor-centred approach','comprehensive reproductive and sexual health care','deeply regret the language','United Kingdom will continue to support access','important role that civil society plays','justice and accountability']}
 ha=[]
 for c,qs in qa.items():
  s=held[c]['text']
  for q in qs:
   a=s.find(q)
   if a<0:raise ValueError('Held source anchor missing: '+q)
   ha.append({'country':c,'quote':q,'start':a,'end':a+len(q),'source_text_digest':digest(s)})
 write_json(ev/'source-criterion-audit.json',{'anchors':ha,'application_scope':'Hypothetical proposals, not observed counterfactual national decisions. Multiple defensible recommendations allowed within access/attribution boundaries.','bounded_absence':'UK selected post-vote statement does not explicitly state France\'s pregnancy-termination formulation; neither speech guarantees a future Council vote. Their real continuing health-care support commitments ARE explicit.','reviewer':'same assistant; no independent reviewer'})
 m=json.loads((ev/'manifest.json').read_text());m.update(created_utc=datetime.now(timezone.utc).isoformat(),supersedes_preparation=str(oe.relative_to(ROOT)),refinement='Separate historical welcome (H1) from omitted-language criticism (H4); explicit primary source anchors. Zero prior model calls on this event.',training_release_sha256=sha256(out/'release.json'),files_sha256={p.name:sha256(p) for p in ev.iterdir() if p.name!='manifest.json'});write_json(ev/'manifest.json',m)
 c=json.loads((ROOT/'configs/posttraining/qwen35-source-application-fit-20261003.json').read_text());c.update(training_pack=str(out.relative_to(ROOT)),training_release_sha256=sha256(out/'release.json'),eval_pack=str(ev.relative_to(ROOT)),eval_manifest_sha256=sha256(ev/'manifest.json'));write_json(ROOT/'configs/posttraining/qwen35-source-application-fit-20261003-v2.json',c)
 print({'training_rows_unchanged':sha256(old/'train.jsonl')==sha256(out/'train.jsonl'),'source_anchors':len(anchors),'held_source_anchors':len(ha),'eval_manifest_sha256':sha256(ev/'manifest.json')})

if __name__=='__main__':main()
