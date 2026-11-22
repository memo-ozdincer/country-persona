"""Apply confirmation and proof-relevance to the same observed reply table."""
import torch

import route

HERE, E = route.HERE, route.E


def public_candidates(menu, names, prior, position):
    known = {option for message in prior if message["role"] == names[position] for option in message["excludes"]}
    for field, values in route.collection.FIELDS.items():
        for value in values:
            compatible = route.environment.allowed(menu, {field: value})
            if compatible and not compatible & known:
                yield compatible


def live_claims(row, notes, menu):
    admitted = row["claims"]
    messages = route.admit.messages(admitted, notes, menu)
    return [r for r in messages if r.get("excludes")]


def assess():
    path = HERE / "results.json"
    old = E.read(path)
    known = old["evaluation"]["records"]
    claims = E.read(HERE.parent / "syria-public-evidence/recovery.json")["episodes"]
    model = torch.tensor(old["training"]["weights"], dtype=torch.float64)
    episodes = {}
    for key, case, notes in route.collection.reader.pair_inputs():
        names = [speaker for speaker, _ in notes]
        before = live_claims(claims[key]["scan_clause"], notes, case["options"])
        initial = route.readout(names, before)["decision"]
        possible = []
        for i in (0, 1):
            candidates = public_candidates(case["options"], names, before, i)
            possible.append(initial == "U" and any(
                route.query(names, before, i, valid)["decision"] != "U" for valid in candidates))
        raw_choice = route.ACTIONS.index(known[key]["policies"]["learned"]["action"])
        feature = torch.tensor(route.features(names, before), dtype=torch.float64)
        probability = route.probabilities(feature, model)
        ranked = probability.masked_fill(~torch.tensor([True, *possible]), -torch.inf)
        # When no question can complete a proof, the silence action stays legal.
        choices = {"confirmation_only": raw_choice, "confirmation_and_proof_relevance": int(ranked.argmax()),
                   "first_proof_relevant": next((i + 1 for i, feasible in enumerate(possible) if feasible), 0)}
        out = {"public_query_can_complete_proof": possible, "policies": {}}
        for policy, choice in choices.items():
            if choice == 0:
                response = route.readout(names, before)
            else:
                actual = known[key]["clarifications"][choice-1]["compatible_packages"]
                response = route.query(names, before, choice-1, actual)
            label = response["decision"]
            targets = known[key]["target"]
            out["policies"][policy] = {"action": route.ACTIONS[choice], "decision": label,
                                      "utility": route.reward(label, targets) - route.QUESTION_COST * bool(choice),
                                      "correct": label in targets, "wrong": label not in {*targets, "U"}}
        episodes[key] = out
    names = next(iter(episodes.values()))["policies"].keys()
    score = {name: {"queries": sum(r["policies"][name]["action"] != "silence" for r in episodes.values()),
                    "correct": sum(r["policies"][name]["correct"] for r in episodes.values()),
                    "wrong_commitments": sum(r["policies"][name]["wrong"] for r in episodes.values()),
                    "net_utility": sum(r["policies"][name]["utility"] for r in episodes.values())}
             for name in names}
    return {"scores": score, "episodes": episodes,
            "baseline_sha256": route.collection.BASE.sha(path),
            "protocol_sha256": route.collection.BASE.sha(HERE / "confirmation-protocol.md")}


if __name__ == "__main__":
    E.emit(assess())
