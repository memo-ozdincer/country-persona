"""Score the compact revision control and compare it with the original team arms."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

import source_record_review as review
from source_record_compact import ARMS, BASE, REVISION, FINAL, frozen_openings


def compare(folder, marks):
    old = json.loads((BASE / "scores.json").read_text())
    new = review.score(folder, marks)
    openings = frozen_openings()
    records = {r["id"]: r for r in map(json.loads, (folder / "transcript.jsonl").read_text().splitlines())}
    families = {}
    for identifier, answer in new.items():
        family, arm, stage = identifier.split("/")
        assert arm in ARMS and stage == "chair"
        chair = records[identifier]
        drafts = [records[f"{family}/{arm}/revision_{i}"] for i in (1, 2)]
        shared = [openings[f"{family}/common/opening_{i}"] for i in (1, 2)]
        for i, draft in enumerate(drafts):
            expected = [shared[i]["id"]] if arm == "independent_drafts" else [shared[i]["id"], shared[1-i]["id"]]
            assert draft["seen"] == expected and draft["cap"] == 160
            payload = json.loads(draft["messages"][-1]["content"])
            assert payload["task"] == REVISION
            assert tuple(payload["evidence"]) == tuple(draft["evidence_ids"])
            assert all(set(content) == {"type", "text"} for content in payload["working_text"])
            assert [x["text"] for x in payload["working_text"]] == [openings[x]["output"] for x in expected]
        assert chair["seen"] == [r["id"] for r in drafts] and chair["cap"] == 256
        assert FINAL in json.loads(chair["messages"][-1]["content"])["task"]
        stage_rows = [*shared, *drafts, chair]
        usage = {"input_tokens": sum(len(r["input_ids"]) for r in stage_rows),
                 "output_tokens": sum(len(r["output_ids"]) for r in stage_rows),
                 "output_ceiling": sum(r["cap"] for r in stage_rows),
                 "revision_caps_hit": sum(not r["ended"] for r in drafts),
                 "revision_words": [len(r["output"].split()) for r in drafts]}
        assert usage["output_ceiling"] == 896
        # A provisional draft ID is never a primary evidence citation.
        invalid_draft_refs = re.findall(
            rf"{re.escape(family)}/(?:interactive|independent_drafts|common)/[w/]+", chair["output"])
        families.setdefault(family, {})[arm] = {"original": old["final"][identifier], "compact": answer,
                                              "usage": usage,
                                              "original_usage": old["budgets"][f"{family}/{arm}"],
                                              "invalid_draft_refs": invalid_draft_refs}
    for arms in families.values():
        assert len(arms) == 2
    return {"scope": marks["scope"], "cases": families,
            "raw_sha256": sha256((folder/"transcript.jsonl").read_bytes()).hexdigest()}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--annotations", type=Path, required=True)
    args = cli.parse_args()
    value = compare(args.directory, json.loads(args.annotations.read_text()))
    print(json.dumps(value, indent=2, ensure_ascii=False))
