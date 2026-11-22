"""Execute a resource-matched Outer Space final-record routing contrast."""
import argparse
import json
from itertools import product
from pathlib import Path
from unittest.mock import patch

import numpy as np

import source_record_run as runner
import source_request_policy as routing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "crossbench/space/historical-task.json"
PROVENANCE = TASK.with_name("references.json")
OUT = HERE.parent / "evidence"
NAME = "space-final-routing-transfer"
PUBLIC = ("apr-amendment", "apr-final")
FIELDS = ("japan-reason", "china-reason", "may-final")
GUIDES = (
    "State Japan's reason for the narrower draft and its concern about the proposed treaty.",
    "State China's acceptance of the underlying focus and what broader binding work it sought through the amendment.",
    "Give the date, symbol, status as a standalone draft, vote tally, and reason the proposal did not pass.",
)
NOTE_CAP, CHAIR_CAP = 56, 160
SOLO_CAP = 2 * NOTE_CAP + CHAIR_CAP
PROMPT = (
    "Write a brief historical Security Council record, up to 125 words. Explicitly name each instrument and vote "
    "stage evidenced by the packet. Give the tally, outcome and reason when supplied. Explicitly attribute national "
    "positions and explain the differences. Mark any missing information briefly. State the limits of Council "
    "authority. Treat national proposals and vote explanations as statements, not acts. Use only the supplied "
    "docket and evidence. Return the record alone and omit inline citations."
)
NOTE_PROMPT = (
    "Write one source-faithful sentence, at most 30 words, retaining every fact asked for. Explicitly name the "
    "actor or instrument. Use the source block only. Return the sentence, with no title or citations."
)


def packet():
    return json.loads(TASK.read_text())


def blocks():
    return {r["id"]: r["text"] for r in packet()["evidence"]}


def as_policy(rows):
    return list(map(np.asarray, rows))


def intended():
    weights = {r["id"]: r["weight"] for r in packet()["rubric"]}
    return {"weights": [weights["japan"], weights["china"] + weights["april-second-text"],
                        weights["later-stage"]],
            "joint": (3, sum(weights[k] for k in ("april-first-text", "overlap", "open-issues")))}


def actions(policy, left, right):
    ask, send, reply = policy
    q, a = int(ask[left]), int(send[left])
    b = int(reply[right, q])
    return {"question": q, "delivery": [a, b], "receipt": int(routing.BITS[a] | routing.BITS[b])}


def worlds(learned, independent, payoff):
    entries = []
    for left, right in product(range(1, 8), repeat=2):
        if left | right != 7:
            continue
        peer, quiet = actions(learned, left, right), actions(independent, left, right)
        erased = int(routing.BITS[peer["delivery"][0]] | routing.BITS[learned[2][right, 0]])
        if not all(peer["delivery"]) or not all(quiet["delivery"]):
            continue
        entry = {"left": left, "right": right, "interactive": peer, "independent": quiet,
                 "erased_receipt": erased,
                 "intended_gain": int(payoff[peer["receipt"]] - payoff[quiet["receipt"]])}
        entries.append(entry)
    # One planned opportunity and one planned counterexample, picked without model outputs.
    good = max(entries, key=lambda r: (r["intended_gain"],
               int(payoff[r["interactive"]["receipt"]] - payoff[r["erased_receipt"]])))
    bad = min(entries, key=lambda r: r["intended_gain"])
    if good == bad:
        bad = next(r for r in entries if r != good)
    return {"best-contrast": good, "lowest-contrast": bad}


def fit(output):
    case = intended()
    prior, loss = routing.TEST_PRIORS["uniform"], routing.TRAIN_LOSS
    payoff = routing.points(case)
    matrix = routing.receipt_matrix(payoff, loss)
    with patch.multiple(routing, TRAIN_IDS=("public-rubric",), TRAIN_PRIORS={"public-rubric": prior}):
        *learned, trace = routing.train({"public-rubric": case})
    independent = routing.best_silent(prior, matrix)
    plan, count = routing.exact_optional(prior, matrix, loss)
    policies = {"interactive": learned, "independent": independent, "exact": plan}
    data = {"rubric_sha256": runner.digest(TASK), "trainer_sha256": runner.digest(Path(routing.__file__)),
            "planned_reward": payoff.tolist(), "seed": routing.SEED, "updates": len(trace), "trace": trace,
            "prior": "uniform", "loss": loss, "exact_maps": count,
            "policies": {name: [r.tolist() for r in policy] for name, policy in policies.items()},
            "planned_net": {name: routing.evaluate(p, prior, payoff, loss)["net"]
                            for name, p in policies.items()},
            "worlds": worlds(learned, independent, payoff)}
    output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"worlds": data["worlds"], "planned_net": data["planned_net"]}, indent=2))


def request(identifier, system, body, cap, allowed):
    return {"id": identifier, "cap": cap, "evidence_ids": list(allowed), "seen": [],
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def role_requests(data):
    source = blocks()
    for name, world in data["worlds"].items():
        for arm in ("interactive", "independent"):
            for side, field in zip(("left", "right"), world[arm]["delivery"], strict=True):
                name_id = FIELDS[field - 1]
                yield request(f"{name}.{arm}.{side}", NOTE_PROMPT,
                              {"task": GUIDES[field - 1], "source": {name_id: source[name_id]}},
                              NOTE_CAP, [name_id])


def chair_requests(data, notes):
    source = blocks()
    docket = {k: source[k] for k in PUBLIC}
    for name, world in data["worlds"].items():
        for arm in ("interactive", "independent"):
            ids = [f"{name}.{arm}.{side}" for side in ("left", "right")]
            delivered = {r["evidence_ids"][0]: r["output"] for r in (notes[k] for k in ids)}
            body = {"task": packet()["task"], "docket": docket, "delivered_source_notes": delivered}
            yield request(f"{name}.{arm}.final", PROMPT, body, CHAIR_CAP, [*PUBLIC, *delivered])


def solo_requests(data):
    source = blocks()
    for name in data["worlds"]:
        body = {"task": packet()["task"], "docket": {k: source[k] for k in PUBLIC},
                "delivered_source_notes": {k: source[k] for k in FIELDS}}
        yield request(f"{name}.pooled-solo.final", PROMPT, body, SOLO_CAP, [*PUBLIC, *FIELDS])


def run(directory, policy, model):
    data = json.loads(policy.read_text())
    def episode(generate):
        notes = generate(list(role_requests(data)))
        chairs = generate(list(chair_requests(data, notes)))
        solos = generate(list(solo_requests(data)))
        return [{"family": NAME, "final": {**chairs, **solos}}]

    def locks():
        paths = (Path(__file__).resolve(), TASK, PROVENANCE, policy.resolve(),
                 Path(runner.__file__), Path(routing.__file__))
        return {p.name: runner.digest(p) for p in paths}

    with patch.multiple(runner, episode=episode, locks=locks):
        runner.run(model, directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("fit", "run"))
    cli.add_argument("--policy", type=Path, required=True)
    cli.add_argument("--directory", type=Path, default=OUT / NAME)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "fit":
        fit(args.policy)
    else:
        run(args.directory, args.policy, args.model)
