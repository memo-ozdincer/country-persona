"""Keep the local menu fixed while giving France receiver context."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import compose_notes as source
import select_notes as original

READ, prior, frozen = original.READ, original.prior, original.frozen
CHAIR = ("The chair already has the public record. Send any distinct national position on the scope "
         "or implementation of a treaty or resolution if your menu contains one. "
         "Otherwise select a distinctive implementation reason or qualification.")
MODES = ("lead", "request")


def plan():
    files = (Path(__file__), HERE / "protocol.md", PARENT / "plan.json", PARENT / "select_notes.py",
             PARENT / "scores.json", PARENT / "routing.json", PARENT / "verified.json")
    before = READ(PARENT / "plan.json")["requests"]
    requests = []
    for req in before:
        order, desk = req["id"].split("/")
        if desk != "0":
            continue
        payload = json.loads(req["messages"][1]["content"])
        for arm in MODES:
            updated = {**payload, "public_already_available_to_chair": original.PUBLIC}
            if arm == "request":
                updated["chair_request"] = CHAIR
            messages = [req["messages"][0], {"role": "user", "content": json.dumps(updated, ensure_ascii=False)}]
            requests.append(req | {"id": f"{order}/{arm}", "messages": messages})
    assert len(requests) == 4
    counts = [sum(len(candidate["forms"]) for candidate in original.legal_forms(original.menu(req))) for req in requests]
    return {"requests": requests, "candidate_counts": counts,
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in files}}


def runtime(mode):
    with patch.object(original, "plan", plan), patch.object(original, "HERE", HERE), patch.object(
            original, "OUT", HERE / "evidence"):
        return mode()


def score():
    current = READ(HERE / "verified.json")
    previous = READ(PARENT / "scores.json")
    routing = READ(PARENT / "routing.json")
    aliases = routing["condition_aliases"]
    results, banks = {}, {}
    for name, reply in current["selections"].items():
        order, arm = name.split("/")
        base = previous["selections"][f"{order}/native"]
        selected = [reply["native"], *base[1:]]
        record = [source.render(selected, mask) for mask in range(8)]
        grades = [row["score"]["released_70"] for row in record]
        keys = [k for k, bank in previous["banks"].items() if bank == grades]
        assert keys
        route = routing["results"][aliases[keys[0]]]["summary"]
        results[name] = {"france": selected[0], "bank": grades, "records": record,
                         "reused_route": aliases[keys[0]], "routing_summary": route}
        banks.setdefault(arm, []).append(grades)
    assert all(len(b) == 2 for b in banks.values())
    return {"results": results, "same_bank_across_orders": {arm: b[0] == b[1] for arm, b in banks.items()},
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), HERE / "verified.json",
                                                        HERE / "plan.json", PARENT / "routing.json")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    if mode == "run":
        runtime(original.run)
    else:
        frozen.emit({"plan": plan, "verify": lambda: runtime(original.verify), "score": score}[mode]())
