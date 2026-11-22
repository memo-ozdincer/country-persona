"""Test separate receipt-status and clause classification before a learned handoff."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import receipt_ack_language as previous

HERE = previous.HERE
runner = previous.runner
DRC = HERE / "case.json"
PRIOR = HERE / "receipt-ack-language-evidence/results.json"
ORDERS = {2: ((0, 1), (1, 0)), 4: ((0, 1, 2, 3), (3, 2, 1, 0)), 5: previous.DECODE_ORDERS}
LABELS = {
    "unami": ("one-time independent strategic review", "recurring reporting on mission responsibilities",
              "expiry of the existing mission mandate", "participants consulted for the strategic review"),
    "drc": ("one-time midterm report to the Council", "monthly updates to the Committee",
            "expiry of the existing Group of Experts mandate", "intended review and possible further extension"),
}
# Second docket has the same delivery interface but different institutions,
# distinct operative verbs and a different clause inventory.
DRC_SPANS = (
    "It requested a midterm report to the Council after discussion with the Committee by 30 December 2023 and a final report by 15 June 2024.",
    "The Group was to send monthly updates to the Committee except in the two report-due months.",
    "The Council extended the Group of Experts mandate to 1 August 2024",
    "intended to review it and act on a possible further extension by 1 July 2024.",
)


def cards():
    raw = previous.load(DRC)["sources"]["EXPERTS"]["card"]
    assert all(span in raw for span in DRC_SPANS)
    return {"unami": tuple(previous.clauses().values()), "drc": DRC_SPANS}


def conditions():
    for family, excerpts in cards().items():
        yield family, "absent", None, "No receipt has been communicated.", None
        for index, excerpt in enumerate(excerpts):
            if family == "unami":
                ack = previous.wire("received", index, previous.clauses())
                waiting = previous.wire("planned", index, previous.clauses())
            else:
                ack = "The chair logged the following excerpt as received: " + excerpt
                waiting = "The desk expects to send this next, but no receipt was logged: " + excerpt
            yield family, "received", index, ack, excerpt
            yield family, "planned", index, waiting, excerpt
        # Distinguish a still-valid acknowledgment from a later withdrawal.
        yield family, "withdrawn", 1, (
            f"The chair had confirmed this passage earlier: {excerpts[1]} "
            "That acknowledgment was withdrawn after checking. The passage is no longer logged as received."
        ), excerpts[1]


def coded(family, kind, index, stage, instruction, text, menu):
    for n, order in enumerate(ORDERS[len(menu)]):
        codes = {c: menu[i] for c, i in zip("ABCDE", order)}
        yield previous.row((family, stage, kind, index, n), instruction + " Return only the selection letter.",
                           {"text": text, "answer_options": codes}, order)


def prompts():
    for family, kind, index, message, excerpt in conditions():
        yield from coded(family, kind, index, "status",
                         "Determine whether the chair currently acknowledges receipt of the quoted passage. "
                         "Read the envelope, including any later correction or withdrawal.",
                         message, ("currently confirmed received", "no current confirmed receipt"))
        yield from coded(family, kind, index, "joint",
                         "Choose the field in the passage only if the chair currently acknowledges receipt. "
                         "Select no receipt for an unconfirmed send, no message, or a withdrawn acknowledgment.",
                         message, (*LABELS[family], "no current confirmed receipt"))
        if kind == "received":
            yield from coded(family, "body", index, "field",
                             "Classify the obligation or institutional act in this passage. "
                             "Read the verb, actor, recipient and timing for the specific requested act.",
                             excerpt, LABELS[family])


def pins():
    files = (Path(__file__), DRC, PRIOR, *(HERE.parents[1] / p for p in previous.pins()))
    return {str(p.relative_to(HERE.parents[1])): previous.sha256(p.read_bytes()).hexdigest() for p in files}


def stable(votes):
    return votes[0] if votes[0] == votes[1] else None


def results(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        raw = runner.read(directory)
    original = previous.load(PRIOR)
    choice = {tuple(v["condition"]): v["choices"] for v in original["actions"]}
    outcomes = {family: [] for family in LABELS}
    for family, kind, index, message, _ in conditions():
        body = previous.pick(raw, (family, "field", "body", index)) if index is not None else [None, None]
        status = previous.pick(raw, (family, "status", kind, index))
        direct = previous.pick(raw, (family, "joint", kind, index))
        content = stable(body)
        confirmed = stable(status)
        composed = content if confirmed == 0 else 4 if confirmed == 1 else None
        outcomes[family].append({"kind": kind, "field": index, "message": message,
                                 "expected": index if kind == "received" else 4,
                                 "field_choices": body, "status_choices": status, "joint_choices": direct,
                                 "separate": composed, "joint": stable(direct)})
    counts = {}
    for family, cases in outcomes.items():
        counts[family] = {}
        for method in ("separate", "joint"):
            counts[family][method] = {
                "correct_positive": sum(r[method] == r["expected"] for r in cases if r["kind"] == "received"),
                "correct_negative": sum(r[method] == 4 for r in cases if r["kind"] != "received"),
                "false_receipt": sum(r[method] in range(4) for r in cases if r["kind"] != "received"),
                "order_disagreement": sum(r[method] is None for r in cases),
            }
    transfers = {}
    for family, cases in outcomes.items():
        transfers[family] = {}
        for method in ("separate", "joint"):
            decode = {(row["kind"], row["field"]): [row[method]] * 2 for row in cases}
            replay = previous.replay(choice, decode, False)
            # The probabilities depend on the decoded slot. Only UNAMI is
            # physically assembled by the UNAMI outcome table.
            columns = ("complete", "calendar", "record_points") if family == "unami" else ("complete",)
            transfers[family][method] = {key: {name: {m: r[m] for m in columns} for name, r in data.items()
                                                if name in ("host_typed_learned", "decoded_learned", "decoded_no_ack")}
                                         for key, data in replay.items()}
    return {"scope": "Same-assistant authored receipt envelopes and exact documentary excerpt bodies. "
                     "The separate model sees paragraph boundaries supplied by the harness. "
                     "The DRC replay projects the slot readings onto the same abstract delivery game; no DRC prose composer is scored.",
            "counts": counts, "examples": outcomes, "replay": transfers}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(results(args.directory), ensure_ascii=False, indent=2))
