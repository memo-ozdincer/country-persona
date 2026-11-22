"""Measure the workshop evidence a signed reply can actually license."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import chair

HERE = Path(__file__).resolve().parent
SIGNED = HERE.parent / "language-signed-reply"
sys.path.insert(0, str(chair.ROOT / "benchmark"))
import evaluate as e

ROLES = ("Desk One", "Desk Two")
ACTION_INPUTS = {
    "native_frozen": ("native-adapter/credit-results.json", "frozen"),
    "native_direct_credit": ("native-adapter/credit-results.json", "adapted"),
    "native_reward": ("native-adapter/results.json", "adapted"),
    "feature_head": ("native-adapter/credit-results.json", "previous_feature_head"),
    "exact_decision_reply": ("native-adapter/credit-results.json", "exact"),
    "truthful_always_send": ("native-adapter/credit-results.json", "truthful_always_send"),
}
CLAIM = re.compile(r"(Desk One|Desk Two) (accepts|excludes) ([A-D])\.")


def claim(id_, role, flag, option):
    field = "accepts" if flag else "excludes"
    return {"id": id_, "role": role, field: [option]}


def initial(public_claims):
    output = []
    for i, text in enumerate(public_claims):
        role, sign, option = CLAIM.fullmatch(text).groups()
        output.append(claim(str(i), role, sign == "accepts", option))
    return output


def public_candidates(menu, log):
    candidates = [
        {field: value} for field in chair.FIELD_LABELS if field in menu[0]
        for value in sorted({row[field] for row in menu})
    ]
    compatible = [(item, set(chair.allowed(menu, item))) for item in candidates]
    return {
        role: [item for item, accepted in compatible if all(
            set(row.get("accepts", [])) <= accepted and not (
                set(row.get("excludes", [])) & accepted
            )
            for row in log if row["role"] == role
        )] for role in ROLES
    }


def run():
    cases = e.cases()
    roster_path = SIGNED / "roster.json"
    roster = e.read(roster_path)["held"]
    data = {file: e.read(SIGNED / file)["results"]["held"]["rows"]
            for file, _ in set(ACTION_INPUTS.values())}
    by_actor = {name: Counter() for name in ACTION_INPUTS}
    transitions = {}
    for stimulus in roster:
        key = stimulus["id"]
        case = cases[key.split("/")[0]]
        menu = case["options"]
        payload = json.loads(stimulus["messages"][1]["content"])
        log = initial(payload["public_claims"])
        old = public_candidates(menu, log)
        assert all(truth in old[role] for role, truth in zip(ROLES, case["membership"], strict=True))
        roles_known_before = sum(len(x) == 1 for x in old.values())
        record = {}
        for name, (file, arm) in ACTION_INPUTS.items():
            actor = data[file][key]["arms"][arm]
            selected = actor["selected"]
            # This is the same oracle role-local audit used in the archived
            # comparison. The public inference below sees the admitted sign.
            admitted = selected != "P" and actor["truthful"]
            enriched = log + [claim("reply", payload["you"], selected == "Y", stimulus["target"])] if admitted else log
            proof = chair.readout("ABCD", ROLES, enriched)
            terminal = bool(proof.get("verified_options")) or proof["state"] == "IMPASSE"
            candidates = public_candidates(menu, enriched)
            assert all(truth in candidates[role] for role, truth in zip(ROLES, case["membership"], strict=True))
            known_after = sum(len(x) == 1 for x in candidates.values())
            both_known = known_after == 2
            if both_known:
                shared = set(chair.allowed(menu, candidates[ROLES[0]][0])) & set(
                    chair.allowed(menu, candidates[ROLES[1]][0])
                )
                assert sorted(shared or {"I"}) == stimulus["gold"]
            r = {"signed_reply": selected, "admitted": admitted, "terminal": terminal,
                 "remaining_mandates": candidates, "newly_identifiable": known_after - roles_known_before}
            record[name] = r
            counts = by_actor[name]
            counts["presentations"] += 1
            counts["admitted_signs"] += admitted
            counts["decision_proof"] += terminal
            counts["proof_with_both_mandates_identifiable"] += terminal and both_known
            counts["proof_with_missing_mandate"] += terminal and not both_known
            counts["both_identifiable_without_explicit_proof"] += both_known and not terminal
            counts["presentations_with_identifiability_gain"] += known_after > roles_known_before
        transitions[key] = {"opening_candidates": old, "actors": record}
    paths = (roster_path, *(SIGNED / file for file in sorted(data)), HERE / "chair.py", Path(__file__))
    return {"counts": by_actor, "transitions": transitions, "sha256": {
        str(path.relative_to(chair.ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths
    }}


if __name__ == "__main__":
    e.emit(run())
