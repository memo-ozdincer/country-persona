"""Verify known source excerpts before routing and again before delivery."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

from duplicate_card_semantic_review import EVIDENCE, FAULTS, STRESSES, exact_silent, read_all, reward_tables, simulate

CASE_DIR = Path(__file__).resolve().parent
SOURCE_CASES = {name: CASE_DIR / f"source-record-{name}-routing.json" for name in ("venezuela", "dprk")}


def hash_text(text):
    return sha256(text.encode("utf-8")).hexdigest()


def registries():
    canonical, reviewed = {}, {}
    provenance = {}
    for case, path in SOURCE_CASES.items():
        source = json.loads(path.read_text())
        provenance[case] = {}
        for role, (name, card) in enumerate(source["cards"].items(), 1):
            text = card["text"]
            first, rest = text.split(". ", maxsplit=1)
            alias = f"{rest} {first}."
            accepted = [hash_text(text), hash_text(alias)]
            assert len(set(accepted)) == 2
            canonical[case, accepted[0]] = role
            for digest in accepted:
                assert (case, digest) not in reviewed
                reviewed[case, digest] = role
            provenance[case][name] = {"role": role, "locator": card["source"],
                                      "canonical_sha256": accepted[0], "reviewed_alias_sha256": accepted[1]}
    return canonical, reviewed, provenance


def role_for(case, text, registry):
    return registry.get((case, hash_text(text)), 0)


def verify_delivery(case, declared_role, passage, registry):
    return declared_role in (1, 2) and role_for(case, passage, registry) == declared_role


def run():
    canonical, reviewed, provenance = registries()
    lock = json.loads((EVIDENCE / "semantic-lock.json").read_text())
    score_path = EVIDENCE / "semantic" / "score.json"
    score = json.loads(score_path.read_text())
    model, _ = read_all(score_path.parent)
    assert score["actions_sha256"] == sha256((score_path.parent / "actions.jsonl").read_bytes()).hexdigest()
    test_rows, readings = [], {}
    for case, source, variant, text, expected in lock["key"]:
        pinned_role = role_for(case, text, reviewed)
        exact_only_role = role_for(case, text, canonical)
        assert pinned_role == expected
        wrong = 3 - source
        foreign = "dprk" if case == "venezuela" else "venezuela"
        checks = {
            "correct_role_has_support": verify_delivery(case, source, text, reviewed),
            "wrong_role_rejected": not verify_delivery(case, wrong, text, reviewed),
            "foreign_docket_rejected": not verify_delivery(foreign, source, text, reviewed),
            "unreviewed_suffix_rejected": not verify_delivery(case, source, text + " Editorial addition.", reviewed),
        }
        assert checks["correct_role_has_support"] == bool(expected)
        assert all(checks[k] for k in checks if k != "correct_role_has_support")
        assert exact_only_role == (source if variant == "full" else 0)
        readings[case, source, variant] = {**model[case, source, variant], "truth": pinned_role,
                                            "canonical_intake": exact_only_role, "reviewed_intake": pinned_role}
        test_rows.append({"case": case, "slot": source, "variant": variant, "passage_sha256": hash_text(text),
                          "accepted_role": pinned_role, "checks": checks})

    trained = np.array(json.loads((EVIDENCE / "buffered-fit.json").read_text())["trained_tables"]["matched"])
    routes = json.loads((EVIDENCE / "dprk-routes.json").read_text())["arms"]
    reward = reward_tables()
    report = {}
    for case, matrix in reward.items():
        report[case] = {}
        for prior_name, arms in routes.items():
            prior = [r["probability"] for r in arms["silent"]["worlds"]]
            report[case][prior_name] = {}
            for condition, rates in FAULTS.items():
                _, silent = exact_silent(prior, 14, rates[1])
                contrasts = {}
                for style, versions in STRESSES.items():
                    comparisons = {}
                    for reader in ("pooled", "all_orders_agree", "canonical_intake", "reviewed_intake"):
                        comparisons[reader] = {
                            name: simulate(case, prior, matrix, table, rates, versions, reader, readings)
                            for name, table in (("trained", trained), ("silent", silent))
                        }
                    archived = score["results"][case]["evaluations"][prior_name][condition][style]
                    for mode in ("pooled", "all_orders_agree"):
                        assert all(comparisons[mode][arm] == archived[mode][arm] for arm in ("trained", "silent"))
                    assert all(comparisons["reviewed_intake"][arm] == archived["oracle"][arm]
                               for arm in ("trained", "silent"))
                    contrasts[style] = comparisons
                report[case][prior_name][condition] = contrasts
    return {
        "scope": "Closed-dossier content attestation with reviewed aliases. No new model inference. "
                 "The verified bytes are mapped to canonical evidence IDs and replayed with the existing archived writer.",
        "semantic_scores_sha256": sha256(score_path.read_bytes()).hexdigest(),
        "registry": provenance, "receipt_tests": test_rows, "results": report,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
