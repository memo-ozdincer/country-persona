"""Score the longer whole-packet outputs against the same field receipts."""
import json
from unittest.mock import patch

import cap_control
import results
import writer

HERE = results.HERE
DIRECTORY = HERE / "cap-evidence"


def run():
    with patch.multiple(writer, build=cap_control.build, locks=cap_control.locks):
        active = writer.replay(DIRECTORY)
    original = {r["id"]: r for r in map(json.loads, (HERE / "evidence/transcript.jsonl").read_text().splitlines())}
    scoring = results.load(HERE / "cap-annotations.json")
    assert scoring["transcript_sha256"] == writer.runner.digest(DIRECTORY / "transcript.jsonl")
    main = results.load(HERE / "evidence/results.json")
    case = results.load(writer.CASE)
    verified = results.verified_bank(case)
    rows = {}
    for name, receipt in active.items():
        prior = original[name]
        assert receipt["messages"] == prior["messages"] and receipt["input_ids"] == prior["input_ids"]
        ids = frozenset(receipt["evidence_ids"])
        proof = verified[ids]["proof"]
        body = results.checked(receipt, scoring["records"][name], proof.keys() - {"procedure"})
        rendered = results.compose([body], case, ids, proof)
        assert rendered["sum_of_caps"] == main["matched_receipts"][name]["separate_fields"]["sum_of_caps"]
        rows[name] = {"whole_original": main["matched_receipts"][name]["whole_packet"],
                      "whole_equal_cap": rendered, "separate_fields": main["matched_receipts"][name]["separate_fields"],
                      "original_generation_is_exact_prefix": receipt["output_ids"][:len(prior["output_ids"])] == prior["output_ids"]}
    return {"scope": "Only the configured output cap changes. Source and prompt tokens match. "
                     "The separate-field input cost and number of calls still differ.",
            "records": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
