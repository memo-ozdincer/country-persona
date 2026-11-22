"""Test whether a proof table keeps workshop memo explanations faithful."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import warrant_live as base
from warrant_live_compile import parse_reports
from check import winners

HERE = base.HERE
EVIDENCE = HERE / "warrant-reasons-evidence"
FAMILY = "warrant-reasons"
ARCHIVE = base.EVIDENCE / "authorized-only/results.json"
GENERAL = base.fit.EVIDENCE / "generalization.json"
ADDED = (" The mechanically computed package table separates feasibility from being best. "
         "Use its feasibility column for zero-grade exclusions and its optimality column for ranking. "
         "Different possible best choices can leave the decision unresolved even when packages are feasible. "
         "Explain what the admitted receipts imply through the public grade domains.")


def policy(roles, correlated, weights):
    fit = base.fit
    prior = fit.prior(correlated)
    env = fit.environment(roles, prior)
    features = np.asarray(fit.features(roles, env))
    opening = (features * weights[:, None, None]).sum(-1).argmax(-1)
    receipt_indices = {}
    for l, r, a, b in product(range(4), range(4), range(3), range(3)):
        cards = roles[0][l], roles[1][r]
        for links in product((False, True), repeat=2):
            facts = tuple((i, slot, cards[i][slot]) for i, slot in enumerate((a, b)) if links[i])
            receipt_indices.setdefault(facts, len(receipt_indices))
    value = fit.value(env[0], env[3], fit.combinations(*np.eye(3)[opening], prior))[0]
    return opening.tolist(), {facts: int(value[m].argmax()) for facts, m in receipt_indices.items()}


def delivered(roles, plan, types, links):
    opening, requests = plan
    cards = tuple(roles[side][kind] for side, kind in enumerate(types))
    facts = tuple((side, opening[side][kind], cards[side][opening[side][kind]])
                  for side, kind in enumerate(types) if links[side])
    labels = [f"O{i+1}" for i, seen in enumerate(links[:2]) if seen]
    q = requests[facts]
    if q and all(links[2:]):
        side, slot = divmod(q - 1, 3)
        facts = (*facts, (side, slot, cards[side][slot]))
        labels.append("F1")
    evidence = dict(zip(labels, (base.wire(*f) for f in facts), strict=True))
    return evidence, base.certificate(roles, facts)


def fresh_views():
    scored = json.loads(GENERAL.read_text())
    report = json.loads(base.FIT.read_text())
    weights = {arm: np.asarray(report[key]) for arm, key in (("initial", "initial"), ("fitted", "fit"))}
    panels = {p["index"]: p for p in scored["panels"]}
    for case in scored["comparisons"]:
        if abs(case["delta"]) < 1e-10:
            continue
        idx, prior = case["panel"], case["prior"]
        roles = panels[idx]["domain"]
        plans = {arm: policy(roles, prior == "correlated", w) for arm, w in weights.items()}
        for a, b, *links in product(range(4), range(4), *((True, False),) * 4):
            options = {arm: delivered(roles, plan, (a, b), links) for arm, plan in plans.items()}
            if options["initial"][1]["permitted_decisions"] == options["fitted"][1]["permitted_decisions"]:
                continue
            for arm, (evidence, proof) in options.items():
                yield f"domain{idx}-{prior}/{arm}", roles, evidence, proof
            break
        else:
            raise ValueError(f"No decision contrast in {idx}/{prior}")


def all_views():
    old = json.loads(ARCHIVE.read_text())["finals"]
    for key, view in old.items():
        if key.endswith("/certificate"):
            yield key.rsplit("/", 1)[0], view["roles"], view["admitted_reports"], view["proof"]
    yield from fresh_views()


def logic(roles, evidence):
    facts = parse_reports(evidence)
    worlds = [world for world in product(*roles)
              if all(world[side][package] == grade for side, package, grade in facts)]
    optimum = [winners(base.fit.MENU, w, "full") for w in worlds]
    table = {}
    for i, package in enumerate(base.fit.PACKAGES):
        pairs = [(min(a[i], b[i]), a[i] + b[i]) for a, b in worlds if a[i] and b[i]]
        def status(n):
            return "all" if n == len(worlds) else ("some" if n else "none")
        table[package] = {"feasible_in_compatible_worlds": status(len(pairs)),
                          "best_in_compatible_worlds": status(sum(package in grades for grades in optimum))}
        if pairs:
            low, total = zip(*pairs, strict=True)
            table[package]["feasible_lower_grades"] = [min(low), max(low)]
            table[package]["feasible_total_grades"] = [min(total), max(total)]
    return table


def requests():
    for key, roles, evidence, proof in all_views():
        payload = {"fictional_workshop": True,
                   "allowed_private_cards": {f"D{i+1}": [dict(zip(base.fit.PACKAGES, card, strict=True))
                                                         for card in role] for i, role in enumerate(roles)},
                   "delivered_grade_reports": evidence, "mechanically_checked_certificate": proof}
        yield base.prompt(f"{key}/certificate", 230, base.FINAL, payload)
        yield base.prompt(f"{key}/reasons", 230, base.FINAL + ADDED, payload | {"package_comparison": logic(roles, evidence)})


def episode(generate):
    pending = list(requests())
    rows = {}
    for start in range(0, len(pending), 6):
        rows.update(generate(pending[start:start + 6]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), ARCHIVE, GENERAL, base.FIT, Path(base.__file__),
             HERE / "warrant_live_compile.py", Path(base.runner.__file__), EVIDENCE / "protocol.md")
    return {str(p.relative_to(HERE)): base.runner.digest(p) for p in files}


def verify(folder):
    from transformers import AutoTokenizer

    launch = json.loads((folder / "launch.json").read_text())
    complete = json.loads((folder / "complete.json").read_text())
    transcript = folder / "transcript.jsonl"
    finals = folder / "final-records.json"
    assert launch["sha256"] == pins() and complete["transcript_sha256"] == base.runner.digest(transcript)
    assert complete["final_records_sha256"] == base.runner.digest(finals)
    rows = {row["id"]: row for row in map(json.loads, transcript.read_text().splitlines())}
    prompts = list(requests())
    assert len(rows) == len(prompts) == complete["records"]
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    for prompt in prompts:
        row = rows[prompt["id"]]
        assert all(row[k] == v for k, v in prompt.items()) and row["input_ids"] == base.runner.encode(token, prompt)
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos)
        assert row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert json.loads(finals.read_text()) == {FAMILY: {k: row["output"] for k, row in rows.items()}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "describe"))
    cli.add_argument("directory", nargs="?", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        pending = list(requests())
        assert len(pending) == 20
        with patch.multiple(base.runner, episode=episode, locks=pins):
            base.runner.run(args.model, args.directory)
    elif args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        print(json.dumps(list(all_views()), indent=2))
