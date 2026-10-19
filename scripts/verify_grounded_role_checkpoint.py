"""Replay actual sources, native input/output tokens and review arithmetic.

This checks provenance/serialization; it does not independently judge semantics.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.scenario_sft import ids_digest, locked_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    assert not a.output.exists()
    config = json.loads((ROOT/"research/scenario-role-sft-20261017-v1/fit-config.json").read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
    summary = dict(scope="Software/provenance replay, not independent semantic assessment", packs={}, generated_records=0)
    names = ["grounded-role-20261019-v1", "grounded-role-cards-20261019-v1", "grounded-role-cards-20261019-v2", "grounded-role-pipeline-20261019-v1", "grounded-role-budget-20261019-v1"]

    def check_record(r, expected_messages, cap):
        messages = r.get("messages", expected_messages)
        assert messages == expected_messages
        ids = tok.apply_chat_template(messages, tokenize=True, return_dict=False,
            add_generation_prompt=True, enable_thinking=False)
        assert len(ids)+cap<=8192
        assert r.get("prefix_sha256") == ids_digest(ids)
        if "prefix_ids" in r:
            assert r["prefix_ids"]==ids
        assert tok.decode(r["output_ids"],skip_special_tokens=False)==r["output_raw"]
        assert tok.decode(r["output_ids"],skip_special_tokens=True)==r["output_display"]
        assert r["generated_tokens"]==len(r["output_ids"])
        assert not r["at_cap"]
        summary["generated_records"]+=1

    def review(path, responses, rubric_path, response_path):
        r = json.loads(path.read_text())
        assert r["responses_sha256"]==sha256(response_path)
        assert r["rubric_sha256"]==sha256(rubric_path)
        assert r["complete_outputs_read"] is True and r["independent_review_complete"] is False
        rubric = json.loads(rubric_path.read_text())
        assert set(r["answers"])=={x["id"] for x in responses}
        counts, guards, passes = Counter(), Counter(), 0
        for x in responses:
            item = r["answers"][x["id"]]
            country=x.get("country", x["id"].rsplit('-',1)[1])
            assert set(item["units"])==set(rubric["units"][country])
            assert set(item["guards"])==set(rubric["guards"])
            assert item["words"]==len(x["output_display"].split())
            ratings=[v["rating"] for k in ["units","guards"] for v in item[k].values()]
            assert all(v in {"met","unmet","uncertain"} for v in ratings)
            strict=all(v=="met" for v in ratings)
            assert strict==item["strict_pass"]
            passes+=strict
            counts.update(v["rating"] for v in item["units"].values())
            guards.update(v["rating"] for v in item["guards"].values())
        return dict(answers=len(responses),units=dict(counts),guards=dict(guards),strict_passes=passes,
                    inspection_sha256=sha256(path),responses_sha256=sha256(response_path))

    for name in names:
        pack=ROOT/"research"/name
        release=json.loads((pack/"release.json").read_text())
        for path, expected in release["files_sha256"].items():
            assert sha256(ROOT/path)==expected, path
        info=dict(frozen_files_verified=len(release["files_sha256"]))
        if (pack/"grounding.json").exists():
            grounding=json.loads((pack/"grounding.json").read_text())
            for span in grounding["spans"]:
                source=ROOT/span["path"]
                assert sha256(source)==span["source_sha256"]
                assert source.read_text()[span["start"]:span["end"]]==span["quote"]
                if span.get("date")=="2022-09-27":
                    assert span["end"]<grounding["current_cutoff_character"]
            info["source_spans_replayed"]=len(grounding["spans"])
        runtime=pack/"runtime"
        if not runtime.exists():
            info["production_answers"]=0
            summary["packs"][name]=info
            continue
        launch=json.loads((runtime/"launch.json").read_text())
        assert launch["status"]=="completed" and launch["runtime"]==locked_runtime()
        assert launch["production_optimizer_updates"]==0
        assert launch["release_sha256"]==sha256(pack/"release.json")
        assert launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        info["production_answers"]=launch["production_generated_answers"]
        before=summary["generated_records"]
        if "pipeline" not in name:
            examples=json.loads((pack/"examples.json").read_text())
            actual=json.loads((runtime/"actual-inputs.json").read_text())
            assert all(x["messages"]==y["messages"] for x,y in zip(examples,actual))
            info["arms"]={}
            for arm in launch["completed_stages"]:
                path=runtime/arm/"responses.jsonl"
                records=[json.loads(s) for s in path.read_text().splitlines()]
                assert len(records)==len(examples)==2
                for record,row in zip(records,examples):
                    assert record["id"]==row["id"]
                    check_record(record,row["messages"],2048)
                info["arms"][arm]=review(runtime/arm/"inspection.json",records,pack/"rubric.json",path)
        else:
            record=json.loads((runtime/"reader-response.json").read_text())
            check_record(record,json.loads((pack/"reader.json").read_text()),3072)
            writer_path=runtime/"writer-responses.jsonl"
            if writer_path.exists():
                inspection=json.loads((runtime/"reader-inspection.json").read_text())
                assert inspection["reader_response_sha256"]==sha256(runtime/"reader-response.json")
                assert inspection["complete_output_read"] is True
                rows=json.loads((ROOT/"research/grounded-role-cards-20261019-v2/examples.json").read_text())
                records=[json.loads(s) for s in writer_path.read_text().splitlines()]
                assert len(records)==2
                for row,r in zip(rows,records):
                    common,role=row["messages"][1]["content"].split("\n\nREQUESTED ROLE:")
                    expected=[row["messages"][0],dict(role="user",content=common+"\n\nMODEL-EXTRACTED WORKING MAP (fallible notes, not new government authority):\n"+record["output_display"]+"\n\nREQUESTED ROLE:"+role)]
                    check_record(r,expected,2048)
                    assert r["unedited_reader_response_sha256"]==sha256(runtime/"reader-response.json")
                info["writer"]=review(runtime/"writer-inspection.json",records,pack/"rubric.json",writer_path)
        assert summary["generated_records"]-before==info["production_answers"]
        summary["packs"][name]=info
    summary.update(status="actual_tokens_sources_and_review_arithmetic_replayed",new_optimizer_updates=0,
                   cumulative_qwen35_updates=4062,independent_semantic_review_complete=False)
    write_json(a.output,summary)
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
