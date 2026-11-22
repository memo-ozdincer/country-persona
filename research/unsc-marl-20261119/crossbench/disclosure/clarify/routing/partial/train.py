"""Counterfactual policy iteration over decentralized partially known menus."""
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
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from environment import options_for, presentations, record, terminal
from guard import guarded
from joint import restore as restore_full
from learn import COST

TRAIN_WIDTHS = (3, 4)
TEST_WIDTHS = (5, 6)
TRAIN_SEED = 31207
TEST_SEED = 92604
MAX_UPDATES = 16


def examples(widths, seed, stress=False):
    """Generate one fixed missing-sign pattern per legal opening presentation."""
    rng = random.Random(seed)
    for width in widths:
        full = (1 << width)-1
        for gold, opening in presentations(width):
            observations = []
            for private in gold:
                # A missing sign is absent from both masks. The two delegates
                # never see each other's masks, including missingness.
                removed = sum(1 << i for i in rng.sample(range(width), 1 + int(stress)))
                available = full & ~removed
                observations.append((private & available, ~private & available))
            yield width, gold, tuple(observations), opening


def opened(opening, local):
    return opening[0] & local[0][0], 0, opening[2] & local[1][0], 0


def groups(known, state, role, full):
    yes, no = known
    return tuple(pool & (yes | no) for pool in options_for(yes, state, role, full))


def pick(pool):
    return pool & -pool


def moves(known, state, role, full):
    choices = {}
    buckets = groups(known, state, role, full)
    yes, no = known
    for group, entries in enumerate(buckets):
        if not entries:
            continue
        bit = pick(entries)
        accept = bool(yes & bit)
        updated = record(state, role, bit, accept)
        # The recipient can confirm a positive proposal immediately. A
        # matching proposal already terminates the session before routing.
        for stay in ((False,) if accept else (False, True)):
            choices[group, stay] = bit, accept, updated, role if stay else 1-role
    if not choices:
        choices[(-1, False)] = 0, False, state, 1-role
    return buckets, choices


def default_action(known, state, full, buckets, choices):
    yes, no = known
    group = next((g for g in (0, 3, 1, 2) if buckets[g]), -1)
    if group not in (1, 3):
        return group, False
    _, _, after, _ = choices[group, False]
    blocked = after[1] | after[3]
    return group, bool(no & ~blocked & full)


def position(local, state, role, turn, width):
    full = (1 << width)-1
    known = local[role]
    buckets, choices = moves(known, state, role, full)
    baseline = default_action(known, state, full, buckets, choices)
    open_count = (full & ~(state[1] | state[3])).bit_count()
    own_yes, own_no = known
    # Bucket counts retain exactly the distinctions available to the actor.
    # In particular, missing peer signs are never represented as exclusions.
    key = (
        turn == 0,
        min(width-turn, 3),
        width-turn-open_count,
        min(own_yes.bit_count(), 2),
        tuple(min(pool.bit_count(), 2) for pool in buckets),
        tuple(action for action in choices),
        baseline,
    )
    return key, choices, baseline


def finish(width, local, start, role, turn, policy):
    full = (1 << width)-1
    for k in range(turn, width):
        if terminal(start, full):
            return True, k-turn
        key, choices, baseline = position(local, start, role, k, width)
        _, _, start, role = choices[policy.get(key, baseline)]
    return terminal(start, full), width-turn


def replay(row, policy):
    width, _, local, opening = row
    return finish(width, local, opened(opening, local), 1, 0, policy)


def full_policy(row, actor):
    width, _, local, opening = row
    full = (1 << width)-1
    state = opened(opening, local)
    role = 1
    believed_yes = tuple(pair[0] for pair in local)
    for turn in range(width):
        if terminal(state, full):
            return True, turn
        _, actions, action = actor(believed_yes, state, role, turn, full)
        selected = actions[action] if actions else (0, state, 1-role)
        bit, _, next_role = selected
        if not (bit & (local[role][0] | local[role][1])):
            _, choices, baseline = position(local, state, role, turn, width)
            _, _, state, role = choices[baseline]
            continue
        accept = bool(bit & local[role][0])
        state = record(state, role, bit, accept)
        role = 1-role if accept else next_role
    return terminal(state, full), width


def label(row):
    return "agreement" if row[1][0] & row[1][1] else "impasse"


def evidence_available(row):
    width, _, (left, right), opening = row
    full = (1 << width)-1
    if left[0] & right[0]:
        return True
    return (left[1] | right[1]) == full and bool(right[1])


def measure(worlds, run):
    counts = Counter()
    trace = []
    for row in worlds:
        outcome = label(row)
        result, slots = run(row)
        enough = evidence_available(row)
        assert not result or enough
        counts[outcome,"presentations"] += 1
        counts[outcome,"evidence_ceiling"] += enough
        counts[outcome,"certificates"] += result
        counts[outcome,"slots"] += slots
        if result:
            assert outcome == "agreement" or slots == row[0]
        trace.append(result)
    return counts, trace


