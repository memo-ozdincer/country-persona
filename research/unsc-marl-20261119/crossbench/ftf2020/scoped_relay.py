"""Execute single, conjunctive and alternative requests with one verified relay."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import corroboration as archive
import written_vote_protocol as binary

HERE = archive.HERE
QUESTION_COST = .05
REPLY_COST = .2


def qualifies(intent, received):
    kind, keys = intent
    actual = set(received)
    if kind in ("one", "all"):
        return set(keys) <= actual
    if kind == "any":
        return bool(set(keys) & actual)
    return False


def named(intent, anchor, inventory, request_kept, reply_kept):
    if intent is None or intent[0] == "unspecified":
        return {"status": "clarify", "requested_ids": [], "received": [], "passage_count": 0,
                "supplement": "", "fees": 0.}
    kind, required = intent
    eligible = set(required)
    assert eligible <= set(archive.KEYS) and eligible
    local = archive.KEYS[anchor]
    received = [local] if local in eligible else []
    missing = [] if qualifies(intent, received) else [key for key in archive.KEYS if key in eligible - set(received)]
    allowed = [archive.KEYS[i] for i in inventory]
    source = next((key for key in missing if key in allowed), None) if request_kept else None
    relay = archive.packet(archive.KEYS.index(source)) if source else None
    if relay and reply_kept:
        assert archive.admit(relay, allowed)
        received.append(source)
    if not received:
        supplement = ""
    else:
        first, *rest = received
        reply = archive.packet(archive.KEYS.index(rest[0])) if rest else None
        supplement = archive.compile_record(archive.packet(archive.KEYS.index(first)), reply, allowed)["supplement"]
    assert len(supplement.split()) <= 85 and len(received) <= 2
    return {"status": "complete" if qualifies(intent, received) else "incomplete",
            "requested_ids": missing, "received": received, "passage_count": len(received),
            "supplement": supplement, "fees": QUESTION_COST * bool(missing) + REPLY_COST * bool(relay)}


def total(intent, rows, q_loss, r_loss):
    require = intent[0] != "unspecified"
    total_score = false_complete = fulfilled = fee = outside_scope = 0.
    for keep_question, keep_reply, output in rows:
        weight = (1 - q_loss if keep_question else q_loss) * (1 - r_loss if keep_reply else r_loss) / 24
        success = qualifies(intent, output["received"]) if require else output["status"] == "clarify"
        total_score += weight * success
        false_complete += weight * (output["status"] == "complete" and not success)
        fulfilled += weight * (output["status"] == "complete")
        outside_scope += weight * bool(set(output["received"]) - set(intent[1]))
        fee += weight * output["fees"]
    return {"correct_resolution_probability": total_score, "claimed_complete_probability": fulfilled,
            "false_completion_probability": false_complete, "records_outside_scope_probability": outside_scope,
            "mean_link_fees": fee}


def run():
    cards = archive.KEYS
    calibration = binary.decoder.transfer.Calibration()
    assessed = {}
    fit_path = HERE / "joint-repair-results.json"
    policy = archive.read(fit_path)
    sender, responder = policy["final_sender"], policy["final_responder"]
    methods = ("repaired_binary", "known_intent_named", "model_intent_named")
    data_path = HERE / "semantic-intent-evidence/results.json"
    records = archive.read(data_path)["records"]
    cases_executed = 0
    for name, data in records.items():
        expected = data["reference"]
        interpretation = data["consensus"]
        branches = {method: [] for method in methods}
        witness = {}
        for anchor, index, q, reply in product(range(4), range(6), (0, 1), (0, 1)):
            roster = archive.PAIRS[index]
            event = binary.execute(sender, responder, anchor, index, q, reply, calibration)
            prior_binary = {"status": "archive_record", "received": event["admitted_sources"],
                            "fees": event["score"] - event["net"]}
            outputs = {"repaired_binary": prior_binary, "known_intent_named": named(expected, anchor, roster, q, reply),
                       "model_intent_named": named(interpretation, anchor, roster, q, reply)}
            for key, response in outputs.items():
                branches[key].append((q, reply, response))
                cases_executed += 1
            if cards[anchor] == "indonesia_national" and index == 5 and q and reply:
                witness = outputs
        assessed[name] = {"intent": expected, "model": interpretation,
                          "metrics": {key: total(expected, rows, calibration.question_loss, calibration.reply_loss)
                                      for key, rows in branches.items()}, "indonesian_pair_example": witness}
    summary = {}
    for category in ("one", "all", "any", "unspecified"):
        scope = [row for row in assessed.values() if row["intent"][0] == category]
        summary[category] = {"requests": len(scope),
                             "methods": {key: {metric: sum(row["metrics"][key][metric] for row in scope) / len(scope)
                                               for metric in scope[0]["metrics"][key]} for key in methods}}
    return {"scope": "Uniform over four protected anchors and six responder inventories. Integrates 10% request and "
                     "reply loss, one reply per mission. Named messages carry explicit requested IDs, a wider alphabet "
                     "than the one-bit repaired protocol. Link fees do not price bandwidth. The reported completion "
                     "criterion checks all or any requested sources and is independent of the diplomacy rubric.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "inputs": {path.name: sha256(path.read_bytes()).hexdigest() for path in (fit_path, data_path)},
            "branches_executed": cases_executed, "summary": summary, "cases": assessed}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
