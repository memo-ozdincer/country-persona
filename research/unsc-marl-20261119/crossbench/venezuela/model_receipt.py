"""Transfer the frozen compound mandate decoder to the Venezuela workshop."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import noisy_frontier as frontier
import workshop_transfer as transfer

runtime = transfer.episode.canonical.transfer.study.probe
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCK = HERE / "model-receipt-lock.json"
LABELS = "ABCDEFGHIJKLMNOP"
FIELDS = {
    "scope": {
        "focused": "Keep the findings confidential in both cycles.",
        "focused-staged": "Keep first-cycle findings confidential. Second-cycle public reporting is optional.",
        "staged-broad": "Make aggregate findings public by the second cycle. First-cycle publication is also acceptable.",
        "all": "Any publication timing is acceptable.",
    },
    "coordination": {
        "un-joint": "Allow UN-led or joint coordination.",
        "host-joint": "Allow host-led or joint coordination.",
    },
    "consent": {
        "required": "Explicit host consent is required.",
        "optional": "Explicit host consent is optional.",
    },
}
SCOPE_ALLOW = {"focused": {"focused"}, "focused-staged": {"focused", "staged"},
               "staged-broad": {"staged", "broad"}, "all": {"focused", "staged", "broad"}}
COORDINATION = {"un-joint": {"un", "joint"}, "host-joint": {"host", "joint"}}
ANCHORS = {"us": ("staged-broad", "un-joint", "optional"),
           "ru-overlap": ("focused-staged", "host-joint", "required"),
           "ru-impasse": ("focused", "host-joint", "required")}


def suite():
    profiles = list(product(*(tuple(values) for values in FIELDS.values())))
    assert len(profiles) == len(LABELS)
    for role, card in transfer.load(HERE/"case.json")["cards"].items():
        for order, ordering in enumerate((profiles, profiles[::-1])):
            payload = {"private_mandate": card, "field_definitions": FIELDS,
                       "answer_profiles": {label: dict(zip(FIELDS, p, strict=True))
                                           for label, p in zip(LABELS, ordering, strict=True)}}
            yield {"id": f"{role}/{order}", "labels": LABELS, "profiles": ordering, "messages": [
                {"role": "system", "content": "Read the fictional private mandate. Identify its requirements for when aggregate findings become public, who coordinates the needs assessment, and whether explicit host consent is required. Choose the single answer profile whose three definitions all match. Respond with only its letter."},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ]}


def projected(fields, option):
    scope, coord, consent = fields
    values = (
        None if scope is None else option["scope"] in SCOPE_ALLOW[scope],
        None if coord is None else option["coordination"] in COORDINATION[coord],
        None if consent is None else consent == "optional" or option["explicit_consent"],
    )
    return False if False in values else None if None in values else True


def reading(layouts, mode):
    # The pinned Mali decoder applies this same field-marginal pooling rule.
    from math import exp, fsum, log

    if mode == "pooled":
        result = []
        for i, choices in enumerate(FIELDS.values()):
            margins = {value: sum(log(fsum(exp(score-max(layout.values()))
                                          for profile, score in layout.items() if profile[i] == value))
                                  for layout in layouts) for value in choices}
            best = [value for value, score in margins.items() if score == max(margins.values())]
            result.append(best[0] if len(best) == 1 else None)
        return tuple(result)
    selected = layouts if mode == "stable" else [layouts[int(mode)]]
    candidates = [p for m in selected for p, score in m.items() if score == max(m.values())]
    return tuple(v[0] if len(set(v)) == 1 else None for v in zip(*candidates, strict=True))


def input_rows(projections, excludes, initial):
    spec = transfer.load(HERE/"case.json")
    for key, item, _, labels, roles, menus, terms in transfer.cases():
        cards = ("us", key[1]) if key[0] == "original" else (key[1], "us")
        row, tape = item
        signed = [{1 << i: projections[card][label] for i, label in enumerate(labels)}
                  for card in cards]
        # The authored gate can only remove unsupported model claims. It
        # never fills fields or package signs the model failed to establish.
        trusted = [
            {bit: sign if sign is (label in menu) else None
             for (bit, sign), label in zip(role_signs.items(), labels, strict=True)}
            for role_signs, menu in zip(signed, menus, strict=True)
        ]
        scopes = tuple(sum(1<<i for i, label in enumerate(labels)
                           if label in excludes[card] and label not in menu)
                       for card, menu in zip(cards, menus, strict=True))
        known = row[2]
        if initial == "modeled":
            known = tuple(tuple(sum(1<<i for i, label in enumerate(labels)
                                    if label not in spec["later_only"][card] and signs[1<<i] is positive)
                                for positive in (True, False))
                          for card, signs in zip(cards, trusted, strict=True))
        yield key, ((row[0], row[1], known, row[3], scopes), tape), trusted, terms


def policies(rows):
    counts = Counter()
    paths = {}
    episode = transfer.episode
    router = transfer.router
    selection = frontier.selection
    for key, item, receipt, terms in rows:
        label = "agreement" if key[1] == "ru-overlap" else "impasse"
        with patch.object(selection.reuse, "singleton_enabled",
                          new=lambda: selection.enabled(True, frontier.ordinary_when_possible)):
            with transfer.canonical.enabled(terms, "public", lambda: episode.delay.enabled(
                    lambda _: "immediate")):
                for mode in frontier.BASELINES:
                    events = []
                    outcome = router.play(item, mode, {}, events=events, recorded=receipt)
                    counts[label,mode,"presentations"] += 1
                    for metric, value in zip(("solved","slots","checks","queries","answers","scope"),
                                             outcome, strict=True):
                        counts[label,mode,metric] += value
                    paths["/".join((*key,mode))] = {"counts": outcome, "events": events}
    return {"counts": router.sp.flatten(counts), "paths": paths}


def score(rows):
    maps = {}
    case = transfer.load(HERE/"case.json")
    for plan in suite():
        role, _ = plan["id"].split("/")
        maps.setdefault(role, []).append(dict(zip(plan["profiles"], rows[plan["id"]]["label_logits"], strict=True)))
    outcomes, totals = {}, Counter()
    for mode in ("0", "1", "stable", "pooled", "authored"):
        counts, fields, signs, excluded = Counter(), {}, {}, {}
        for card, options in transfer.EXPECTED.items():
            fields[card] = ANCHORS[card] if mode == "authored" else reading(maps[card], mode)
            signs[card] = {opt["id"]: projected(fields[card], opt) for opt in case["options"]}
            excluded[card] = [o["id"] for o in case["options"] if fields[card][0] is not None and
                              o["scope"] not in SCOPE_ALLOW[fields[card][0]]]
            for found, wanted in zip(fields[card], ANCHORS[card], strict=True):
                counts["field", "unknown" if found is None else "correct" if found == wanted else "wrong"] += 1
            for name, sign in signs[card].items():
                counts["package", "unknown" if sign is None else "correct" if sign is (name in options) else "wrong"] += 1
            assert all(not sign or name in options for name, sign in signs[card].items()) or mode != "authored"
        outcomes[mode] = {
            "fields": fields, "signs_before_admission": signs, "scope_before_admission": excluded,
            "counts": transfer.router.sp.flatten(counts),
            "routing": {initial: policies(input_rows(signs, excluded, initial))
                        for initial in ("authored", "modeled")},
        }
        totals.update({f"{mode}/{k}": v for k, v in outcomes[mode]["counts"].items()})
    return {"totals": dict(totals), "conditions": outcomes}


def hashes():
    files = list(HERE.parent.rglob("*.py")) + [HERE/"case.json"]
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


if __name__ == "__main__":
    with patch.multiple(runtime, LOCK=LOCK, LABELS=LABELS, suite=suite, score=score, hashes=hashes):
        runtime.main()
