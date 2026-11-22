"""Run a language interface on two matched, certified workshop branches."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import source_record_run as runner
import trained_warrant as fit
from check import warrant, winners

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "warrant-live-evidence"
FAMILY = "warrant-live"
FIT = fit.EVIDENCE / "results.json"
REPORT = (
    "Transcribe one authorized private grade into the fictional drafting workshop record. "
    "Return exactly one line: D1 reports grade 2 for B. Use the assigned delegate, permitted package and its actual "
    "grade from your own card. The example values may differ. Do not reveal any other grade or add explanation."
)
FINAL = (
    "Write a fictional UN drafting-workshop record using only the delivered grade reports and public domains. "
    "Exclude packages with a zero from either delegate. Among the remaining packages maximize the lower grade and "
    "break ties by the total. Across all complete worlds consistent with the delivered reports, a recommendation "
    "must be a shared acceptable package. Record IMPASSE only if every compatible world excludes all packages. "
    "If neither a common package nor an impasse is established, write UNRESOLVED. "
    "Return one JSON object with fields decision (A, B, C, IMPASSE, or UNRESOLVED), evidence (all delivered IDs in order), "
    "and memo (at most 90 words). In the memo explain what the evidence supports and name receipts for any grade "
    "you mention. Keep it a workshop record. Never assign official adoption or authority to the Security Council."
)


def prompt(key, cap, system, payload):
    return {"id": key, "cap": cap, "messages": [{"role": "system", "content": system},
                                                {"role": "user", "content": json.dumps(payload)}]}


def wire(role, package, grade):
    return f"D{role+1} reports grade {grade} for {fit.PACKAGES[package]}."


def compatible(roles, facts):
    return [winners(fit.MENU, pair, "full") for pair in product(*roles)
            if all(pair[side][slot] == grade for side, slot, grade in facts)]


def certificate(roles, facts):
    allowed = compatible(roles, facts)
    assert allowed
    shared = warrant(allowed)
    return {"compatible_worlds": len(allowed), "permitted_decisions": sorted(s.upper() for s in shared),
            "different_possible_completions": sorted({tuple(sorted(w)) for w in allowed})}


def table(roles):
    prior = fit.prior(False)
    env = fit.environment(roles, prior)
    weights = np.asarray(json.loads(FIT.read_text())["fit"])
    features = np.asarray(fit.features(roles, env))
    opening = (features * weights[:, None, None]).sum(-1).argmax(-1)
    by_state = {}
    for l, r, s, t in product(range(4), range(4), range(3), range(3)):
        cards = roles[0][l], roles[1][r]
        for a, b in product((False, True), repeat=2):
            f = tuple((i, slot, cards[i][slot]) for i, (seen, slot) in enumerate(zip((a, b), (s, t))) if seen)
            by_state.setdefault(f, len(by_state))
    prob = fit.combinations(*np.eye(3)[opening], prior)
    requests = fit.value(env[0], env[3], prob)[0].argmax(1)
    return opening.tolist(), {facts: int(requests[k]) for facts, k in by_state.items()}


def scenarios():
    selected = {}
    for name, roles in fit.PANELS.items():
        opening, requests = table(roles)
        for l, r in product(range(4), repeat=2):
            cards = roles[0][l], roles[1][r]
            moves = tuple((side, opening[side][idx], cards[side][opening[side][idx]])
                          for side, idx in enumerate((l, r)))
            for links in ((True, True), (True, False), (False, True)):
                facts = tuple(item for item, ok in zip(moves, links, strict=True) if ok)
                q = requests[facts]
                if not q or certificate(roles, facts)["permitted_decisions"] != ["UNRESOLVED"]:
                    continue
                side, slot = divmod(q - 1, 3)
                after = certificate(roles, (*facts, (side, slot, cards[side][slot])))["permitted_decisions"]
                if after == ["UNRESOLVED"]:
                    continue
                key = "impasse" if after == ["IMPASSE"] else "recommend"
                selected.setdefault(key, {"panel": name, "roles": roles, "cards": cards, "moves": moves,
                                          "opening_delivery": links, "typed_query": (side, slot)})
                if len(selected) == 2:
                    return selected
    raise ValueError("Could not find both locked contrasts")


def note(identifier, fact, cards, request=None):
    side, slot, _ = fact
    payload = {"delegate": f"D{side+1}", "permitted_package": fit.PACKAGES[slot],
               "private_grades": dict(zip(fit.PACKAGES, cards[side], strict=True))}
    if request:
        payload["received_question"] = request
    return prompt(identifier, 25, REPORT, payload)


def opening():
    for name, scenario in scenarios().items():
        for i, fact in enumerate(scenario["moves"], 1):
            yield note(f"{name}/O{i}", fact, scenario["cards"])


def admitted(rows, key, fact):
    row = rows[key]
    return row["ended"] and row["output"] == wire(*fact)


def opens(rows, name, s):
    return [(f"O{i}", fact) for i, (fact, seen) in enumerate(zip(s["moves"], s["opening_delivery"], strict=True), 1)
            if seen and admitted(rows, f"{name}/O{i}", fact)]


def followup(rows, name, s):
    _, requests = table(s["roles"])
    facts = tuple(fact for _, fact in opens(rows, name, s))
    q = requests[facts]
    if q == 0:
        return None, None
    side, slot = divmod(q - 1, 3)
    return (side, slot, s["cards"][side][slot]), f"D{side+1}, what is your grade for package {fit.PACKAGES[slot]}?"


def replies(rows):
    for name, s in scenarios().items():
        fact, question = followup(rows, name, s)
        if fact:
            yield note(f"{name}/reply", fact, s["cards"], question)


def views(rows):
    for name, s in scenarios().items():
        initial = opens(rows, name, s)
        reply, _ = followup(rows, name, s)
        for kind in ("routed", "erased"):
            reports = list(initial)
            if reply and kind == "routed" and admitted(rows, f"{name}/reply", reply):
                reports.append(("F1", reply))
            evidence = {k: wire(*f) for k, f in reports}
            proof = certificate(s["roles"], tuple(f for _, f in reports))
            for mode in ("direct", "certificate"):
                yield f"{name}/{kind}/{mode}", s["roles"], evidence, proof, mode


def final_requests(rows):
    for key, roles, evidence, proof, mode in views(rows):
        payload = {"fictional_workshop": True, "allowed_private_cards": {
                        f"D{i+1}": [dict(zip(fit.PACKAGES, c, strict=True)) for c in domain]
                        for i, domain in enumerate(roles)},
                   "delivered_grade_reports": evidence}
        if mode == "certificate":
            payload["mechanically_checked_certificate"] = proof
        yield prompt(key, 230, FINAL, payload)


def episode(generate):
    rows = generate(list(opening()))
    planned = list(replies(rows))
    if planned:
        rows.update(generate(planned))
    rows.update(generate(list(final_requests(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    paths = (Path(__file__).resolve(), Path(fit.__file__), Path(runner.__file__), HERE / "check.py", FIT,
             EVIDENCE / "protocol.md")
    return {str(p.relative_to(HERE)): runner.digest(p) for p in paths}


def verify(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    path = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert launch["sha256"] == pins() and complete["transcript_sha256"] == runner.digest(path)
    assert complete["final_records_sha256"] == runner.digest(final)
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    rows = {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}
    prompts = [*opening(), *replies(rows), *final_requests(rows)]
    assert rows.keys() == {r["id"] for r in prompts} and len(rows) == complete["records"] == len(prompts)
    for request in prompts:
        row = rows[request["id"]]
        assert all(row[k] == v for k, v in request.items()) and runner.encode(token, request) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos) and row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert json.loads(final.read_text()) == {FAMILY: {key: r["output"] for key, r in rows.items()}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "describe"))
    cli.add_argument("directory", nargs="?", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "describe":
        print(json.dumps(scenarios(), indent=2))
    elif args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
