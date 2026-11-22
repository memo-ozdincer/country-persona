"""Execute one selected prospective policy contrast through an authorized reply."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import warrant_safety_transfer as study

safe, world, base, score = study.safe, study.world, study.base, study.score
EVIDENCE = study.EVIDENCE / "reply-audit"
ARCHIVE = study.EVIDENCE / "results.json"
FAMILY = "warrant-safety-transfer-reply"


def select():
    rng = np.random.default_rng(study.HISTORY_SEED)
    for domain in json.loads(ARCHIVE.read_text())["domains"]:
        cards = np.asarray(domain["cards"])
        table = np.asarray(domain["observed_slots"])
        task = world.Workshop(cards)
        for label in ("uniform", "correlated"):
            draws = rng.random((safe.HISTORIES, safe.PREFIXES[-1]))
            if not domain["valid_for_stable_model"]:
                continue
            p = world.prior(label == "correlated")
            _, occurrence = score.actual_values(task, p, table)
            planner = safe.Planner(task, p)
            histories = np.searchsorted(np.cumsum(occurrence), draws, side="right")
            for h, history in enumerate(histories):
                support = planner.table_support(history)
                for state in np.flatnonzero(occurrence):
                    q, lower = planner.decision(int(state), support)
                    if lower <= 0.:
                        continue
                    slots = table[np.arange(3), world.TYPES]
                    opened = slots @ np.array([9, 3, 1])
                    idx, link = np.argwhere(task.state[np.arange(64), opened] == state)[0]
                    facts = [(i, int(s), int(task.world[idx, i, s])) for i, s in enumerate(slots[idx]) if world.LINKS[link, i]]
                    return {"domain": domain["domain"], "prior": label, "history_index": h, "receipt_state": int(state),
                            "lower_expected_gain": lower, "choices": {"grade_only": int(planner.baseline[state]), "conservative": q},
                            "opening_facts": facts, "private": task.world[idx].tolist(), "possible_cards": cards.tolist(),
                            "opening_link_survival": world.LINKS[link].tolist(),
                            "surviving_local_tables": list(map(len, support))}
            planner.decision.cache_clear()
    return None


def requests():
    branch = select()
    if branch:
        for key, q in branch["choices"].items():
            if q:
                role, slot = world.ACTIONS[q]
                fact = role, slot, branch["private"][role][slot]
                yield base.authorized.note(key, fact, branch["private"])


def certify(case, evidence):
    task = world.Workshop(np.asarray(case["possible_cards"]))
    support = world.ALL
    for fact in evidence:
        support &= task.bit_reports[tuple(fact)]
    assert support
    labels = [label for j, label in enumerate((*score.PACKAGES, "IMPASSE")) if support & ~task.winner_masks[j] == 0]
    count = support.bit_count()
    compatible = [pair for pair in task.world if all(pair[role, slot] == grade for role, slot, grade in evidence)]
    checked = []
    for pair in compatible:
        ranked = {name: (min(grades), sum(grades))
                  for name, grades in zip(score.PACKAGES, pair.T, strict=True) if all(grades)}
        checked.append({name for name, ranking in ranked.items() if ranking == max(ranked.values())} or {"IMPASSE"})
    assert count == len(compatible) and set(labels) == set.intersection(*checked)
    reports = [base.phrases.wire(*f) for f in evidence]
    if labels == ["IMPASSE"]:
        reason = "Each compatible world excludes every package. The workshop records an impasse."
    elif labels:
        reason = f"{labels[0]} has the best or tied-best rank in every compatible world. The workshop recommends {labels[0]}."
    else:
        reason = "The compatible worlds have no shared decision. The workshop leaves the decision unresolved."
    memo = " ".join(["Fictional workshop record.", *reports,
                    f"Compatible grade-card combinations total {count}.", reason])
    return {"compatible_worlds": count, "permitted_decisions": labels or ["UNRESOLVED"],
            "admitted_reports": reports, "memo": memo}


def result(rows):
    branch = select()
    assert branch
    arms = {}
    for key, q in branch["choices"].items():
        evidence = list(branch["opening_facts"])
        if q:
            role, slot = world.ACTIONS[q]
            fact = role, slot, branch["private"][role][slot]
            note = rows[key]
            accepted = note["ended"] and note["output"] == base.phrases.wire(*fact)
            if accepted:
                evidence.append(fact)
            raw = note["output"]
        else:
            accepted, raw = False, None
        arms[key] = {"query": q, "reply": raw, "accepted": accepted, "expected_request_fee_in_replay": world.two.REPLY_COST if q else 0.,
                     "final_workshop_certificate": certify(branch, evidence)}
    return {"selected_example": branch, "arms": arms}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    files = (Path(__file__).resolve(), ARCHIVE, EVIDENCE / "protocol.md")
    return {**study.pins(), **{str(p.relative_to(study.HERE)): base.phrases.runner.digest(p) for p in files}}


def verify(folder):
    with patch.multiple(study.replay, requests=requests, pins=pins, FAMILY=FAMILY):
        return study.replay.verify(folder)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "describe", "score"))
    cli.add_argument("folder", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "describe":
        print(json.dumps(select(), indent=2))
    elif args.mode == "run":
        assert list(requests())
        with patch.multiple(base.phrases.runner, episode=episode, locks=pins):
            base.phrases.runner.run(args.model, args.folder)
    else:
        print(json.dumps(result(verify(args.folder)), indent=2))
