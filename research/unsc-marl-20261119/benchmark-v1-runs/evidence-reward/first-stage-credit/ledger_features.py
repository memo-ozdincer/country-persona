"""Read directly observed public commitments for the first-stage fitted policy."""
from itertools import permutations
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "source-bound-chair"))
import signed_coverage as signed

E, ROLES = signed.e, signed.ROLES
NAMES = ("bias", "has_proof", "target_unresolved", "unresolved_fraction",
         "other_accepts_target", "delivery", "is_affirmative")


def features(log, role, target, delivery, yes):
    ledger = signed.chair.readout("ABCD", ROLES, log)
    state = ledger["state"]
    assert state != "CONTRADICTORY_DISCLOSURE"
    other = ROLES[1 - ROLES.index(role)]
    unresolved = ledger["unresolved_options"]
    return (1., float(state in ("AGREEMENT_POSSIBLE", "IMPASSE")), float(target in unresolved),
            len(unresolved)/4, float(any(row["role"] == other and target in row.get("accepts", ())
                                        for row in log)), delivery, float(yes))


def relabel(log, roles, choices):
    output = []
    for row in log:
        transformed = {**row, "role": roles[row["role"]]}
        for name in ("accepts", "excludes"):
            if name in row:
                transformed[name] = [choices[label] for label in row[name]]
        output.append(transformed)
    return output


def build():
    import json

    source = E.read(signed.SIGNED/"roster.json")
    output = {}
    permutations_checked = 0
    for split, rows in source.items():
        output[split] = {}
        for item in rows:
            payload = json.loads(item["messages"][1]["content"])
            log = signed.initial(payload["public_claims"])
            args = (log, payload["you"], item["target"], item["delivery"], item["truth"])
            expected = features(*args)
            if split == "held":
                for labels in permutations("ABCD"):
                    lookup = dict(zip("ABCD", labels, strict=True))
                    for order in permutations(ROLES):
                        swap = dict(zip(ROLES, order, strict=True))
                        variant = relabel(log, swap, lookup)
                        assert features(variant, swap[args[1]], lookup[args[2]], *args[3:]) == expected
                        permutations_checked += 1
            output[split][item["id"]] = expected
    return {"features": output, "columns": NAMES, "held_role_menu_relabelings": permutations_checked}


if __name__ == "__main__":
    E.emit(build())
