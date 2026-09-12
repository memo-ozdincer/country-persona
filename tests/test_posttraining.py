import pytest
from country_persona.posttraining import event_order
from country_persona.train import validated_export
from country_persona.evaluate import check_case
from country_persona.io import write_jsonl,digest


def test_event_first_selection_does_not_let_one_conference_dominate():
    rows=[({}, {'id':str(i),'split_group':'large'}) for i in range(10)]
    rows +=[({}, {'id':'x','split_group':'small'})]
    selected=event_order(rows)
    assert len({m['split_group'] for _,m in selected[:2]})==2
    assert event_order(rows)==event_order(list(reversed(rows)))


def test_research_release_is_explicit_and_never_claims_human_approval(tmp_path):
    row={'prompt':[{'role':'user','content':'Q'}],'completion':[{'role':'assistant','content':'A'}]}
    m={'id':'one','row_index':0,'split':'train','example_sha256':digest(row),'status':'research_prepared',
       'machine_checks_passed':True,'human_reviewed':False,'model_revision':'abc','tokenizer_lock_sha256':'hash'}
    write_jsonl(tmp_path/'d.jsonl',[row]);write_jsonl(tmp_path/'m.jsonl',[m])
    with pytest.raises(ValueError,match='admitted'):validated_export(tmp_path/'d.jsonl',tmp_path/'m.jsonl','train')
    _,metas=validated_export(tmp_path/'d.jsonl',tmp_path/'m.jsonl','train',True)
    assert metas[0]['human_reviewed'] is False
    with pytest.raises(ValueError,match='Expected dev'):validated_export(tmp_path/'d.jsonl',tmp_path/'m.jsonl','dev',True)


def test_changed_evidence_invalidates_comparison():
    case={'id':'a','prompt':[{'role':'user','content':'original evidence'}]}
    case['case_sha256']=digest(case);check_case(case)
    case['prompt'][0]['content']='different evidence'
    with pytest.raises(ValueError,match='hash'):check_case(case)


def test_event_bootstrap_weights_events_not_repeated_rows():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('review_scorer',Path(__file__).parents[1]/'scripts/score_reviews.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cases=[];reviews=[]
    for i in range(11):
        cases.append({'id':str(i),'split_group':'large' if i<10 else 'small','country':'CHN','suite':'qa','condition':'plain'})
        for run,score in [('before',0),('after',2 if i<10 else 0)]:
            reviews.append({'case_id':str(i),'run':run,'reviewer':'fixture-reviewer','position_fidelity_0_to_2':str(score),
                'unsupported_commitment':'0','attribution_error':'0','supported_claims':'1','total_checkable_claims':'1'})
    result=module.summarize(cases,reviews,'before','after')
    fidelity=next(r for r in result['results'] if r['metric']=='fidelity')
    assert fidelity['paired_change']==.5 and fidelity['event_groups']==2
    with pytest.raises(ValueError,match='No paired'):module.summarize(cases,[],'before','after')
