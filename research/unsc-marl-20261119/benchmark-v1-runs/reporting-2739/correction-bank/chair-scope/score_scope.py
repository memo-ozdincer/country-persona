"""Apply the frozen adjudicator and calculate the exact upstream reward contrast."""
from fractions import Fraction
from pathlib import Path

import chair_scope as study

HERE, BANK, CASE, e = study.HERE, study.BANK, study.CASE, study.e
ACTIONS = ("00", "01", "10", "11")


def effects(matrix):
    original, reply, remove, both = (matrix[action] for action in ACTIONS)
    return {"remove_opening_comparison": remove - original,
            "replace_reply": reply - original,
            "both": both - original,
            "interaction": both - reply - remove + original,
            "span": max(matrix.values()) - min(matrix.values()),
            "optimal_actions": [action for action in ACTIONS if matrix[action] == max(matrix.values())],
            "gradient_at_uniform_logits": [
                str(Fraction(remove + both - reply - original, 8)),
                str(Fraction(reply + both - remove - original, 8)),
            ]}


def run():
    verified = e.read(HERE / "verified.json")
    marks = e.read(HERE / "final-marks.json")
    original_marks = e.read(BANK.parent / "source-check/final-marks.json") | e.read(BANK / "final-marks.json")
    assert set(marks) == set(verified["packets"]) - set(original_marks)
    all_marks = original_marks | marks
    original = e.read(BANK / "results.json")["outcomes"]
    results = {}
    for key, item in verified["outcomes"].items():
        reply = item["reply"]
        packet = e.judge.request(e.final_packet(CASE, [{}, {}, reply]))
        assert packet == verified["packets"][item["packet"]]
        score = e.final_score(CASE, [{}, {}, reply], all_marks[packet["id"]])
        results[key] = score | {
            "original_raw_70": original[key]["raw_70"],
            "original_released_70": original[key]["released_70"],
            "released_gain": score["released_70"] - original[key]["released_70"],
            "packet": item["packet"], "input_tokens": reply["input_tokens"],
            "output_tokens": reply["output_tokens"],
        }
    report = {}
    for order in (0, 1):
        rows = {action: results[f"{order}/{action}"] for action in ACTIONS}
        report[str(order)] = {metric: effects({action: value(row) for action, row in rows.items()})
                              for metric, value in (("released", lambda row: row["released_70"]),
                                                    ("raw_lower", lambda row: row["raw_70"][0]))}
    paths = (Path(__file__), HERE / "plan.json", HERE / "verified.json", HERE / "final-marks.json",
             BANK / "results.json", BANK / "final-marks.json", BANK.parent / "source-check/final-marks.json")
    return {"outcomes": results, "within_scoped_chair": report,
            "sources_sha256": {str(path.relative_to(BANK.parent)): study.pin(path) for path in paths}}


if __name__ == "__main__":
    e.emit(run())
