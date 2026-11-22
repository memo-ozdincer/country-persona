"""Test source-bound receipt display on actual two-deadline handover decisions."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import grade_handovers
import handover

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import relay_text as runner
sys.path.insert(0, str(handover.CROSS / "drc2023"))
import receipt_ack as route

POLICY = route.HERE / "receipt-ack.json"
ARMS = ("pooled_text", "field_receipt")
VIEWS = ((0, 1, 2), (1, 2, 0), (2, 0, 1))


def load(path):
    return json.loads(path.read_text())


def fixtures():
    source = handover.render()
    assert source["inputs"] == load(HERE / "handover-inputs.json")
    assert source["keys"] == load(HERE / "handover-key.json")
    return source


def questions():
    for case in fixtures()["inputs"]:
        docket = handover.CASES[case["family"]]
        for position, (field, _, expected_source) in enumerate(docket):
            proposed = case["draft"][field]
            alternative, = [date for _, date, _ in docket if date != proposed]
            wording = ("As the next Council scheduling clerk, decide this one field. "
                       "Confirm the proposed date only if the supplied source establishes that date for this exact field. "
                       "Correct it if the source establishes the alternative. Select verification if the relevant source is missing "
                       "or neither date is established. A date for a different legal act is insufficient. Return only the option letter.")
            options = (f"Confirm {proposed}", f"Correct to {alternative}", "Refer for verification, without supplying a date")
            order = VIEWS[(case["id"] + position) % len(VIEWS)]
            menu = {letter: options[slot] for letter, slot in zip("ABC", order, strict=True)}
            cards = [{"source_id": i, "excerpt": card} for i, card in case["holdings"].items() if card is not None]
            for arm in ARMS:
                payload = {"calendar_field": field, "draft": proposed,
                           "received_documentary_cards": cards, "options": menu}
                if arm == "field_receipt":
                    payload["field_receipt"] = {"source_for_this_field": expected_source,
                                                "received": case["holdings"][expected_source] is not None}
                yield {"observation": (case["id"], position, arm), "legal": order, "messages": [
                    {"role": "system", "content": wording},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ]}


def hashes():
    files = (Path(__file__), Path(runner.__file__), Path(handover.__file__), Path(grade_handovers.__file__),
             Path(route.__file__), Path(route.base.__file__), POLICY, HERE / "handover-inputs.json",
             HERE / "handover-key.json", *(handover.CROSS / family / "case.json" for family in handover.CASES))
    from hashlib import sha256
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def choose(row):
    best = [j for j, value in zip(row["legal"], row["scores"], strict=True) if value == max(row["scores"])]
    return best[0] if len(best) == 1 else None


def predict(raw, arm, gate=False):
    rows = []
    for case in fixtures()["inputs"]:
        docket = handover.CASES[case["family"]]
        answer = {"id": case["id"], "actions": {}, "deliverable": {}}
        for position, (field, _, expected_source) in enumerate(docket):
            action = choose(raw[case["id"], position, arm])
            if gate and case["holdings"][expected_source] is None:
                action = 2
            proposed = case["draft"][field]
            alternate, = [date for _, date, _ in docket if date != proposed]
            answer["actions"][field] = ("confirm", "correct", "verify", "unresolved")[action if action is not None else 3]
            answer["deliverable"][field] = (proposed, alternate, None, None)[action if action is not None else 3]
        rows.append(answer)
    return rows


def exact_receipt_probabilities(prior_name, peer):
    focus = (0, 1)
    roster = route.base.roster(prior_name)
    policy = route.stored(POLICY)
    probabilities = [0.] * 4
    link = route.base.CHAIR
    for (left, right), p in roster.items():
        for first, a in route.base.choose_probability(policy, "sender", focus, left):
            for arrived, obs, m in route.events(first, "ack", link):
                seen = obs if peer else None
                for second, b in route.base.choose_probability(policy, "recipient", focus, right, seen):
                    for second_arrived, r in ((False, 1-link), (True, link)):
                        delivered = ({first} if arrived else set()) | ({second} if second_arrived else set())
                        mask = 2 * int(0 in delivered) + int(1 in delivered)
                        probabilities[mask] += p*a*m*b*r
    assert abs(sum(probabilities) - 1) < 1e-9
    return probabilities


def downstream(predictions):
    gold = fixtures()["keys"]
    output = {}
    for name in ("overlap", "split"):
        output[name] = {}
        for mode in (True, False):
            weights = exact_receipt_probabilities(name, mode)
            fields = full = unsupported = 0.
            for row, answer in zip(predictions, gold, strict=True):
                assert row["id"] == answer["id"]
                w = weights[row["id"] % 4] / 8
                good = [row["actions"][key] == expected and row["deliverable"][key] == answer["deliverable"][key]
                        for key, expected in answer["actions"].items()]
                fields += sum(good) * w
                full += (all(good) and row["id"] % 4 == 3) * w
                unsupported += sum(row["actions"][key] in ("confirm", "correct") and expected == "verify"
                                   for key, expected in answer["actions"].items()) * w
            output[name]["visible" if mode else "erased"] = {
                "receipt_masks": weights, "fields_right_of_two": fields, "complete_usable": full,
                "expected_unsupported_certifications": unsupported}
    return output


def score(directory):
    with patch.multiple(runner, observations=questions, hashes=hashes):
        raw = runner.read(directory)
    policies = {arm: predict(raw, arm) for arm in ARMS}
    policies["field_receipt_with_gate"] = predict(raw, "field_receipt", gate=True)
    policies["oracle"] = [{"id": row["id"], "actions": row["actions"], "deliverable": row["deliverable"]}
                          for row in fixtures()["keys"]]
    return {"scope": "Frozen next-label inference. The two arms see the same documentary excerpts and possible dates. "
                     "The additional structured receipt identifies the card for the field and whether it arrived. "
                     "The gate enforces referral on a verified absence. Archived selection probabilities are replayed under simulated holdings.",
            "arms": {name: {"accuracy": grade_handovers.grade(rows), "exact_routing_replay": downstream(rows),
                            "predictions": rows} for name, rows in policies.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=questions, hashes=hashes):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
