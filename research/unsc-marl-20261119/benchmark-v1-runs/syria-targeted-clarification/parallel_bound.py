"""Measure the additive value of both independently collected clarification replies."""

import route

HERE, E = route.HERE, route.E


def run():
    artifact = HERE / "results.json"
    episodes = E.read(artifact)["evaluation"]["records"]
    outcomes = {}
    for key, row in episodes.items():
        answers = row["clarifications"]
        roles = [item["speaker"] for item in answers]
        if any(answer["compatible_packages"] is None for answer in answers):
            raise ValueError("Parallel comparison requires two valid independently collected answers")
        ledger = route.readout(roles, [route.full(a["speaker"], a["compatible_packages"]) for a in answers])
        one = any(r["decision"] in row["target"] for r in row["branch_outcomes"].values())
        both = ledger["decision"] in row["target"]
        outcomes[key] = {"both": ledger, "correct": both,
                         "oracle_at_most_one_correct": one,
                         "two_help": both and not one}
    return {"episodes": outcomes, "correct_two_parallel": sum(r["correct"] for r in outcomes.values()),
            "gains_over_at_most_one": sum(r["two_help"] for r in outcomes.values()),
            "source_sha256": route.collection.BASE.sha(artifact)}


if __name__ == "__main__":
    E.emit(run())
