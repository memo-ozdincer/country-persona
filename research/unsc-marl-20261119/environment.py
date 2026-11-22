"""Two-delegate, two-round UN-inspired workshop with simulated private mandates."""
from collections import Counter
from itertools import product
import json
from pathlib import Path
import random

FAMILIES_PATH = Path(__file__).with_name("families.json")
FAMILIES = json.loads(FAMILIES_PATH.read_text())
HOLD = -1
ABSENT = -2


def world(family, option_order, mandates):
    """Apply public option permutation before revealing private instructions."""
    return {
        "family": family,
        "options": list(option_order),
        "mandates": [[int(index in mandate) for index in option_order] for mandate in mandates],
    }


def sample_worlds(families, count, seed):
    rng = random.Random(seed)
    worlds = []
    for index in range(count):
        family = families[index % len(families)]
        order = list(range(len(FAMILIES[family]["options"])))
        rng.shuffle(order)
        # Stratify to expose both error directions. Sampling never uses national vote labels.
        deadlock = (index // len(families)) % 4 == 0
        while True:
            mandates = [{j for j in order if rng.random() < 0.5} for _ in range(2)]
            if all(mandates) and (not mandates[0] & mandates[1]) == deadlock:
                worlds.append(world(family, order, mandates))
                break
    return worlds


def overlap(case):
    return tuple(i for i, (left, right) in enumerate(zip(*case["mandates"])) if left and right)


def allowed(case, choices):
    return all(choice == HOLD or case["mandates"][role][choice] for role, choice in enumerate(choices))


def outcome(case, signals, ballots):
    feasible = overlap(case)
    invalid_signal = not allowed(case, signals)
    invalid_ballot = not allowed(case, ballots)
    both_hold = tuple(ballots) == (HOLD, HOLD)
    agreement = ballots[0] == ballots[1] and ballots[0] in feasible
    valid_deadlock = both_hold and not feasible
    strict = (agreement or valid_deadlock) and not (invalid_signal or invalid_ballot)
    return {
        "reward": -1 if invalid_signal or invalid_ballot else int(strict),
        "strict": strict,
        "feasible": bool(feasible),
        "agreement": agreement,
        "valid_deadlock": valid_deadlock,
        "false_hold": both_hold and bool(feasible),
        "unsupported_signal": invalid_signal,
        "unsupported_ballot": invalid_ballot,
    }


def audit():
    """Independent oracle based on sets, exhaustively checked across 3/4 options."""
    counts = Counter()
    for n in (3, 4):
        actions = [HOLD, *range(n)]
        menus = [{i for i, bit in enumerate(bits) if bit} for bits in product((0, 1), repeat=n)]
        for first, second in product(menus, repeat=2):
            case = world("audit", range(n), (first, second))
            feasible = first & second
            for signal_a, signal_b, vote_a, vote_b in product(actions, repeat=4):
                signals, votes = (signal_a, signal_b), (vote_a, vote_b)
                invalid = ({signal_a, vote_a} - {HOLD} - first) or ({signal_b, vote_b} - {HOLD} - second)
                correct = (vote_a == vote_b and vote_a in feasible) or (vote_a == vote_b == HOLD and not feasible)
                expected = -1 if invalid else int(correct)
                assert outcome(case, signals, votes)["reward"] == expected
                counts[n] += 1
    return dict(counts)


def text_view(case, role, phase, peer=ABSENT, own=ABSENT):
    family = FAMILIES[case["family"]]
    labels = "ABCD"
    options = "\n".join(f"{labels[i]}. {family['options'][j]}" for i, j in enumerate(case["options"]))
    approved = ", ".join(labels[i] for i, bit in enumerate(case["mandates"][role]) if bit)
    intro = (
        f"Simulated Security Council drafting workshop based on {family['meeting']}. "
        f"{family['public_context']} Public options for this fictional workshop:\n{options}\n"
        f"You represent {family['roles'][role]}, delegate {role + 1} of 2. "
        f"Your private simulated instructions allow only {approved}. "
        "Actual historical votes and commitments are outside this simulation. "
        "Both delegates must select the same allowed option for agreement. H means hold. "
    )
    if phase == "proposal":
        return intro + "Send one option that you can support, or H. Return only its letter."
    label = lambda code: "none" if code == ABSENT else "H" if code == HOLD else labels[code]
    return intro + (
        f"Your preliminary proposal was {label(own)}. The other delegate sent {label(peer)}. "
        "Both now choose independently. Select an option you can support if you expect both can select it. "
        "Choose H if no joint option can responsibly be selected. Return only the letter."
    )
