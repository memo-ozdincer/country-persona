"""Collect isolated source-ranking calls on the held Somalia docket."""
import argparse
from hashlib import sha256
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "myanmar" / "shift" / "policy"))
import interval_search as router

n, e = router.n, router.s.q.e
OUT = HERE / "evidence"
SOURCE = HERE / "case.json"
LIB = router.s.q.t.old
DEPENDENCIES = {"local-procurement": {"china", "somalia"}, "different-emphases": {"china", "us"}}


def plan():
    case = n.read(SOURCE)
    blocks = {x["id"]: x["text"] for x in case["public"]}
    menus = case["menus"]
    compiled = {}
    requests = []
    for role, entries in menus.items():
        compiled[role] = {}
        for label, text in entries.items():
            start = blocks[role].index(text)
            compiled[role][label] = {"source": role, "start": start, "end": start + len(text), "text": text}
        instruction = ("Select passage IDs that preserve this speaker's distinct position. "
                       + case["prompts"][role] +
                       " Return only a JSON array of ID strings ordered by importance. Omit merely secondary detail.")
        payload = {"task": case["task"], "speaker": role, "passages": entries}
        requests.append({"part": role, "request": LIB.b.request(instruction, payload, 72)})
    weights = {entry["id"]: entry["weight"] for entry in case["rubric"]}
    score = {mask: sum(weights[k] for k, owners in DEPENDENCIES.items()
                       if owners == {role for bit, role in zip(n.BITS[1:], case["roles"]) if bit & mask})
             for mask in (3, 5, 6)}
    chosen = max(score, key=score.get)
    assert chosen == router.s.PAIR == 3
    paths = (Path(__file__), HERE / "protocol.md", SOURCE, Path(router.__file__))
    return {"requests": requests, "spans": compiled, "calibration_pair": chosen, "pair_dependency_weights": {str(k): v for k, v in score.items()},
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


def collect(generate, directory):
    current = plan()
    assert current == n.read(HERE / "plan.json")
    for request in current["requests"]:
        row = request | {"response": generate(request["request"])}
        n.base.suite.append(directory / "calls.jsonl", row)


def calls():
    rows = n.lines(OUT / "calls.jsonl")
    assert [{k: row[k] for k in ("part", "request")} for row in rows] == plan()["requests"]
    return rows


def verify():
    assert plan() == n.read(HERE / "plan.json")
    with patch.object(n, "OUT", OUT), patch.object(LIB.audit, "calls", calls):
        return LIB.audit.verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        with patch.object(n.base.suite, "collect", collect), patch.object(
                n.base, "roster", return_value={"somalia-2753-passage-selection": None}):
            n.base.run(OUT)
    else:
        e.emit(plan() if mode == "plan" else verify())
