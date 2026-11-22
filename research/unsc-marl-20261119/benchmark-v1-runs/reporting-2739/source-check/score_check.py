"""Score final records and verify cited evidence-flow annotations."""
from pathlib import Path

import source_check as study

HERE, CASE, e = study.HERE, study.CASE, study.e


def result():
    verified = e.read(HERE / "verified.json")
    marks = e.read(HERE / "final-marks.json")
    flows = e.read(HERE / "flow-marks.json")
    previous = e.read(HERE.parent / "results.json")["results"]
    assert set(marks) == set(verified["final_packets"])
    assert set(flows) == set(verified["traces"])
    outcomes = {}
    blocks = e.judge.by_id(e.evidence(CASE))
    for key, row in verified["traces"].items():
        calls = [row["opening"], row["second"]["reply"], row["final"]["reply"]]
        packet = e.judge.request(e.final_packet(CASE, calls))
        assert packet == verified["final_packets"][row["packet"]]
        score = e.final_score(CASE, calls, marks[row["packet"]])
        original = previous[f'{CASE["id"]}/{key}']
        flow = flows[key]
        assert set(flow) == {"opening_issue", "second_reason", "second_limit", "final_retention"}
        for label, (text, note, sources) in flow.items():
            turn = 0 if label == "opening_issue" else 2 if label == "final_retention" else 1
            assert note and all(source in blocks for source in sources)
            assert not text or text in calls[turn]["text"]
        outcomes[key] = score | {
            "packet": row["packet"], "flow": flow,
            "second_completion": calls[1]["termination"],
            "second_words": len(calls[1]["text"].split()),
            "input_tokens": sum(c["input_tokens"] for c in calls),
            "output_tokens": sum(c["output_tokens"] for c in calls),
            "raw_gain_over_original": score["raw_70"][0] - original["raw_70"][0],
            "released_gain_over_original": score["released_70"] - original["released_70"],
        }
    pairs = {
        str(order): {
            "peer_minus_independent_released": outcomes[f"peer/{order}"]["released_70"] -
            outcomes[f"independent/{order}"]["released_70"],
            "peer_minus_independent_raw": outcomes[f"peer/{order}"]["raw_70"][0] -
            outcomes[f"independent/{order}"]["raw_70"][0],
        }
        for order in (0, 1)
    }
    inputs = (Path(__file__), HERE / "verified.json", HERE / "final-marks.json", HERE / "flow-marks.json")
    return {"paired_deltas": pairs, "outcomes": outcomes,
            "sha256": {path.name: study.study.pin(path) for path in inputs}}


if __name__ == "__main__":
    e.emit(result())
