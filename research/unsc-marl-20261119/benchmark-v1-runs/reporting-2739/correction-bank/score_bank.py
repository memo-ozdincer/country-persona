"""Measure individual and joint effects on the unchanged final writer."""
from pathlib import Path

import correction as study

HERE, e, CASE = study.HERE, study.e, study.CASE


def run():
    verified = e.read(HERE / "verified.json")
    archived = e.read(study.OLD / "final-marks.json")
    marks = e.read(HERE / "final-marks.json")
    original = e.read(study.OLD / "results.json")["outcomes"]
    assert set(marks) == set(verified["packets"]) - set(archived)
    verdicts = archived | marks
    outcomes = {}
    for key, row in verified["outcomes"].items():
        order, edits = key.split("/")
        packet = verified["packets"][row["packet"]]
        reply = row["reply"]
        verdict = verdicts[packet["id"]]
        assert e.judge.request(e.final_packet(CASE, [{}, {}, reply])) == packet
        score = e.final_score(CASE, [{}, {}, reply], verdict)
        if edits == "00":
            assert row["reused"] and all(v == original[f"peer/{order}"][k] for k, v in score.items())
        issues = [u["id"] for u in verdict["units"] if u["status"] != "met"]
        outcomes[key] = score | {"packet": row["packet"], "reused": row["reused"],
                                 "guard_span": verdict["guard"]["response"],
                                 "guard_reason": verdict["guard"]["reason"], "unmet_or_uncertain": issues}
    contrasts = {}
    for order in (0, 1):
        rows = {key: outcomes[f"{order}/{key}"] for key in ("00", "10", "01", "11")}
        differences = {}
        for metric in ("raw_lower", "released"):
            y = {key: row["raw_70"][0] if metric == "raw_lower" else row["released_70"]
                 for key, row in rows.items()}
            differences[metric] = {
                "delete_opening_comparison": y["10"] - y["00"],
                "replace_reply": y["01"] - y["00"],
                "both": y["11"] - y["00"],
                "interaction": y["11"] - y["10"] - y["01"] + y["00"],
            }
        contrasts[str(order)] = differences
    inputs = (HERE / "plan.json", HERE / "verified.json", HERE / "final-marks.json",
              study.OLD / "final-marks.json", study.OLD / "results.json", Path(__file__))
    return {"outcomes": outcomes, "contrasts": contrasts,
            "sha256": {str(path.relative_to(HERE.parent)): study.study.pin(path) for path in inputs}}


if __name__ == "__main__":
    e.emit(run())
