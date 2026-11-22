"""Score the two packet-specific prompts and reweight the frozen route outcomes."""
import json

from receipt_outcomes import CITATION, EVIDENCE, final_review, writer

HERE = writer.HERE
PROBE = HERE / "receipt-scope-evidence"


def run():
    parent = json.loads((EVIDENCE / "results.json").read_text())
    rules = json.loads(writer.CASE.read_text())["rules"]
    raw = PROBE / "transcript.jsonl"
    reviews = json.loads((HERE / "receipt-scope-annotations.json").read_text())
    assert reviews["transcript_sha256"] == writer.runner.digest(raw)
    old_rows = {r["id"]: r for r in map(json.loads, (EVIDENCE / "transcript.jsonl").read_text().splitlines())}
    public = writer.compile_bank()[1][frozenset()]["text"]
    changed = {}
    for row in map(json.loads, raw.read_text().splitlines()):
        old = old_rows[row["id"]]
        a, b = (json.loads(r["messages"][1]["content"]) for r in (old, row))
        assert a.pop("task") != b.pop("task") and a == b
        assert old["messages"][0] == row["messages"][0] and old["cap"] == row["cap"]
        label = ",".join(sorted(row["evidence_ids"]))
        review = reviews["records"][row["id"]]
        prior = parent["bank"][label]
        met = {"procedure": [public], **review["met"]}
        assert met.keys() <= writer.compile_bank()[1][frozenset(row["evidence_ids"])]["proof"].keys()
        record = public + "\n\n" + row["output"]
        outcome = final_review(rules, {**row, "output": record}, {**review, "met": met})
        citations = {c for group in CITATION.findall(row["output"]) for c in group.split(", ")}
        release = (outcome["complete"] and outcome["source_guard_clear"] and outcome["word_count"] <= 185
                   and len(row["output"].split()) <= 155 and citations == set(row["evidence_ids"]))
        changed[label] = {"before_points": prior["points"], "after": {**outcome, "releasable": release},
                          "prior_release": prior["releasable"], "record": record}
    deltas = {}
    for scenario, route in parent["routes"].items():
        summary = {}
        for name in route["mean"]:
            coverage = points = releases = released_points = 0.
            for case in route["rows"]:
                for label, weight in case[name]["packet_probabilities"].items():
                    if label not in changed:
                        continue
                    c = changed[label]
                    before, after = c["before_points"], c["after"]
                    coverage += weight
                    points += weight * (after["points"] - before)
                    releases += weight * (after["releasable"] - c["prior_release"])
                    released_points += weight * (after["points"] * after["releasable"] - before * c["prior_release"])
            n = len(route["rows"])
            summary[name] = {"affected_probability": coverage / n, "change_in_record_points": points / n,
                             "change_in_release_probability": releases / n,
                             "change_in_released_points": released_points / n}
        deltas[scenario] = summary
    return {"scope": "Posthoc counterfactual substitution on two targeted failed packets. All other generated "
                     "packets and router choices are held fixed. This is not a fresh policy comparison.",
            "changed": changed, "reweighted_deltas": deltas}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
