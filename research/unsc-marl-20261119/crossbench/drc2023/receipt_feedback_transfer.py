"""Apply the frozen negative-receipt policy to three existing UN dockets."""
from functools import partial
import json
from pathlib import Path
from unittest.mock import patch

import receipt_feedback as feedback
from policy_replay import policy

HERE = Path(__file__).resolve().parent
relay = policy.relay
shift = policy.shift
CONDITIONS = ("original", "strong_specialist_B", "mislabelled_specialist_B")


def metrics(distributions, pending, target, ident, bank, anchor):
    local = bank[frozenset({ident[anchor]})]["record_points"]
    results = {}
    for name, distribution in distributions.items():
        assert abs(sum(row[0] for row in distribution.values()) - 1.) < 1e-9
        score = sum(row[0] * bank[frozenset(ident[i] for i in target if i not in left)]["record_points"]
                    for left, row in distribution.items())
        fees = sum(row[1] for row in distribution.values())
        results[name] = {"record_points": score, "contact_fees": fees, "net": score - local - fees,
                         "contact_attempts": sum(row[2] for row in distribution.values()),
                         "complete": distribution.get(frozenset(), (0.,))[0],
                         "mean_received": sum((len(pending) - len(left)) * row[0]
                                              for left, row in distribution.items())}
    return results


def run():
    source = HERE / "evidence/receipt-feedback.json"
    former = HERE.parent / "colombia2023/specialist-fit-results.json"
    new, old = ({shift.transfer.immutable(row["local_state"]): row["probabilities"]
                 for row in json.loads(path.read_text())["policy"]} for path in (source, former))
    families = {}
    for name, ids, bank, mapped in shift.datasets():
        table = {(row["anchor"], *row["other_cards"]): row for row in mapped["rows"]}
        conditions = {}
        for condition in CONDITIONS:
            strength, desk, kind = shift.CONDITIONS[condition]
            hint = 1 - desk if kind == "wrong_hint" else desk
            rows = []
            for target, anchor in relay.SCENARIOS:
                pending = tuple(i for i in target if i != anchor)
                prior = shift.distribution(pending, strength, desk, kind)
                context = table[ids[anchor], *(ids[i] for i in pending)]
                ordering = (hint, 1 - hint)
                distributions = {"learned_no_ack": shift.remap(old, prior, target, anchor, context, ordering),
                                 "adaptive_no_ack": policy.script(target, anchor, ids, bank, prior, True)}
                for label, blind in (("learned_ack", False), ("learned_ack_erased", True)):
                    with patch.object(shift.transfer, "outcomes", partial(feedback.replay, blind=blind)):
                        distributions[label] = shift.remap(new, prior, target, anchor, context, ordering)
                with patch.object(relay, "transitions", feedback.script_transitions):
                    distributions["adaptive_ack"] = policy.script(target, anchor, ids, bank, prior, True)
                    distributions["fixed_ack"] = policy.script(target, anchor, ids, bank, prior, False)
                values = metrics(distributions, pending, target, ids, bank, anchor)
                assert values["adaptive_ack"]["net"] + 1e-9 >= values["fixed_ack"]["net"]
                assert values["adaptive_ack"]["net"] + 1e-9 >= values["learned_ack"]["net"]
                rows.append({"anchor": ids[anchor], "target": [ids[i] for i in target], "values": values})
            conditions[condition] = {"mean": shift.transfer.mean([row["values"] for row in rows]), "rows": rows}
        families[name] = conditions
    assert set(families) == {"unami", "unifil", "colombia"}
    return {"scope": "Frozen written-vote-only policies. Three excluded dockets, existing authored banks "
                     "and payoff mapping, simulated holdings, matched scripts with the true prior. "
                     "These endpoints use authored records.",
            "families": families,
            "pins": {path.name: feedback.results.writer.runner.digest(path) for path in (
                source, former, Path(__file__), HERE.parent / "ftf2020/adaptive-align-results.json",
                HERE.parent / "colombia2023/verified-transfer.json")}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