def counterfactual(worlds, policy):
    effect = defaultdict(Counter)
    for width, gold, local, opening in worlds:
        state, role, full = opened(opening, local), 1, (1 << width)-1
        for turn in range(width):
            if terminal(state, full):
                break
            key, choices, default = position(local, state, role, turn, width)
            selected = policy.get(key, default)
            _, _, after, next_role = choices[selected]
            cert, slots = finish(width, local, after, next_role, turn+1, policy)
            for candidate, (_, _, alternate, recipient) in choices.items():
                if candidate == selected:
                    continue
                new_cert, new_slots = finish(width, local, alternate, recipient, turn+1, policy)
                tally = effect[key, candidate]
                tally["visits"] += 1
                tally["gained"] += new_cert and not cert
                tally["lost"] += cert and not new_cert
                tally["slots_saved"] += slots-new_slots
            state, role = after, next_role
    return effect


def useful(stats, class_):
    return stats[class_,"certificates"] - COST*stats[class_,"slots"]


def flat(stats):
    return {"/".join(key):value for key,value in sorted(stats.items())}


def fit(worlds):
    policy = {}
    initial, _ = measure(worlds, lambda r: replay(r, policy))
    current = initial
    journal = []
    for _ in range(MAX_UPDATES):
        effects = counterfactual(worlds, policy)
        ranked = sorted((
            -(v["gained"]-v["lost"]+COST*v["slots_saved"]), k
        ) for k,v in effects.items() if v["visits"] >= 3)
        accepted = False
        for loss, (key, candidate) in ranked:
            if loss >= 0:
                break
            trial = dict(policy)
            if candidate == key[-1]:
                trial.pop(key, None)
            else:
                trial[key] = candidate
            summary, _ = measure(worlds, lambda r: replay(r,trial))
            classes = ("agreement","impasse")
            if any(summary[c,"certificates"] < current[c,"certificates"] for c in classes):
                continue
            if sum(useful(summary,c)-useful(current,c) for c in classes) <= 0:
                continue
            policy, current = trial, summary
            journal.append({"observation":key,"action":candidate,
                            "counterfactual":dict(effects[key,candidate]),"metrics":flat(summary)})
            accepted = True
            break
        if not accepted:
            break
    return policy, {"initial":flat(initial),"final":flat(current),"updates":journal}


def freeze(policy):
    return [[key, value] for key,value in sorted(policy.items())]


def restore(raw):
    return {tuple(k[:4])+(tuple(k[4]),tuple(map(tuple,k[5])),tuple(k[6])):tuple(v) for k,v in raw}


def compare(rows, policy, old):
    methods = {
        "exclusion_script":lambda r:replay(r,{}),
        "original_learned":lambda r:full_policy(r,old),
        "partial_learned":lambda r:replay(r,policy),
    }
    scores = {k:measure(rows,v) for k,v in methods.items()}
    baseline = scores["exclusion_script"][1]
    transitions = Counter()
    for mode, (_, audit) in scores.items():
        for row,a,b in zip(rows,baseline,audit,strict=True):
            transitions[mode,label(row),str(a),str(b)] += 1
    return {"metrics":{arm:flat(v[0]) for arm,v in scores.items()},"paired_vs_script":flat(transitions)}


def dump(output,name,data):
    (output/name).write_text(json.dumps(data,indent=2)+"\n")


def main(output):
    output.mkdir()
    policy_source = ROOT/"evidence/joint/policy.json"
    deps = [Path(__file__).resolve(), policy_source, *(ROOT/n for n in ("environment.py","guard.py","joint.py","learn.py"))]
    dump(output,"launch.json",{
        "host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
        "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
        "sha256":{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in deps},
        "train_widths":TRAIN_WIDTHS,"test_widths":TEST_WIDTHS,"train_seed":TRAIN_SEED,"test_seed":TEST_SEED,
        "max_updates":MAX_UPDATES,"slot_cost":COST,
    })
    partial, training = fit(list(examples(TRAIN_WIDTHS,TRAIN_SEED)))
    dump(output,"training.json",training)
    dump(output,"policy.json",freeze(partial))
    print(f"Accepted updates: {len(training['updates'])}",flush=True)
    old = guarded(restore_full(json.loads(policy_source.read_text())))
    for n in TEST_WIDTHS:
        matches = list(examples((n,),TEST_SEED+n,stress=n==6))
        scored=compare(matches,partial,old)
        dump(output,f"heldout-{n}.json",scored)
        print(n,scored["metrics"],flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    main(p.parse_args().output)
