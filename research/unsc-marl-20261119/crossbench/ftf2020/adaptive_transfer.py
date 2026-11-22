"""Replay the frozen written-vote team on two other verified UN record rubrics."""
from collections import defaultdict
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, permutations, product
import json
from pathlib import Path

import adaptive_relay as relay

HERE = Path(__file__).resolve().parent
FROZEN = HERE / "adaptive-fit-results.json"


def read(path):
    return json.loads(path.read_text())


def named_sources():
    unami_path = HERE.parent / "unami2023/case.json"
    unifil_path = HERE.parent / "unifil-record.json"
    unami = read(unami_path)
    files = (FROZEN, unami_path, unifil_path, HERE.parent / "references.json",
             HERE.parent / "unifil-reserve.json", HERE / "accession.json",
             HERE / "task.json", HERE / "corroboration.py", HERE / "adaptive_relay.py",
             Path(__file__).resolve())
    iraq = read(files[3])["families"][unami["family"]]
    assert iraq["benchmark"]["unsc_bench_index"] == 256
    assert len(iraq["prediction_ref_only"]) == 15 and set(iraq["prediction_ref_only"].values()) == {"Y"}
    unifil = read(unifil_path)
    lebanon = read(files[4])
    assert lebanon["draft"] == "S/2023/641" and len(lebanon["reference_votes"]) == 15
    sources = {k: v.split(". ", 2)[-1] for deck in unami["roles"].values() for k, v in deck.items()}
    assert sources["SUPPORT"].startswith("At the Iraqi") and sources["SCOPE"].startswith("The review")
    unami_cards = {k: sources[k] for k in ("SUPPORT", "REVIEW", "CONSULT", "SCOPE")}
    unami_points = {k: frozenset({source}) for k, (source, _) in unami["rules"].items()}
    vote = unami["public"]["VOTE"].split(". ", 2)[-1]
    vote = vote.replace("The President announced adoption and the meeting ended. ", "")
    public = " ".join((vote, sources["TERM"], sources["REPORT"]))

    unifil_source = {item["id"]: item["text"] for item in unifil["evidence"]}
    # The fourth card is the existing public operative summary from the
    # earlier UNIFIL experiment, now treated as a simulated archive holding.
    unifil_cards = {k: unifil_source[k] for k in ("brazil", "china", "russia", "operative")}
    unifil_points = {k: frozenset(deps) for k, deps in {
        "procedure": ["vote"], "disposition": ["vote"], "duration": ["operative"],
        "permission": ["operative"], "coordination": ["operative"], "brazil-reason": ["brazil"],
        "china-reason": ["china"], "russia-reason": ["russia"], "overlap": ["brazil", "china"],
        "open-issue": ["brazil", "china"],
    }.items()}
    assert set(unifil_points) == {r["id"] for r in unifil["rubric"]}
    return {
        "unami": (unami_cards, {"VOTE", "TERM", "REPORT"}, unami_points, public, "", 106),
        "unifil": (unifil_cards, {"vote"}, unifil_points, unifil_source["vote"],
                   "Brazil and China both supported the mission. They differed on how adequately "
                   "the text addressed Lebanon's concerns.", 118),
    }, {str(f.relative_to(HERE.parent)): sha256(f.read_bytes()).hexdigest() for f in files}


def record_bank(spec):
    cards, base_ids, proof, public, comparison, cap = spec
    rows = {}
    for size in range(4):
        for names in combinations(cards, size):
            received = set(names)
            available = base_ids | received
            blocks = [cards[name] for name in names]
            if comparison and {"brazil", "china"} <= received:
                blocks.append(comparison)
            supplement = " ".join(blocks)
            completed = {rule: sorted(deps) for rule, deps in proof.items() if deps <= available}
            assert len(supplement.split()) <= cap, (names, cap)
            record = f"{public} {supplement}".strip()
            assert len(record.split()) <= 175, names
            rows[frozenset(names)] = {"text": record, "record_points": 7 * len(completed),
                                      "licensed_by": completed, "supplement_words": len(supplement.split())}
    return rows


def ftf_bank():
    case = relay.archive.load()
    return {frozenset(names): {"record_points": relay.assembly(
        case, [relay.KEYS.index(k) for k in names], [relay.archive.packet(relay.KEYS.index(k)) for k in names]
    )["final_record_score"]} for size in range(1, 4) for names in combinations(relay.KEYS, size)}


def immutable(value):
    return tuple(map(immutable, value)) if isinstance(value, list) else value


