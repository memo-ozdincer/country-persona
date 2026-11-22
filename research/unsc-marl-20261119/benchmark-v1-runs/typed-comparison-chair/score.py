"""Render generic type claims and replay the learned communication policies."""
import json

from collect_typed import HERE, LABELS, plan, prior, PREVIOUS, WITNESS

earlier = prior.load("typed_policy_replay", PREVIOUS / "score.py")
read = prior.read
fixture = prior.fixture
CLAIMS = {
    "conditions": ("The delegate’s stated condition for its own support is distinct from the "
                   "adopted terms for appointment, which require consultation and do not require consent."),
    "mandates": ("The delegate’s account of a complementary role is consistent with the adopted "
                 "provision’s safeguard for the existing mandate."),
}


def compose(ids, prediction, expected):
    cards = prior.blocks(*ids)
    standalone = sum(x["weight"] for x in cards)
    claim = CLAIMS.get(prediction)
    record = "\n\n".join([*(b["text"] for b in cards), *([claim] if claim else [])])
    if claim:
        assert all(ids)
    assert 0 < len(record.split()) <= fixture.CASE["word_cap"]
    clear = not claim or prediction == expected
    bonus = 22 if claim and clear else 0
    return {"answer": record, "released_70": standalone + bonus if clear else 0,
            "released_relationship": bonus, "guard": "clear" if clear else "failed"}


def decision(choices):
    values = set(choices.values())
    return next(iter(values)) if len(values) == 1 and None not in values else "none"


def run():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    outputs = read(HERE / "verified.json")["outputs"]
    assert set(outputs) == set(spec["requests"])
    team = read(prior.TEAM / "results.json")
    banks = {mode: {key: compose(row["receipts"], "none", "none") for key, row in fixture.cases()[0].items()}
             for mode in (*LABELS, "agree")}
    grades = {}
    for key, row in spec["fixtures"].items():
        selected = {}
        for view, letters in LABELS.items():
            response = outputs[f"{key}/{view}"]
            assert response["receipts"] == row["receipts"]
            selected[view] = (letters.get(response["reply"]["text"])
                              if response["reply"]["termination"] == "complete" else None)
        predictions = selected | {"agree": decision(selected)}
        grades[key] = {"predictions": predictions, "expected": row["expected"],
                       "primary": "changed_from" not in row}
        if grades[key]["primary"]:
            for mode, value in predictions.items():
                banks[mode][key] = compose(row["receipts"], value, row["expected"])
    overview = {mode: {split: sum(r["predictions"][mode] == r["expected"]
                                   for r in grades.values() if r["primary"] == primary)
                       for split, primary in (("canonical", True), ("counterfactual", False))}
                for mode in banks}
    old = read(WITNESS / "results.json")
    return {"types": grades, "correct_of_four": overview, "composed": banks,
            "replays": {mode: earlier.evaluate(bank, team) for mode, bank in banks.items()},
            "prior_reference": {
                "direct": old["policies"]["direct"]["summary"],
                "witness": old["policies"]["witness"]["summary"],
                "archival": old["archival"],
            }}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
