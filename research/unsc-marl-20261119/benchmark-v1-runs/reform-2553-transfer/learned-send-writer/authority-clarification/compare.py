"""Replay the delivered-source scores and compare the scoped writer to baseline."""
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from unittest.mock import patch

import scope_prompt

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
spec = spec_from_file_location("paired_2553_scores", PARENT / "score.py")
score = module_from_spec(spec)
spec.loader.exec_module(score)


def run():
    with patch.object(score, "HERE", HERE), patch.object(score.writer, "locked", scope_prompt.locked):
        output = score.run()
    old = json.loads((PARENT / "scores.json").read_text())
    packets = json.loads((HERE / "verified.json").read_text())["packets"]
    authorities = json.loads((HERE / "authority.json").read_text())
    assert set(authorities) == set(packets)
    counts = Counter()
    for id_, entry in authorities.items():
        assert entry["status"] in {"clear_distinction", "incomplete", "conflated", "ambiguous"}
        assert entry["span"] and entry["span"] in packets[id_]["reply"]["text"]
        counts[entry["status"]] += 1
    output["authority_attribution"] = dict(counts)
    output["authority_marks_sha256"] = scope_prompt.baseline.pin(HERE / "authority.json")
    output["comparison"] = {
        "original_release_count": sum(x["release"] for x in old["grades"].values()),
        "clarified_release_count": sum(x["release"] for x in output["grades"].values()),
        "original_pair_delta": old["expected_differences"],
        "original_scores_sha256": scope_prompt.baseline.pin(PARENT / "scores.json"),
    }
    return output


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
