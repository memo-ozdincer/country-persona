"""Audit a frozen learned responder on the held UNIFIL workshop menu."""
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "first-stage-credit"))
import first_link as frozen
import ledger_features as public

E, ROLES = public.E, public.ROLES
OPTIONS = "ABCD"
SEND = frozen.SEND
RATES = (.8, .04)
BONUS = .2


def accepted(menu, requirement):
    return {row["id"] for row in menu if all(row[k] == v for k, v in requirement.items())}


def conditions(menu):
    return [{field: value} for field in ("cadence", "format") for value in sorted({r[field] for r in menu})]


def role_candidates(menu, log):
    options = [(req, accepted(menu, req)) for req in conditions(menu)]
    return {role: [req for req, compatible in options if all(
        set(row.get("accepts", ())) <= compatible and not set(row.get("excludes", ())) & compatible
        for row in log if row["role"] == role
    )] for role in ROLES}


def state(menu, log):
    proof = public.signed.chair.readout(OPTIONS, ROLES, log)
    candidates = role_candidates(menu, log)
    assert all(candidates.values())
    arms = list(proof["verified_options"])
    status = (arms[0] if arms else "IMPASSE" if proof["state"] == "IMPASSE" else "UNRESOLVED")
    known = all(len(x) == 1 for x in candidates.values())
    points = 0. if status == "UNRESOLVED" else 1. if known else 1-BONUS
    return status, points, candidates


def subsets(rows):
    for i in range(len(rows)+1):
        yield from combinations(rows, i)


def summarize(cases, weights, rate):
    menu = cases["menu"]
    total, details = {}, {}
    for world in cases["worlds"]:
        own = [accepted(menu, r) for r in world["requirements"]]
        gold = own[0] & own[1] or {"IMPASSE"}
        genuine = [(role, query, public.signed.claim(f"{i}/{query}", role, query in own[i], query))
                   for i, role in enumerate(ROLES) for query in OPTIONS]
        counts = {name: Counter() for name in ("frozen_head", "proof_rule", "record_oracle")}
        book = Counter()
        witnesses = {}
        for log in subsets([row for _, _, row in genuine]):
            before, full_before, prior = state(menu, log)
            assert before in gold | {"UNRESOLVED"}
            for role, query, claim in genuine:
                after, full_after, posterior = state(menu, [*log, {**claim, "id": "reply"}])
                assert after in gold | {"UNRESOLVED"} and full_after >= full_before
                assert all(t in posterior[label] for label,t in zip(ROLES, world["requirements"], strict=True))
                signed = bool(claim.get("accepts"))
                features = public.features(log, role, query, rate, signed)
                makes_proof = before == "UNRESOLVED" and after != before
                attribution_only = before != "UNRESOLVED" and full_after > full_before
                new_record_value = rate*(full_after-full_before) - SEND
                actions = {
                    "frozen_head": frozen.margin(features, weights) > 0.,
                    "proof_rule": makes_proof,
                    "record_oracle": new_record_value > 1e-10,
                }
                book["presentations"] += 1
                book["new_proof_possible"] += makes_proof
                book["attribution_only_possible"] += attribution_only
                if makes_proof and not actions["frozen_head"]:
                    bucket = "missed_approval" if signed else "missed_impasse"
                elif attribution_only and not actions["frozen_head"]:
                    bucket = "missed_attribution_after_proof"
                elif actions["frozen_head"] and full_after == full_before:
                    bucket = "send_no_record_gain"
                else:
                    bucket = "none"
                if bucket != "none":
                    book[bucket] += 1
                    witnesses.setdefault(bucket, {
                        "opening": log, "reply": claim, "queried": query, "verified_sign": signed,
                        "before": before, "after": after, "prior_candidates": prior,
                        "posterior_candidates": posterior, "observations": features,
                    })
                for arm, speaks in actions.items():
                    m = counts[arm]
                    m["sends"] += speaks
                    m["new_proofs_if_delivered"] += speaks and makes_proof
                    m["attribution_only_replies_if_delivered"] += speaks and attribution_only
                    m["no_record_gain_sends"] += speaks and full_after == full_before
                    m["expected_record_gain"] += rate*(full_after-full_before) if speaks else 0.
                    m["net_increment"] += new_record_value if speaks else 0.
                    m["agrees_with_record_oracle"] += speaks == actions["record_oracle"]
        total[world["id"]] = {"gold": sorted(gold), "counts": book, "arms": counts}
        details[world["id"]] = witnesses
    return {"worlds": total, "witnesses": details}


def run():
    config = E.read(HERE/"case.json")
    weights_path = HERE.parent/"first-stage-credit/ledger-fit.json"
    saved = E.read(weights_path)
    weights = saved["weights"]["ledger_only"]
    assert {w["id"] for w in config["worlds"]} == {"unique-agreement", "impasse", "multiple-agreements"}
    sources = [HERE/path for name,path in config["sources"].items() if name in {
        "retrospective_evidence", "benchmark_linkage"
    }]
    texts, links = map(E.read, sources)
    assert config["meeting"] == links["meeting"] and config["date"] == links["date"]
    assert "2695" in texts["evidence"][0]["text"]
    files = [Path(__file__), HERE/"case.json", HERE/"protocol.md", weights_path, *sources]
    return {"scope": "three fictional worlds from one historical event family",
            "fixed_delivery": RATES, "credit_proxy": BONUS,
            "results": {str(rate): summarize(config, weights, rate) for rate in RATES},
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    E.emit(run())
