"""Grade crossed writer inputs alongside both archived corners."""
import argparse

import crossover

E, HERE, KEY = crossover.E, crossover.HERE, crossover.KEY


def examples():
    rows = E.read(HERE / "crossover-evidence/crossed.json")
    for row, (arm, case, notes, req) in zip(rows, crossover.inputs(), strict=True):
        assert row["arm"] == arm and row["request"] == req
        yield arm, case, [*notes, row["response"]]


def deck():
    return sorted((E.final_packet(case, calls) for _, case, calls in examples()), key=lambda row: row["id"])


def report(verdicts):
    reference = E.read(HERE / "results.json")["conditions"][KEY]
    fields = ("exact_decision", "words", "guard", "raw_70", "released_70")
    rows = {"raw_opening_raw_reply": {k: reference["raw_peer"][k] for k in fields},
            "projected_opening_projected_reply": {k: reference["constraint_only_peer"][k] for k in fields}}
    joint = next(row for row in E.read(HERE / "evidence/episodes.json") if row["episode"] == KEY)
    joint_body = joint["final"]["response"]["text"].partition("\n")[2]
    body_matches = {}
    for arm, case, calls in examples():
        packet = E.final_packet(case, calls)
        marked = E.final_score(case, calls, verdicts[packet["id"]])
        rows[arm] = {k: marked[k if k != "exact_decision" else "mechanical"] for k in fields}
        body_matches[arm] = packet["answer"].partition("\n")[2] == joint_body
    return {"episode": KEY, "conditions": rows,
            "body_identical_to_combined_projection": body_matches,
            "exact_success_arms": [key for key, row in rows.items() if row["exact_decision"]["accepted"]]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score"))
    args = cli.parse_args()
    if args.mode == "deck":
        E.emit(deck())
    else:
        E.emit(report(E.read(HERE / "crossover-marks.json")))
