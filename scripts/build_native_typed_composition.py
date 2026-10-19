"""Lock one actual source output; test a typed companion in its remaining budget."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/native-typed-composition-20261019-v1"


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,default=OUT)
    OUT=parser.parse_args().output.resolve()
    assert not OUT.exists()
    source_run=ROOT/"runs/native-scope-partial-writer-20261019-v1"
    source_file=source_run/"brazil_source/responses.jsonl"
    source_record=json.loads(source_file.read_text());source=source_record["output_display"]
    source_review=json.loads((source_run/"brazil_source/inspection.json").read_text())["records"][0]
    assert source_review["complete_output_contract_pass"] is True
    source_words=len(source.split());budget=240-source_words;assert budget==74
    parent=ROOT/"research/native-state-decomposition-20261019-v1/missing-outside"
    row=json.loads((parent/"example.json").read_text());old_id=row["id"];row["id"]="typed-composition-9469-BRA"
    row["messages"][0]["content"]=row["messages"][0]["content"].replace("at most 240 words",f"at most {budget} words")
    suffix="\nREQUESTED ROLE: BRA national delegation."
    assert row["messages"][1]["content"].endswith(suffix)
    instruction=("\nLOCKED SOURCE PART\nThe following is an already written, verified model paraphrase of the dated source positions. "
        "It is not an authentic quotation or a statement that workplan R existed historically. It will be retained verbatim outside your reply.\n"+source+
        "\nCOMPANION APPLICATION TASK\nWrite only the companion application paragraph, at most "+str(budget)+" words, so the combined document remains at most240. "
        "Use three short labeled parts within the paragraph: R now: give only fictional R's existing provisions and remaining gaps. "
        "Workshop recommendation: give selected repairs and their practical competing cost, rather than merely listing possible options. "
        "Authority: identify workshop analysis and the unestablished official Brazilian endorsement of R/future vote. "
        "Name R as the owner of its provisions; do not describe them as programmes or concrete services established by Brazil's historical speech. "
        "Do not repeat or rewrite the locked source part.")
    row["messages"][1]["content"]=row["messages"][1]["content"][:-len(suffix)]+instruction+suffix
    rubric=json.loads((parent/"rubric.json").read_text());rubric["units"]={row["id"]:rubric["units"][old_id]}
    rubric["guards"]["length"]=f"Application component at most{budget} whitespace words; unedited source+application at most240."
    rubric["scope"]="Typed application component plus deterministic composition of one actual source output. Not a matched-input repair of original ambiguous R or a single-generation endpoint."
    source_rubric=json.loads((ROOT/"research/native-scope-partial-writer-20261019-v1/rubric.json").read_text())
    whole=json.loads(json.dumps(rubric));whole_id="whole-"+row["id"]
    whole["units"]={whole_id:{**source_rubric["units"][source_record["id"]],**rubric["units"][row["id"]]}}
    whole["guards"]["length"]="Whole unedited source+application at most240 whitespace-separated words."
    cfg=json.loads((parent/"config.json").read_text());training=json.loads((source_run/"training-result.json").read_text())
    cfg.update(adapter_path=str((source_run/"adapter").relative_to(ROOT)),adapter_files_sha256=training["serialization"]["files_sha256"],
        adapter_tensor_digest=training["update"]["final_adapter_digest"],decoder_path=str((source_run/"decoder.json").relative_to(ROOT)),
        source_words=source_words,component_word_budget=budget,whole_word_budget=240,cumulative_qwen35_updates=4182)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    protocol=dict(question="Can explicit provenance labels and separate budgets preserve all source/application meaning in a full240word prototype without more training?",
        planned_new_answers=2,optimizer_updates=0,source_call_reused_not_regenerated=True,
        source_path=str(source_file.relative_to(ROOT)),source_sha256=sha(source_file),source_inspection_path=str((source_run/"brazil_source/inspection.json").relative_to(ROOT)),
        source_inspection_sha256=sha(source_run/"brazil_source/inspection.json"),source_case_id=source_record["id"],
        component_budget=budget,source_words=source_words,whole_budget=240,
        whole_case_id=whole_id,
        composition="Exact output_display source + two newline characters + exact application output_display. No human edits, truncation or additional writer call.",
        intervention="Same fully specified missing-outside plan/dossier/map/rule; add shared verified source draft, explicit ownership labels and remaining-word budget. Source/wording/order/budget representation change together; no isolated prompt-factor causal claim.",
        strong_base_control="Same common native48-generated source, complete raw sources/maps, rule and exact application input to both base and saved native48. Base source223word answer is not a different arm history.",
        scope="One adaptive same-episode composition prototype, historically exposed source and provided conditional action rule. Not independent review, sealedOOD, private utility, persona/diplomatic/collective gain or proof that original direct full task is repaired.",
        independent_review_complete=False,old_seed_control="preserved/unrun")
    OUT.mkdir()
    for name,value in [("example",row),("rubric",rubric),("whole-rubric",whole),("config",cfg),("protocol",protocol)]:
        (OUT/(name+".json")).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
    (OUT/"example.txt").write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+"\n")
    (OUT/"locked-source.txt").write_text(source)
    ref=("R now: Cooperation, a public update and protected inside-Libya outreach are funded; outside coverage and four-inquiry detail are missing. "
         "Workshop recommendation: Extend the existing channel outside and request line-by-line updates. Broader outreach/reporting needs staff and witness-privacy safeguards; cheaper narrower outreach risks selectivity. "
         "Authority: This is workshop analysis, not observed Brazilian endorsement of R or an established future vote.")
    assert len(ref.split())<=budget
    (OUT/"feasibility-not-for-model.json").write_text(json.dumps(dict(author="same assistant",not_model_input_or_target=True,not_model_output_or_official_quote=True,
        text=ref,component_words=len(ref.split()),whole_words=source_words+len(ref.split())),indent=2)+"\n")
    print(json.dumps(dict(locked_source_words=source_words,component_budget=budget,reference_words=len(ref.split()),reference_whole_words=source_words+len(ref.split()))))
