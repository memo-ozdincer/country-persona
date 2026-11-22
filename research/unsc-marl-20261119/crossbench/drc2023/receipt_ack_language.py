"""Read status and content of documentary receipts and test the resulting action."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
import sys
from pathlib import Path
from unittest.mock import patch

import receipt_ack as experiment

HERE = experiment.HERE
sys.path.insert(0, str(HERE.parents[1]))
import relay_text as runner
POLICY = HERE / "receipt-ack.json"
SOURCE = HERE.parent / "unami2023/case.json"
FIELDS = ("REVIEW", "REPORT", "TERM", "CONSULT")
FORMS = (("absent", None), *product(("received", "planned"), range(4)))
FOCUS = (0, 1)
DECODE_ORDERS = ((0, 1, 2, 3, 4), (4, 3, 2, 1, 0))


def load(path):
    return json.loads(path.read_text())


def clauses():
    case = load(SOURCE)
    cards = {key: value for role in case["roles"].values() for key, value in role.items()}
    replayed = load(experiment.UNAMI)
    result = {key: cards[key] for key in FIELDS}
    result["REVIEW"] = replayed["archived_peer_sentence"]
    result["REPORT"] = replayed["report_documentary_witness"]
    assert result["REPORT"] in cards["REPORT"] and replayed["review_documentary_witness"] in cards["REVIEW"]
    return result


def wire(kind, name, cards):
    if kind == "absent":
        return "No message has arrived."
    intro = ("The chair confirmed it received and recorded this passage: " if kind == "received"
             else "The first desk intends to forward this passage. The chair has not confirmed receipt: ")
    return intro + cards[FIELDS[name]]


def row(key, system, body, order):
    return {"observation": key, "legal": order, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
    ]}


def prompts():
    cards = clauses()
    for form, clause in FORMS:
        packet = wire(form, clause, cards)
        for run, order in enumerate(DECODE_ORDERS):
            codes = {k: ("no confirmed receipt" if i == 4 else FIELDS[i]) for k, i in zip("ABCDE", order, strict=True)}
            system = ("Identify the source field the chair has received, or select no confirmed receipt. "
                      "Plans are not receipts. The excerpt determines the field. Return only the selection letter.")
            yield row(("decode", form, clause, run), system,
                      {"documentary_receipt_message": packet, "answer_options": codes}, order)
        for holding in experiment.base.PAIRS:
            for run, order in enumerate((holding, holding[::-1])):
                system = ("You are the second archival desk and can forward one of your local clauses. "
                          "Help the chair receive both requested clauses. Skip a duplicate only if that clause "
                          "has already been confirmed received. If both requested clauses are equally eligible "
                          "because neither has been confirmed, prefer REVIEW. Return only the selection letter.")
                options = {k: FIELDS[i] for k, i in zip("AB", order, strict=True)}
                held = {FIELDS[i]: cards[FIELDS[i]] for i in holding}
                yield row(("choose", form, clause, *holding, run), system,
                          {"requested": [FIELDS[i] for i in FOCUS], "local_cards": held,
                           "documentary_receipt_message": packet, "answer_options": options}, order)


def pins():
    files = (Path(__file__), Path(runner.__file__), Path(experiment.__file__), POLICY, SOURCE, experiment.UNAMI)
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def pick(raw, prefix, rounds=2):
    values = []
    for run in range(rounds):
        row = raw[(*prefix, run)]
        best = [choice for choice, value in zip(row["legal"], row["scores"], strict=True) if value == max(row["scores"])]
        values.append(best[0] if len(best) == 1 else None)
    return values


def replay(choice, decode, planned):
    parent = experiment.stored(POLICY)
    outcomes = {}
    score_table = load(experiment.UNAMI)["records"]["no_question"]["receipts"]
    for context in ("overlap", "split"):
        prior = experiment.base.roster(context)
        measures = {}
        for name in ("host_typed_learned", "decoded_learned", "direct_language", "direct_no_ack", "decoded_no_ack"):
            sums = Counter()
            for (left, right), p in prior.items():
                for first, a in experiment.base.choose_probability(parent, "sender", FOCUS, left):
                    for received, observed, prob in experiment.events(first, "ack", experiment.base.CHAIR):
                        # A disclosed plan is a stress test in failed-delivery worlds.
                        form = ("received", observed) if observed is not None else (
                            ("planned", first) if not received and planned else ("absent", None))
                        if name.endswith("no_ack") and form[0] == "received":
                            form = ("absent", None)
                        if name == "host_typed_learned":
                            value = observed
                        elif name.startswith("decoded"):
                            candidate = decode[form]
                            value = candidate[0] if candidate[0] == candidate[1] and candidate[0] in range(4) else None
                        if name.startswith("direct"):
                            selected = choice[(*form, *right)]
                            # Uniformly randomize option order and split a numerical tie evenly.
                            b = {slot: sum(.5 if result == slot else .25 if result is None else 0.
                                           for result in selected) for slot in right}
                        else:
                            b = dict(experiment.base.choose_probability(parent, "recipient", FOCUS, right, value))
                        for second, weight in b.items():
                            for delivered, link in ((False, 1 - experiment.base.CHAIR), (True, experiment.base.CHAIR)):
                                mass = p * a * prob * weight * link
                                cards = ({first} if received else set()) | ({second} if delivered else set())
                                got_review, got_report = (slot in cards for slot in FOCUS)
                                key = f"{'ask' if got_review else 'pass'}/{'fetch' if got_report else 'no_fetch'}"
                                result = score_table[key]
                                sums["mass"] += mass
                                sums["complete"] += mass * result["both_obligations_source_complete"]
                                sums["calendar"] += mass * (result["calendar_entries"] == 3)
                                sums["record_points"] += mass * result["points"]
            assert abs(sums.pop("mass") - 1.) < 1e-9
            measures[name] = dict(sums)
        outcomes[context] = measures
    return outcomes


def scores(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        raw = runner.read(directory)
    decoder = {key: pick(raw, ("decode", *key)) for key in FORMS}
    choice = {(*key, *holding): pick(raw, ("choose", *key, *holding))
              for key, holding in product(FORMS, experiment.base.PAIRS)}
    received = {key: val for key, val in decoder.items() if key[0] == "received"}
    negative = {key: val for key, val in decoder.items() if key[0] != "received"}
    counts = {
        "stable_correct_received": sum(v == [key[1]] * 2 for key, v in received.items()),
        "stable_correct_no_receipt": sum(v == [4, 4] for v in negative.values()),
        "stable_false_receipt": sum(v[0] == v[1] and v[0] in range(4) for v in negative.values()),
        "choice_disagreement_or_tie": sum(a != b or a is None for a, b in choice.values()),
        "choice_conditions": len(choice),
    }
    return {"scope": "Frozen Qwen next-label inference for receipt decoding and direct follow-up. "
                     "Envelope statements are authored controls around archived UNAMI prose. "
                     "The two-part authenticated content is an evaluation reference. "
                     "Exact replay applies measured choices to simulated private inventories and unreliable delivery.",
            "counts": counts, "decode": [{"condition": key, "choices": val} for key, val in decoder.items()],
            "actions": [{"condition": key, "choices": val} for key, val in choice.items()],
            "replay": {"ordinary": replay(choice, decoder, False),
                       "failed_delivery_plan_stress": replay(choice, decoder, True)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(scores(args.directory), indent=2))
