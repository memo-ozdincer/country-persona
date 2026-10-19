"""Replay two component answers and their exact, unedited 13-unit compositions."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from country_persona.io import sha256,write_json
from country_persona.scenario_sft import ids_digest,locked_runtime


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    pack=ROOT/"research/native-typed-composition-20261019-v1";run=ROOT/"runs/native-typed-composition-20261019-v1"
    for path,expected in json.loads((pack/"release.json").read_text())["files_sha256"].items():
        assert sha256(ROOT/path)==expected,path
    cfg=json.loads((pack/"config.json").read_text());protocol=json.loads((pack/"protocol.json").read_text());row=json.loads((pack/"example.json").read_text())
    assert sha256(ROOT/protocol["source_path"])==protocol["source_sha256"]
    assert sha256(ROOT/protocol["source_inspection_path"])==protocol["source_inspection_sha256"]
    source_record=json.loads((ROOT/protocol["source_path"]).read_text());source=source_record["output_display"]
    source_review=json.loads((ROOT/protocol["source_inspection_path"]).read_text())["records"][0]
    assert source_review["complete_output_contract_pass"] is True
    assert source==(pack/"locked-source.txt").read_text()
    assert len(source.split())==protocol["source_words"]==166
    assert cfg["component_word_budget"]+len(source.split())==cfg["whole_word_budget"]==240
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg["model_path"],local_files_only=True)
    ids=tok.apply_chat_template(row["messages"],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
    assert json.loads((run/"actual-input.json").read_text())==dict(**row,prefix_ids=ids,prefix_sha256=ids_digest(ids))
    launch=json.loads((run/"launch.json").read_text());assert launch["status"]=="completed"
    assert launch["production_generation_records"]==2 and launch["production_optimizer_updates"]==0
    assert launch["runtime"]==locked_runtime() and launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["adapter_digest"]==cfg["adapter_tensor_digest"]
    assert json.loads((run/"decoder.json").read_text())==json.loads((ROOT/cfg["decoder_path"]).read_text())
    for name,expected in cfg["adapter_files_sha256"].items():assert sha256(ROOT/cfg["adapter_path"]/name)==expected
    rubric=json.loads((pack/"rubric.json").read_text());whole_rubric=json.loads((pack/"whole-rubric.json").read_text());results={}
    for arm in ["base","adapter"]:
        dest=run/arm;response=json.loads((dest/"responses.jsonl").read_text());review=json.loads((dest/"inspection.json").read_text())
        assert review["complete_outputs_read"] is True and review["independent_review_complete"] is False
        assert review["responses_sha256"]==sha256(dest/"responses.jsonl") and review["rubric_sha256"]==sha256(pack/"rubric.json")
        assert response["prefix_sha256"]==ids_digest(ids)
        assert tok.decode(response["output_ids"],skip_special_tokens=False)==response["output_raw"]
        assert tok.decode(response["output_ids"],skip_special_tokens=True)==response["output_display"]
        assert len(response["output_ids"])==response["generated_tokens"] and not response["at_cap"]
        item=review["records"][0];assert len(review["records"])==1 and item["id"]==row["id"]==response["id"]
        assert item["words"]==len(response["output_display"].split())
        assert set(item["material"])==set(rubric["units"][row["id"]]) and set(item["guards"])==set(rubric["guards"])
        assert (item["guards"]["length"]=="met")== (item["words"]<=cfg["component_word_budget"])
        ratings=list(item["material"].values())+list(item["guards"].values())
        assert all(x in {"met","unmet","uncertain"} for x in ratings)
        assert item["strict_pass"]==all(x=="met" for x in ratings)
        composed=source+"\n\n"+response["output_display"]
        assert (dest/"composed.txt").read_text()==composed
        whole_review=json.loads((dest/"whole-inspection.json").read_text());assert whole_review["complete_outputs_read"] is True and whole_review["independent_review_complete"] is False
        assert whole_review["composed_sha256"]==sha256(dest/"composed.txt") and whole_review["rubric_sha256"]==sha256(pack/"whole-rubric.json")
        w=whole_review["records"][0];assert w["id"]==protocol["whole_case_id"] and w["words"]==len(composed.split())==len(source.split())+item["words"]
        assert set(w["material"])==set(whole_rubric["units"][w["id"]]) and set(w["guards"])==set(whole_rubric["guards"])
        assert len(w["material"])==13
        assert (w["guards"]["length"]=="met")== (w["words"]<=240)
        allratings=list(w["material"].values())+list(w["guards"].values())
        assert all(x in {"met","unmet","uncertain"} for x in allratings) and w["strict_pass"]==all(x=="met" for x in allratings)
        assert isinstance(item["requested_scope_followed"],bool) and isinstance(item["typed_provenance_followed"],bool)
        assert w["complete_output_contract_pass"]==(w["strict_pass"] and item["requested_scope_followed"] and item["typed_provenance_followed"])
        results[arm]=dict(component_words=item["words"],whole_words=w["words"],component_material=dict(Counter(item["material"].values())),
            whole_material=dict(Counter(w["material"].values())),whole_guards=dict(Counter(w["guards"].values())),whole_strict_pass=w["strict_pass"],
            scope_followed=item["requested_scope_followed"],typed_provenance_followed=item["typed_provenance_followed"],
            full_contract_pass=w["complete_output_contract_pass"],generated_tokens=response["generated_tokens"])
    write_json(a.output,dict(status="two_typed_components_and_unedited_13_unit_whole_documents_replayed",new_generation_records=2,
        reused_source_generation_records_not_double_counted=1,additional_writer_calls=0,optimizer_updates=0,cumulative_qwen35_updates=4182,
        source_words=166,component_budget=74,whole_budget=240,results=results,independent_semantic_review_complete=False,
        scope="One adaptive same-source composition prototype with shared verified model source and provided action rule; no original-task repair or persona/collective/strongOOD claim."))
    print(json.dumps(json.loads(a.output.read_text()),indent=2))


if __name__=="__main__":main()