def outcomes(policy, target, anchor, prior, canonical=False):
    """Evaluate exact distribution over received sets and costs."""
    @lru_cache(None)
    def recurse(world, pending, history):
        if not pending or len(history) == 3:
            return {pending: (1., 0., 0.)}
        output = defaultdict(lambda: [0., 0., 0.])
        p = policy["requester", target, anchor, history]
        output[pending][0] += p[0]
        for contact, mass in enumerate(p[1:]):
            if mass == 0:
                continue
            admissible = tuple(i for i in pending if i in world[contact])
            fees = relay.QUESTION_COST + relay.LINK * relay.REPLY_COST * bool(admissible)
            if admissible:
                choice = ((1., 0.) if canonical else policy["responder", pending, world[contact]]) if len(admissible) == 2 else (1.,)
                observed = [(card, relay.RECEIPT * prob) for card, prob in zip(admissible, choice, strict=True)]
                observed.append((None, 1 - relay.RECEIPT))
            else:
                observed = [(None, 1.)]
            for card, chance in observed:
                if chance == 0:
                    continue
                then = tuple(i for i in pending if i != card)
                for terminal, (likelihood, cost, attempts) in recurse(world, then, history + ((contact, card),)).items():
                    row = output[terminal]
                    weight = mass * chance
                    row[0] += weight * likelihood
                    row[1] += weight * (cost + likelihood * fees)
                    row[2] += weight * (attempts + likelihood)
        return output

    marginal = defaultdict(lambda: [0., 0., 0.])
    initial = tuple(i for i in target if i != anchor)
    for world, mass in prior.items():
        for pending, values in recurse(world, initial, ()).items():
            for i, value in enumerate(values):
                marginal[pending][i] += mass * value
    assert abs(sum(row[0] for row in marginal.values()) - 1.) < 1e-9
    return marginal


def policy_compare(target, anchor, named, bank, measured):
    missing = frozenset(target) - {anchor}
    records = {}
    for size in range(3):
        for absent in combinations(sorted(missing), size):
            keys = frozenset(named[i] for i in target if i not in absent)
            records[frozenset(absent) | {anchor}] = {"final_record_score": bank[keys]["record_points"]}
    start = records[missing | {anchor}]["final_record_score"]

    def net(pending):
        return records[pending | {anchor}]["final_record_score"] - start

    result = {}
    for label, distribution in measured.items():
        result[label] = relay.metrics((
            distribution.get((), (0.,))[0],
            sum(row[1] for row in distribution.values()),
            sum(row[2] for row in distribution.values()),
            start + sum(row[0] * net(frozenset(pending)) for pending, row in distribution.items()),
        ))
    routes = product(range(2), repeat=3)
    _, fixed = max((relay.plan(relay.DESIGN, missing, 3, net, route) for route in routes), key=lambda item: item[0])
    expected, adaptive = relay.plan(relay.DESIGN, missing, 3, net)
    for label, tree in (("fixed_canonical", fixed), ("adaptive_canonical", adaptive)):
        result[label] = relay.metrics(relay.evaluate(tree, relay.DESIGN, missing, anchor, records))
    assert abs(result["adaptive_canonical"]["record_reward"] + 35 - start - expected) < 1e-9
    for row in result.values():
        row.pop("reward")
        row["net_gain_over_anchor"] = row.pop("record_reward") + 35 - start
    return result


def mean(rows):
    return {k: {metric: sum(row[k][metric] for row in rows) / len(rows) for metric in rows[0][k]}
            for k in rows[0]}


def run():
    fitted = read(FROZEN)
    original = {immutable(row["local_state"]): row["probabilities"] for row in fitted["policy"]}
    measured = {(target, anchor): {
        "frozen_joint": outcomes(original, target, anchor, relay.DESIGN),
        "frozen_canonical_reply": outcomes(original, target, anchor, relay.DESIGN, canonical=True),
    } for target, anchor in relay.SCENARIOS}

    def replay(ids, bank):
        return mean([policy_compare(target, anchor, ids, bank, measured[target, anchor])
                     for target, anchor in relay.SCENARIOS])

    reference = replay(relay.KEYS, ftf_bank())
    for observed, expected in (("frozen_joint", "joint_learned"),
                               ("frozen_canonical_reply", "learned_requester_canonical_responder"),
                               ("fixed_canonical", "exact_fixed_canonical"),
                               ("adaptive_canonical", "exact_adaptive_canonical")):
        for field in ("completion", "final_record_score", "cost", "attempts"):
            assert abs(reference[observed][field] - fitted["metrics"][expected]["design_mixture"][field]) < 1e-8
    dossiers, locks = named_sources()
    families = {}
    for family, deck in dossiers.items():
        bank = record_bank(deck)
        card_orders = [{"slots": order, "scores": replay(order, bank)} for order in permutations(deck[0])]
        families[family] = {
            "registry_order": card_orders[0],
            "alias_averaged": mean([row["scores"] for row in card_orders]),
            "frozen_minus_fixed_by_alias": [row["scores"]["frozen_joint"]["net_gain_over_anchor"] -
                                           row["scores"]["fixed_canonical"]["net_gain_over_anchor"] for row in card_orders],
            "alias_detail": card_orders,
            "bank": {",".join(sorted(k)): v for k, v in bank.items()},
        }
    return {"scope": "Frozen transport policy transfer. Two previously researched historical dockets were "
                     "excluded from the fitted policy. Recipient data and availability are synthetic. "
                     "The final scorer uses authored evidence-linked records rather than model prose. "
                     "Controls are replanned with the target rubric and the same synthetic roster prior.",
            "design": {"aliases_per_family": 24, "protected_anchor_targets_per_alias": 12,
                       "contacts": 3, "link_delivery": relay.LINK},
            "hashes": locks, "ftf_exact_replay": reference, "transfer": families}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
