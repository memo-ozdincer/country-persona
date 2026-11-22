"""Run two public mandate declarations and the fixed v1 Iraq writer."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "syria-baseline"
CLARIFY = HERE.parent / "syria-targeted-clarification"
sys.path.insert(0, str(CLARIFY))
import route
import confirm

E = route.E
COLLECTOR = route.collection.BASE
LEDGER = route.LEDGER
FIELDS = {"term": ["retain", "shorten"], "documentation": ["public", "annex"]}


def cases():
    return {k: v for k, v in E.cases().items() if v["family"] == "iraq"}


def make_dialogue_request(case, order, reported):
    role_index = order if reported is None else 1 - order
    role = case["roles"][role_index]
    system = (
        "You are the named replying workshop delegate. Report your own full fictional requirement from "
        "your own card. Your declaration means you can accept exactly the options satisfying it. "
        "Do not infer anyone else's requirement or report a joint outcome. "
        "Return only a JSON object with exactly two string keys, field and value."
    )
    public = {"role": role, "own_card": case["owned"][role_index][0]["text"],
              "menu": [{"id": p["id"], "proposal": p["text"]} for p in case["options"]],
              "field_dictionary": FIELDS}
    if reported is not None:
        public["prior_declaration"] = {"role": reported["role"], "stated_requirement": reported["condition"]}
    return {"max_output_tokens": 100, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(public, ensure_ascii=False)}
    ]}


def declaration(response):
    with patch.object(route.collection, "FIELDS", FIELDS):
        return route.parse(response)


def full(case, role, condition):
    if condition is None:
        return None
    allowed = route.environment.allowed(case["options"], condition)
    assert allowed
    return route.full(role, allowed)


def proof_action(case, roles, public):
    # Keep the same relevance check with the new public case dictionary.
    with patch.object(route.collection, "FIELDS", FIELDS):
        can_complete = [any(route.query(roles, public, i, option)["decision"] != "U" for option in
                            confirm.public_candidates(case["options"], roles, public, i)) for i in (0, 1)]
    return can_complete


def native_request(case, order, arm, prior):
    # Use the same release API for the exact independent control.
    return E.build_request(case, arm, order, prior)


def note(role, condition):
    requirement = "No valid full declaration was supplied."
    if condition is not None:
        field, value = next(iter(condition.items()))
        requirement = f"My complete fictional mandate is {field} = {value}. I accept exactly the options satisfying it."
    return {"speaker": role, "text": requirement}


def writer_request(case, order, reported, proof):
    req = E.build_request(case, "peer", order, reported)
    if proof is not None:
        packet = json.loads(req["messages"][1]["content"])
        symbol = proof["decision"]
        result = {"I": "IMPASSE", "U": "UNRESOLVED"}.get(symbol, symbol)
        packet["mechanical_workshop_certificate"] = {
            "decision": result,
            "limits": "Fictional workshop result only. This establishes no official action, vote or authority.",
            "certifying_disclosures": proof["state"].get("verified_options") or proof["state"].get("blocked_options"),
        }
        req["messages"][1]["content"] = json.dumps(packet, ensure_ascii=False)
    return req


def pins():
    paths = (Path(__file__), HERE / "protocol.md", E.HERE / "release.json",
             CLARIFY / "confirm.py", CLARIFY / "route.py")
    return {str(p.relative_to(HERE.parent.parent)): COLLECTOR.sha(p) for p in paths}


def collect(generate, directory):
    rows = []
    for key, case in cases().items():
        for order in (0, 1):
            independent = []
            for _ in range(3):
                req = native_request(case, order, "independent", independent)
                response = generate(req)
                independent.append({"request": req, "response": response, "speaker": req["speaker"],
                                    "text": response["text"]})
            roles = case["roles"][::1 if order == 0 else -1]
            first_req = make_dialogue_request(case, order, None)
            first_raw = generate(first_req)
            first = declaration(first_raw)
            msgs = [statement for statement in [full(case, roles[0], first)] if statement is not None]
            possible = proof_action(case, roles, msgs)
            assert not possible[0]
            second_record = None
            second = None
            if possible[1]:
                second_req = make_dialogue_request(case, order, {"role": roles[0], "condition": first})
                second_raw = generate(second_req)
                second = declaration(second_raw)
                second_record = {"request": second_req, "response": second_raw}
                if statement := full(case, roles[1], second):
                    msgs.append(statement)
            proof = route.readout(roles, msgs)
            reported = [note(roles[0], first), note(roles[1], second)]
            writers = {}
            for arm, certificate in (("typed_notes", None), ("with_certificate", proof)):
                req = writer_request(case, order, reported, certificate)
                writers[arm] = {"request": req, "response": generate(req)}
            rows.append({"id": f"{key}/{order}", "roles": roles, "independent": independent,
                         "first": {"request": first_req, "response": first_raw}, "second": second_record,
                         "extracted": [first, second], "can_complete_proof": possible,
                         "public_claims": msgs, "ledger": proof, "rendered_notes": reported, "writers": writers})
            COLLECTOR.suite.append(directory / "episodes.jsonl", rows[-1])
    (directory / "transfer-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    assert all(COLLECTOR.sha(directory / f) == stamp for f, stamp in E.read(directory / "complete.json").items())
    assert E.read(directory / "transfer-lock.json") == pins()
    t = AutoTokenizer.from_pretrained(COLLECTOR.MODEL, local_files_only=True)
    eos = t.convert_tokens_to_ids("<|im_end|>")
    traces = iter(json.loads(line) for line in (directory / "tokens.jsonl").read_text().splitlines())
    count = 0
    runs = [json.loads(line) for line in (directory / "episodes.jsonl").read_text().splitlines()]
    assert len(runs) == 4
    for row in runs:
        key, order = row["id"].split("/")
        order = int(order)
        case = cases()[key]
        roles = case["roles"][::1 if order == 0 else -1]
        assert row["roles"] == roles
        for i, earlier in enumerate(row["independent"]):
            assert native_request(case, order, "independent", row["independent"][:i]) == earlier["request"]
        first, second = row["extracted"]
        assert row["first"]["request"] == make_dialogue_request(case, order, None)
        assert declaration(row["first"]["response"]) == first
        messages = [m for m in [full(case, roles[0], first)] if m is not None]
        assert row["can_complete_proof"] == proof_action(case, roles, messages)
        if row["second"]:
            assert row["second"]["request"] == make_dialogue_request(case, order, {"role": roles[0], "condition": first})
            assert declaration(row["second"]["response"]) == second
            if message := full(case, roles[1], second):
                messages.append(message)
        assert row["public_claims"] == messages and row["ledger"] == route.readout(roles, messages)
        reported = [note(role, value) for role, value in zip(roles, row["extracted"], strict=True)]
        for arm, repaired in row["writers"].items():
            assert repaired["request"] == writer_request(case, order, reported,
                                                          row["ledger"] if arm == "with_certificate" else None)
        calls = [*row["independent"], row["first"], row["second"], *row["writers"].values()]
        for call in filter(None, calls):
            actual = next(traces)
            assert COLLECTOR.prompt(t, call["request"]) == actual["input_ids"] and call["response"] == actual["response"]
            ids = actual["output_ids"]
            assert len(ids) <= call["request"]["max_output_tokens"] and eos not in ids[:-1]
            assert (ids[-1] == eos) == (actual["response"]["termination"] == "complete")
            assert t.decode(ids, skip_special_tokens=True).strip() == actual["response"]["text"]
            count += 1
    assert next(traces, None) is None
    return {"verified_calls": count, "episodes": len(runs), "optimizer_updates": 0}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("--directory", type=Path, default=HERE / "evidence")
    args = p.parse_args()
    if args.mode == "run":
        with patch.object(COLLECTOR.suite, "collect", collect), patch.object(COLLECTOR, "roster", cases):
            COLLECTOR.run(args.directory)
    else:
        E.emit(verify(args.directory))
