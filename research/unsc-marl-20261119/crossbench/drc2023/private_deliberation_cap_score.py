"""Compare factual survival at two reporter caps and with verbatim forwarding."""
import json

import private_deliberation_caps as experiment
from private_deliberation_score import RUBRIC

HERE = experiment.HERE
EVIDENCE = HERE / "private-deliberation-cap-evidence"


def run():
    raw = experiment.replay(EVIDENCE)
    baseline = experiment.parent.read(experiment.BASE / "results.json")
    source = experiment.archived()
    review = experiment.parent.read(HERE / "private-deliberation-cap-review.json")
    assert review["transcript_sha256"] == experiment.runner.digest(EVIDENCE / "transcript.jsonl")
    labels = review["records"]
    assert labels.keys() == raw.keys()
    result = {}
    for family, _, _ in experiment.parent.fixtures():
        rubric = RUBRIC[family]
        base = baseline["cases"][family]["arms"]
        for key, annotation in labels.items():
            if not key.startswith(family + "/"):
                continue
            assert annotation["facts"].keys() <= rubric.keys()
            candidate = raw[key]["output"]
            assert all(spans and all(span in candidate for span in spans) for spans in annotation["facts"].values())
            assert all(span in candidate for span in annotation["conflicts"])

        identifier_a = f"{family}/desk_a"
        from_a = set(baseline["annotations"][identifier_a]["facts"])
        assert all(rubric[atom][0] == "A" for atom in from_a)
        arms = {}
        witnesses = {}
        for arm in experiment.ARMS:
            key = f"{family}/{arm}"
            annotation = labels[key]
            output = raw[key]
            if arm == "verbatim":
                eligible = set(rubric)
                calls = [output]
                notes = None
            else:
                report_key = f"{family}/report_{arm}"
                reporter = raw[report_key]
                original = source[f"{family}/desk_b_{arm}"]
                r = labels[report_key]
                assert reporter["messages"] == original["messages"]
                common = 0
                for old_token, new_token in zip(original["output_ids"], reporter["output_ids"]):
                    if old_token != new_token:
                        break
                    common += 1
                visible_peer = identifier_a in reporter["seen"]
                licensed = {atom for atom, (owner, _) in rubric.items() if owner == "B"}
                if visible_peer:
                    licensed |= from_a
                reporter_supported = licensed & r["facts"].keys()
                eligible = from_a | reporter_supported
                notes = {
                    "supported": sorted(reporter_supported),
                    "new_vs_first_note": sorted(reporter_supported - from_a),
                    "repeat_from_first_note": sorted(reporter_supported & from_a),
                    "unsupported_correct_facts": sorted(r["facts"].keys() - reporter_supported),
                    "conflicts": r["conflicts"],
                    "ended": reporter["ended"],
                    "tokens": len(reporter["output_ids"]),
                    "base_cap_ended": original["ended"],
                    "base_tokens": len(original["output_ids"]),
                    "common_output_prefix_tokens": common,
                }
                calls = [source[identifier_a], reporter, output]
            facts = set(annotation["facts"])
            supported = facts & eligible
            witnesses[arm] = supported
            words = len(output["output"].split())
            arms[arm] = {
                "supported_facts": sorted(supported), "count_of_8": len(supported),
                "correct_but_unwitnessed": sorted(facts - supported),
                "conflicts": annotation["conflicts"],
                "reporter": notes, "final_ended": output["ended"], "final_words": words,
                "strict_contract": len(supported) == len(rubric) and not annotation["conflicts"]
                                   and output["ended"] and words <= 73,
                "inference_calls": len(calls),
                "input_tokens": sum(len(call["input_ids"]) for call in calls),
                "output_tokens": sum(len(call["output_ids"]) for call in calls),
                "configured_output_cap": sum(call["cap"] for call in calls),
                "base_count_of_8": base[arm]["eligible_facts_out_of_8"] if arm in base else None,
            }
        result[family] = {
            "arms": arms,
            "interactive_only": sorted(witnesses["interactive"] - witnesses["independent"]),
            "independent_only": sorted(witnesses["independent"] - witnesses["interactive"]),
        }
    return {"scope": "Same-assistant exact-span review. The reporting prompt stays identical to baseline. "
                     "Only its generation cap is raised. The final prompt and cap stay fixed. Verbatim forwarding "
                     "uses two accepted source passages and no desk inference.",
            "dockets": result, "annotations": labels}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
