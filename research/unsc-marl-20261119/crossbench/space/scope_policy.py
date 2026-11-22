"""Learn when to verify and publish a scope constraint under a fixed action budget."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LOOKUP = HERE.parent / "disclosure/clarify/routing/partial/lookup"
sys.path.insert(0, str(LOOKUP))
from lookup import choices, opened, record, terminal

VERIFY_SCOPE = True
ORDINARY_MOVE = False
TRAIN_SEED = 115884
TEST_SEED = 244119
COST = 0.015
CHECK_COST = 0.005


def openings(width, truth, rng):
    offered = tuple(rng.choice([1 << i for i in range(width) if mask & (1 << i)]) for mask in truth)
    return offered[0], 0, offered[1], 0


def panels(widths, seed, per_kind, missing):
    """One verified field per role plus separate package restrictions."""
    rng = random.Random(seed)
    rows = []
    for width in widths:
        count = Counter()
        full = (1 << width) - 1
        while min(count[False], count[True]) < per_kind:
            pools = [0, 0, 0]
            categories = list(range(3)) + rng.choices(range(3), k=width-3)
            rng.shuffle(categories)
            for i, category in enumerate(categories):
                pools[category] |= 1 << i
            scope = tuple(sum(mask for mask in pools if rng.random() < .47) for _ in range(2))
            # A second private restriction can exclude packages inside the retained scopes.
            retained = tuple((full ^ mask) & rng.randint(1, full) for mask in scope)
            if not all(scope) or not all(retained):
                continue
            label = bool(retained[0] & retained[1])
            if count[label] >= per_kind:
                continue
            showing = [full ^ sum(1 << i for i in rng.sample(range(width), missing)) for _ in range(2)]
            local = tuple((menu & known, (full ^ menu) & known)
                          for menu, known in zip(retained, showing, strict=True))
            rows.append((width, retained, local, openings(width, retained, rng), scope))
            count[label] += 1
    return rows


def move_options(width, state, local, role, step, available):
    _, allowed, default = choices(state, local, role, step, width, 0)
    ordinary = allowed[default]
    yes, no = local[role]
    open_ = ((1 << width) - 1) & ~(state[1] | state[3])
    unknown = open_ & ~(yes | no)
    may_check = bool(available & (1 << role)) and bool(unknown) and step + 2 <= width + 1
    baseline = may_check and default[0] != 0 and (
        unknown.bit_count() >= 3 or (default[0] == -1 and unknown.bit_count() >= 2)
    )
    # The scope contents are private even to the actor until verification.
    observation = (
        min(width + 1 - step, 4), min(open_.bit_count(), 4), min(unknown.bit_count(), 3),
        min((open_ & no).bit_count(), 2), min((yes & open_).bit_count(), 2),
        bool(unknown & state[2 * (1 - role)]), default[0], baseline,
    )
    return observation, may_check, baseline, ordinary


def advance(row, state, role, step, available, move, ordinary):
    if move == ORDINARY_MOVE:
        return ordinary[1], ordinary[2], step + 1, available
    scope = row[-1][role]
    assert not scope & row[1][role]
    return record(state, role, scope, False), 1 - role, step + 2, available & ~(1 << role)


def rollout(row, policy, start=None, trace=None, no_scope=False):
    width, _, local, opening, _ = row
    state, role, step, available = start or (opened(opening, local), 1, 0, 3)
    full = (1 << width) - 1
    checks = 0
    while step < width + 1 and not terminal(state, full):
        obs, legal, baseline, ordinary = move_options(width, state, local, role, step, available)
        move = legal and not no_scope and policy.get(obs, baseline)
        if trace is not None and legal:
            trace.append((obs, move, advance(row, state, role, step, available, not move, ordinary)))
        state, role, step, available = advance(row, state, role, step, available, move, ordinary)
        checks += move
    return terminal(state, full), step, checks


def stats(rows, policy, no_scope=False):
    observed, counts = [], Counter()
    for row in rows:
        solved, slots, checks = rollout(row, policy, no_scope=no_scope)
        observed.append(solved)
        tag = "agreement" if row[1][0] & row[1][1] else "impasse"
        counts[tag, "paths"] += 1
        for name, value in (("solved", solved), ("slots", slots), ("checks", checks)):
            counts[tag, name] += value
    return observed, counts


def fitness(counts):
    return sum(counts[k, "solved"] - COST * counts[k, "slots"] - CHECK_COST * counts[k, "checks"]
               for k in ("agreement", "impasse"))


def flatten(counts):
    return {"/".join(k): v for k, v in sorted(counts.items())}


def fit(rows):
    policy = {}
    initial, base = stats(rows, policy)
    history = []
    current = base
    for _ in range(8):
        deltas, visits = defaultdict(float), Counter()
        for row in rows:
            decisions = []
            solved, finish, _ = rollout(row, policy, trace=decisions)
            # Common prefix cancels except for the number of prior calls.
            # The local surrogate credits outcome and finishing time, with
            # the exact full policy objective used for acceptance below.
            for observation, move, alternative in decisions:
                alt_solved, alt_finish, _ = rollout(row, policy, start=alternative)
                delta = int(alt_solved) - int(solved) + COST * (finish - alt_finish)
                key = observation, not move
                deltas[key] += delta
                visits[key] += 1
        accepted = False
        for (obs, move), estimate in sorted(deltas.items(), key=lambda item: (-item[1], item[0])):
            if estimate <= 0:
                break
            if visits[obs, move] < 5:
                continue
            candidate = {**policy, obs: move}
            paired, metrics = stats(rows, candidate)
            if any(a and not b for a, b in zip(initial, paired, strict=True)):
                continue
            if fitness(metrics) <= fitness(current):
                continue
            policy, current = candidate, metrics
            history.append({"observation": obs, "verify_scope": move,
                            "candidate_visits": visits[obs, move], "metrics": flatten(current)})
            accepted = True
            break
        if not accepted:
            break
    return policy, {"initial": flatten(base), "final": flatten(current), "updates": history}


def compare(rows, policy):
    initial, original = stats(rows, {})
    learned, trained = stats(rows, policy)
    _, no_scope = stats(rows, {}, no_scope=True)
    paired = Counter()
    for row, a, b in zip(rows, initial, learned, strict=True):
        tier = "agreement" if row[1][0] & row[1][1] else "impasse"
        paired[tier, str(a), str(b)] += 1
    return {"script": flatten(original), "learned": flatten(trained),
            "without_field": flatten(no_scope), "paired": flatten(paired)}


def study():
    policy, train = fit(panels((4, 5), TRAIN_SEED, 700, 2))
    heldout = panels((6, 7), TEST_SEED, 1200, 3)
    rng = random.Random(TEST_SEED + 1)
    lost = [(*row[:-1], tuple(mask if rng.random() >= .25 else 0 for mask in row[-1])) for row in heldout]
    return {"scope": "Synthetic fit, one field checked once per role, two slots to verify and publish.",
            "training": train,
            "policy": [[obs, val] for obs, val in sorted(policy.items())],
            "heldout": compare(heldout, policy), "unreturned_checks": compare(lost, policy)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output
    output.mkdir()
    locked = (Path(__file__), LOOKUP / "lookup.py", LOOKUP.parent / "train.py",
              LOOKUP.parents[1] / "environment.py")
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(output.resolve()),
        "sha256": {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest()
                   for p in locked},
    }
    (output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    result = study()
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"updates": len(result["training"]["updates"]),
                      "heldout": result["heldout"], "unreturned_checks": result["unreturned_checks"]}, indent=2))


if __name__ == "__main__":
    main()
