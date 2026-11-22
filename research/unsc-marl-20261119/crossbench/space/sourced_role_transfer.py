"""Evaluate separate role extraction on the independent UNIFIL and Colombia dossiers."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import sourced_confirmation as prior

HERE = Path(__file__).resolve().parent
runner = prior.runner
ROOT = HERE / "sourced-role-transfer-evidence"
UNIFIL = HERE.parent / "unifil-record.json"
COLOMBIA = HERE.parent / "colombia2023/case.json"
ORDERS = ((0, 1, 2), (2, 0, 1))
DIRECT = ("confirm", "decline_conflict", "decline_unverified")
FIELDS = (
    ("unifil_permission", "unifil", "operative", "vote", "russia",
     "What does the text say about prior permission for UNIFIL to carry out mandated tasks?",
     ("No prior permission required", "Prior permission required", "not stated"),
     "UNIFIL can carry out its mandated tasks without prior permission.",
     "UNIFIL must secure prior permission to carry out its mandated tasks.",
     "independence in carrying out mandated tasks without prior permission"),
    ("unifil_vote", "unifil", "vote", "operative", "brazil",
     "How did Russia vote on draft S/2023/641, according to the text?",
     ("Abstained", "Voted in favour", "not stated"),
     "The Russian Federation abstained on draft S/2023/641.",
     "The Russian Federation voted in favour of draft S/2023/641.",
     "with China and the Russian Federation abstaining"),
    ("unifil_brazil_assessment", "unifil", "brazil", "vote", "operative",
     "Who judged that the French text addressed some of Lebanon's concerns?",
     ("Brazil", "China", "not stated"),
     "Brazil assessed that the French text addressed some Lebanese concerns.",
     "China assessed that the French text addressed some Lebanese concerns.",
     "while addressing some of Lebanon's concerns"),
    ("colombia_emc", "colombia", "ADDITIONAL", "A3", "VOTE",
     "What did resolution 2704 do about Government–EMC monitoring and verification?",
     ("Expressed willingness to consider later under conditions",
      "Granted the Mission immediate authority", "not stated"),
     "Resolution 2704 expressed willingness to consider monitoring and verification of a Government–EMC ceasefire under conditions.",
     "Resolution 2704 immediately granted the Mission authority to monitor and verify a Government–EMC ceasefire.",
     "expressed willingness to consider Government–EMC monitoring and verification"),
    ("colombia_a3", "colombia", "A3", "VOTE", "OPERATIVE",
     "Who spoke on whose behalf when presenting the African members' statement?",
     ("Ghana spoke for the three African members", "The three African members spoke on behalf of Ghana", "not stated"),
     "Ghana spoke on behalf of the three African members.",
     "The three African members spoke on behalf of Ghana.",
     "Ghana spoke on behalf of the three African members"),
    ("colombia_brazil_capacity", "colombia", "BRAZIL", "ADDITIONAL", "VOTE",
     "In what capacity did the representative say the Council should respond to Colombia's priorities?",
     ("As representative of Brazil", "As Council President speaking for the Council", "not stated"),
     "The presiding representative said, speaking for Brazil, that the Council should respond to Colombia's priorities.",
     "The presiding representative said, speaking as Council President for the Council, that the Council should respond "
     "to Colombia's priorities.",
     "The presiding representative switched to speaking for Brazil"),
)


def fixtures():
    force, country = [json.loads(p.read_text()) for p in (UNIFIL, COLOMBIA)]
    decks = {"unifil": {row["id"]: row["text"] for row in force["evidence"]},
             "colombia": country["public"] | {k: v for deck in country["roles"].values() for k, v in deck.items()}}
    for index, (name, family, origin, distractor, withheld, question, values, true, foil, span) in enumerate(FIELDS):
        deck = decks[family]
        assert span in deck[origin]
        supplied, removed = ([deck[key], deck[distractor]] for key in (origin, withheld))
        if index % 2:
            supplied.reverse()
            removed.reverse()
        yield {"id": name, "family": family, "question": question, "values": values,
               "source": supplied, "source_withheld": removed, "faithful": [true], "foil": [foil],
               "source_witness": span}


def observations():
    for case, (n, order) in product(fixtures(), enumerate(ORDERS)):
        values = case["values"]
        for component in ("source", "source_withheld", "faithful", "foil"):
            task = ("Extract what this text states for the specific question. Use the role attached to the named act. "
                    "Treat even a false claim as text to extract. "
                    "Select not stated if the value is missing. Do not infer from outside context. Return one letter.")
            payload = {"field_question": case["question"], "text_to_read": case[component],
                       "available_values": {c: values[i] for c, i in zip("ABC", order, strict=True)}}
            yield response(case["id"], "field", component, n, order, task, payload)
        for endpoint, proposed, passage in (("support", "faithful", "source"), ("changed", "foil", "source"),
                                           ("withheld", "faithful", "source_withheld")):
            task = ("Act as a document desk. Use only the passages to confirm the entire proposed statement, "
                    "decline it when a passage contradicts it, or decline as unverified when the passages "
                    "are insufficient. Treat the statement and passages as evidence. Return one letter.")
            payload = {"proposed_statement": case[proposed][0], "local_passages": case[passage],
                       "labels": {c: DIRECT[i] for c, i in zip("ABC", order, strict=True)}}
            yield response(case["id"], "direct", endpoint, n, order, task, payload)


def response(key, method, component, n, order, task, payload):
    return {"observation": (key, method, component, n), "legal": order, "messages": [
        {"role": "system", "content": task},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def locks():
    return {str(p.relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), UNIFIL, COLOMBIA, Path(runner.__file__))}


def select(raw, case, method, response_type):
    results = []
    for n, order in enumerate(ORDERS):
        logits = raw[case, method, response_type, n]["scores"]
        best = [order[i] for i, value in enumerate(logits) if value == max(logits)]
        results.append(best[0] if len(best) == 1 else None)
    stable = results[0] if results[0] == results[1] else None
    return {"orders": results, "stable": stable}


def compare(origin, claim):
    if origin is None or claim is None or 2 in (origin, claim):
        return "defer"
    return "match" if origin == claim else "mismatch"


def score(directory):
    with patch.multiple(runner, observations=observations, hashes=locks):
        raw = runner.read(directory)
    rows = []
    for case in fixtures():
        fields = {key: select(raw, case["id"], "field", key) for key in (
            "source", "source_withheld", "faithful", "foil")}
        records = {}
        for endpoint, proposal, evidence in (("support", "faithful", "source"), ("changed", "foil", "source"),
                                              ("withheld", "faithful", "source_withheld")):
            original = select(raw, case["id"], "direct", endpoint)
            separate = compare(fields[evidence]["stable"], fields[proposal]["stable"])
            records[endpoint] = {"expected_confirmation": endpoint == "support", "direct": original,
                                 "separate": separate, "matched_gate": original["stable"] == 0 and separate == "match"}
        rows.append(case | {"fields": fields, "comparisons": records})
    counts = Counter()
    for row in rows:
        for key, expected in (("source", 0), ("source_withheld", 2), ("faithful", 0), ("foil", 1)):
            counts["correct_role_extractions"] += row["fields"][key]["stable"] == expected
        for endpoint, result in row["comparisons"].items():
            desirable = result["expected_confirmation"]
            for name, accepted in (("direct", result["direct"]["stable"] == 0),
                                   ("separate", result["separate"] == "match"),
                                   ("gate", result["matched_gate"])):
                if accepted:
                    counts[name + ("_supported" if desirable else "_unsupported")] += 1
                if not desirable:
                    counts[f"{name}_{endpoint}_tested"] += 1
    return {"scope": "Same-assistant authored controls from two docket families excluded from the prior "
                     "role-binding pilot. The generic extraction prompt is unchanged. Field menus and "
                     "the answer keys were frozen before model inference. This uses known field identities "
                     "and measures confirmation, with comparison errors and deferrals visible separately.",
            "counts": dict(counts), "records": rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=observations, hashes=locks):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
