"""Evaluate a typed clarification handoff without silently narrowing scope."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re

import scoped_relay as relay
import witness_context as context

HERE = context.HERE
AFTER = re.compile(r"^\s+(?:is|was)\s+(?:not what (?:I|we) need|already in (?:my|our) (?:file|records))\b", re.I)


def compiled(text, output, ended):
    decision, why = context.compile_guarded(text, output, ended)
    if not decision or decision[0] == "unspecified":
        return decision, why
    for span in output.splitlines():
        after = text[text.index(span) + len(span):]
        if AFTER.match(after):
            return None, "post_object_exclusion_or_possession"
    return decision, why


def confirm(answer):
    if not isinstance(answer, dict) or answer.keys() != {"mode", "records"}:
        return None
    mode, records = answer["mode"], answer["records"]
    if mode not in ("one", "all", "any") or type(records) is not list:
        return None
    if not all(isinstance(key, str) and key in relay.archive.KEYS for key in records):
        return None
    if not records or len(set(records)) != len(records):
        return None
    if (mode == "one") != (len(records) == 1):
        return None
    return mode, tuple(sorted(records))


def comparisons():
    examples = {
        "empty": ({}, False),
        "unrecognized_id": ({"mode": "one", "records": ["some-other-draft"]}, False),
        "duplicate": ({"mode": "all", "records": ["us", "us"]}, False),
        "two_in_single": ({"mode": "one", "records": ["us", "russia"]}, False),
        "one_in_alternatives": ({"mode": "any", "records": ["us"]}, False),
        "unknown_mode": ({"mode": "sometimes", "records": ["us"]}, False),
        "bad_records_type": ({"mode": "one", "records": "us"}, False),
        "single": ({"mode": "one", "records": ["us"]}, True),
        "alternatives": ({"mode": "any", "records": ["us", "russia"]}, True),
        "conjunction": ({"mode": "all", "records": ["council_president", "indonesia_national"]}, True),
        "larger_conjunction": ({"mode": "all", "records": ["us", "russia", "council_president"]}, True),
    }
    results = {}
    for key, (reply, valid) in examples.items():
        selected = confirm(reply)
        assert bool(selected) == valid
        results[key] = selected
    outputs = [relay.named(results["larger_conjunction"], anchor, roster, True, True)
               for anchor, roster in product(range(4), relay.archive.PAIRS)]
    assert all(response["status"] != "complete" for response in outputs)
    return results


def run():
    path = HERE / "witness-evidence/results.json"
    old = relay.archive.read(path)["records"]
    c = relay.binary.decoder.transfer.Calibration()
    outcomes, diagnostics = {}, {}
    for key, row in old.items():
        reference = row["reference"][0], tuple(row["reference"][1])
        admitted, why = compiled(row["assignment"], row["generated_spans"], row["reason"] != "invalid_generation")
        clarified = not admitted or admitted[0] == "unspecified"
        if clarified and reference[0] != "unspecified":
            # This is an authored reply, not another model generation or an
            # observed user interaction. It defines an explicit upper test.
            final = confirm({"mode": reference[0], "records": list(reference[1])})
        else:
            final = admitted
        results = {}
        for method, selection in (("alone", admitted), ("confirmed", final), ("typed_reference", reference)):
            events = [(q, r, relay.named(selection, focus, roster, q, r))
                      for focus, roster, q, r in product(range(4), relay.archive.PAIRS, (0, 1), (0, 1))]
            results[method] = relay.total(reference, events, c.question_loss, c.reply_loss)
        outcomes[key] = {"reference": reference, "initial": admitted, "asked": bool(clarified),
                         "authored_confirmation": bool(clarified and reference[0] != "unspecified"),
                         "final": final, "reason": why, "metrics": results}
    for key, (text, output, admitted) in {**context.replay.FOILS, **context.FRESH_CONTEXTS}.items():
        result, reason = compiled(text, output, True)
        observed = bool(result and result[0] != "unspecified")
        assert observed == admitted
        diagnostics[key] = {"admitted": observed, "reason": reason}
    kinds = {}
    for kind in ("one", "all", "any", "unspecified"):
        rows = [row for row in outcomes.values() if row["reference"][0] == kind]
        kinds[kind] = {"cases": len(rows), "clarifications": sum(row["asked"] for row in rows),
                       "authored_answers": sum(row["authored_confirmation"] for row in rows),
                       "mean_resolution": {label: sum(row["metrics"][label]["correct_resolution_probability"]
                                                      for row in rows) / len(rows)
                                           for label in ("alone", "confirmed", "typed_reference")}}
    return {"scope": "The exact-span decoder stays first. Withheld dispatches go to an explicit confirmation "
                     "contract. Responses in the simulation are gold typed answers for determinate requests, "
                     "not human replies or model predictions. There is no added response for unspecified requests. "
                     "The expected resolution metric measures the existing one-reply transport.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "model_evidence_sha256": sha256(path.read_bytes()).hexdigest(),
            "categories": kinds, "cases": outcomes,
            "scope_context_foils": diagnostics, "confirmation_validation": comparisons()}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
