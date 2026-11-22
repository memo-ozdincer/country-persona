"""Audit a typographic apostrophe equivalence without editing the transcript."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_validated_accounts as study


def canonical(s):
    return s.replace("\N{RIGHT SINGLE QUOTATION MARK}", "'")


def run(rows):
    raw_score = study.score(rows)
    witness = study.witness

    def check(row, card):
        messages = deepcopy(row["messages"])
        body = json.loads(messages[-1]["content"])
        body["source"] = canonical(body["source"])
        messages[-1]["content"] = json.dumps(body, ensure_ascii=False)
        return witness({**row, "messages": messages, "output": canonical(row["output"])},
                       {**card, "source": canonical(card["source"])})

    with patch.object(study, "witness", check):
        scores = study.score(rows)
    assert scores["sha256"] == raw_score["sha256"]
    scores["typography_audit"] = {
        "mapping": {"\N{RIGHT SINGLE QUOTATION MARK}": "'"},
        "prior_release_bank": raw_score["released_bank"],
        "fields_changed": {
            k: [i for i, (before, after) in enumerate(zip(v["fields"], scores["witnesses"][k]["fields"], strict=True), 1)
                if before != after]
            for k, v in raw_score["witnesses"].items()
        },
        "scorer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return scores


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    print(json.dumps(run(study.verify(args.directory)), ensure_ascii=False, indent=2))
