"""Evaluate the trained joint policy by scoring each public card completion."""
from hashlib import sha256
from itertools import product
import json

import torch

import relay_compromise_joint as joint
import relay_compromise_language as language
from relay_compromise_audit import oracle
from relay_compromise_language_audit import view
from relay_compromise_public import observations as narrowed_observations

FIT = joint.KIT / "relay-compromise-joint" / "coverage.json"
PROMPTS = joint.SOURCE / "actions.jsonl"


def visible(row):
    _, relay, far, *options = row["messages"][-1]["content"].splitlines()
    menu = tuple(x.split(". ", 1)[1] for x in options)
    _, left = view(relay, menu[:-2])
    _, right = view(far, menu[:-2])
    return menu, tuple(product(left, right))


def label_sets(predictions, width):
    return set.intersection(*(set(p[:width]) for p in predictions))


def check(raw, table, ranker):
    full = {}
    with torch.no_grad():
        for key, r in raw.items():
            name, _, left, right, _ = key
            if not left or not right:
                continue
            menu, (cards,) = visible(r)
            f, frozen, stored_menu = table[key]
            assert stored_menu == menu
            scores = ranker(f, frozen)
            choices = sorted(menu, key=lambda a: float(scores[menu.index(a)]), reverse=True)
            full[name, cards] = choices
    rows = []
    for r in [*raw.values(), *narrowed_observations()]:
        label, _, left, right, _ = r["observation"]
        family, _, condition = label.partition("/")
        if family not in language.OFFSETS:
            continue
        menu, cards = visible(r)
        predicted = [full[family, c] for c in cards]
        all_gold = [oracle(menu[:-2], *c) for c in cards]
        expected = set.intersection(*all_gold) or {"unresolved"}

        def rank_across_cards(action):
            positions = [row.index(action) for row in predicted]
            return max(positions), sum(positions), menu.index(action)

        options = {}
        for k in (1, 2):
            # "Unresolved" is handled after intersecting the concrete choices.
            sets = label_sets(predicted, k) - {"unresolved"}
            options[f"top_{k}"] = min(sets, key=rank_across_cards, default="unresolved")
        rows.append({"family": family, "condition": condition or ("complete" if left and right else "incomplete"),
                     "visible_cards": [left, right], "completion_count": len(cards),
                     "package_order": menu[:-2],
                     "warranted_choices": sorted(expected), "answers": options,
                     "correct": {k: a in expected for k, a in options.items()},
                     "witnesses": [{"cards": c, "allowed": sorted(g), "ranked": p}
                                   for c, g, p in zip(cards, all_gold, predicted, strict=True)]})
    return rows


def collision():
    known = (3, 3, 3)
    normal = ((1, 1, 1), (1, 2, 2))
    crossed = ((1, 1, 2), (1, 2, 1))
    def ranges(domain):
        return [(min(p), max(p)) for p in zip(*domain, strict=True)]
    assert ranges(normal) == ranges(crossed)
    both_valid = set.intersection(*(oracle("ABC", known, c) for c in normal))
    none_valid = set.intersection(*(oracle("ABC", known, c) for c in crossed))
    assert both_valid == {"B", "C"} and not none_valid
    return {"visible": known, "identical_ranges": ranges(normal),
            "domains": [{"cards": normal, "choices": sorted(both_valid)},
                        {"cards": crossed, "choices": ["unresolved"]}]}


def run():
    torch.set_num_threads(1)
    payload = json.loads(FIT.read_text())
    assert payload["inputs_sha256"] == sha256(PROMPTS.read_bytes()).hexdigest()
    policy = joint.Joint(True)
    weights = payload["training"]["qwen_joint"]["state"]
    policy.load_state_dict({k: torch.tensor(v) for k, v in weights.items()})
    with language.inputs():
        raw = language.scorer.read(joint.SOURCE)
    return {"fit_sha256": sha256(FIT.read_bytes()).hexdigest(),
            "rows": check(raw, joint.unpack(), policy.rank),
            "marginal_range_collision": collision()}


if __name__ == "__main__":
    print(json.dumps(run(), separators=(",", ":")))
