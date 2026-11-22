"""Compose supported claims and replay the pre-trained desks."""
import json

from collect_roles import CLAIMS, HERE, SLOTS, TYPED, plan, prior, read, typed

writer = typed.prior.load("role_scoped_renderer", TYPED / "score.py")
MODES = ("ab", "ba", "mean", "agreement")


def phrase_match(row):
    early, late = (row["packet"][slot].casefold() for slot in SLOTS)
    if "withhold support" in early and "no consent requirement" in late:
        return "conditions"
    if "complement to unama" in early and "preserving the mandate and work of unama" in late:
        return "mandates"
    return "none"


def run():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    outputs = read(HERE / "verified.json")["outputs"]
    assert len(outputs) == len(spec["requests"])
    gates = {}
    for card in spec["cards"]:
        gates[card] = {}
        for relation in CLAIMS:
            margins = {}
            for key, labels in prior.MAPPINGS.items():
                logits = outputs[f"{card}/{relation}/{key}"]["logits"]
                positive = next(x for x, y in labels.items() if y == "process")
                negative = next(x for x, y in labels.items() if y == "fund")
                margins[key] = logits[positive] - logits[negative]
            values = list(margins.values())
            gates[card][relation] = {
                "margins": margins | {"mean": sum(values)/2},
                "passes": {k: v > 0 for k, v in margins.items()} |
                          {"mean": sum(values) > 0, "agreement": all(v > 0 for v in values)},
            }
    bank = {mode: {k: writer.compose(row["receipts"], "none", "none")
                   for k, row in writer.fixture.cases()[0].items()} for mode in MODES}
    records = {}
    for key, pair in spec["pairs"].items():
        cards = spec["references"][key]
        choices = {"phrase": phrase_match(pair)}
        for mode in MODES:
            supported = [rel for rel in CLAIMS if all(
                gates[card][rel]["passes"][mode] for card in cards.values())]
            choices[mode] = supported[0] if len(supported) == 1 else "none"
            if pair["group"] == "canonical":
                bank[mode][key] = writer.compose(pair["receipts"], choices[mode], pair["expected"])
        records[key] = {"expected": pair["expected"], "group": pair["group"], "choices": choices}
    groups = ("canonical", "previous_control", "paraphrase", "quoted_reversal")
    correct = {mode: {group: sum(r["choices"][mode] == r["expected"]
                                for r in records.values() if r["group"] == group)
                      for group in groups} for mode in (*MODES, "phrase")}
    team = read(typed.prior.TEAM / "results.json")
    old = read(TYPED / "results.json")
    return {"cards": gates, "relations": records, "correct_out_of_four": correct,
            "composed": bank, "replays": {k: writer.earlier.evaluate(v, team) for k, v in bank.items()},
            "previous_approvals": old["correct_of_four"]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
