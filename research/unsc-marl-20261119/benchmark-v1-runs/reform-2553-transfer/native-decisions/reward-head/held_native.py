"""Collect the held native Resolution 2422 decisions at one-card capacity."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import reward_head as head

HERE, native, READ, prior = head.HERE, head.native, head.READ, head.prior
trib = head.old.tribunals
CASE = trib.CASE
RATES = (.55, .95)
SHARES = (.25, .75)
OUT = HERE / "evidence"


def setup():
    (_, counts, caps, raw, edges, point), = [row for row in head.old.un_cases() if row[0] == "tribunals"]
    assert counts == (2, 2, 2) and caps == (1, 1, 1)
    order = list(trib.CARDS)
    menus = [[value[1] for value in row.values()] for row in trib.CARDS.values()]
    choice = head.old.options(counts, caps)
    true = {ids: [point([choice[i][a] for i, a in enumerate(ids)], mask) for mask in range(8)]
            for ids in product(range(2), repeat=3)}
    return order, menus, raw, edges, true


def requests():
    roles, menus, local, edges, _ = setup()
    for share, rate in product(SHARES, RATES):
        shared = {"resolution": "S/RES/2422 (2018)", "roles": {"early": roles[1], "later": roles[0], "independent": roles[2]},
                  "early_card_prior": {"1": share, "2": 1. - share}, "receipt_probability_per_desk": rate,
                  "standalone_points": {role: {str(j+1): pts for j, pts in enumerate(weights)}
                                        for role, weights in zip(roles, local, strict=True)},
                  "joint_requirements": [{"cards": [f"{roles[i]} card {a+1}", f"{roles[j]} card {b+1}"], "extra": pts}
                                         for i, a, j, b, pts in edges]}
        observed = {
            "absent": {"early_receipt": "did not arrive"},
            "card1": {"early_receipt": "arrived", "card": "1", "owner": roles[1], "text": menus[1][0]},
            "card2": {"early_receipt": "arrived", "card": "2", "owner": roles[1], "text": menus[1][1]},
            "arrived": {"early_receipt": "arrived", "card": "not shown"},
            "none": {"early_receipt": "no observation"},
        }
        for view, mapping in product((*native.VIEWS, "independent"), native.LABELS):
            desk = 2 if view == "independent" else 0
            payload = {**shared, "your_desk": roles[desk], "your_menu": {str(i+1): text for i, text in enumerate(menus[desk])},
                       "your_view": observed["none" if view == "independent" else view],
                       "letter_to_your_card": native.LABELS[mapping]}
            yield {"id": f"{share}/{rate}/{view}/{mapping}", "max_output_tokens": 2,
                   "messages": [{"role": "system", "content": native.SYSTEM},
                                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def plan():
    pins = (Path(__file__), HERE / "protocol.md", HERE / "fit.json", Path(head.__file__), Path(native.__file__),
            Path(trib.__file__), Path(head.old.__file__), prior.RELEASE / "release.json",
            head.PARTNER.parent / "private-results.json")
    rows = list(requests())
    assert len(rows) == 48
    return {"requests": rows, "case": CASE["id"], "official_meeting": "S/PV.8295",
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in pins}}


def reuse(call):
    with patch.object(native, "HERE", HERE), patch.object(native, "OUT", OUT), patch.object(
            native, "CASE", CASE), patch.object(native, "plan", plan):
        return call()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        reuse(native.run)
    else:
        native.frozen.emit(plan() if mode == "plan" else reuse(native.verify))
