"""Score the records and semantic decisions under zero and transferred cutoffs."""
import json

from collect_doc import CLAIM, HERE, OPTIONS, fixture, prior, read


def margins(outputs, arm, view):
    result = {}
    for suffix, labels in prior.MAPPINGS.items():
        scores = outputs[f"{arm}/{view}/{suffix}"]["logits"]
        process = next(label for label, action in labels.items() if action == "process")
        fund = next(label for label, action in labels.items() if action == "fund")
        result[suffix] = scores[process] - scores[fund]
    return result | {"mean": sum(result.values()) / len(result)}


def run():
    sources = read(HERE / "source-views.json")
    archive = read(HERE / "verified.json")["outputs"]
    intercept, slope = read(CLAIM / "results.json")["reform_claim_scoped"]["coefficients"]
    rows = {}
    for key, source in sources["views"].items():
        early = source["registered"]
        records = {}
        for role, late in OPTIONS.items():
            record = fixture.render(early, late)
            grade = fixture.verify(early, late, record)
            records[role] = {"record": record, "grade": grade, "sent": late}
        direct = margins(archive, "direct", key)
        claim = margins(archive, "claim", key)
        policies = {
            "fixed_consultation": "process", "fixed_unama": "fund",
            "direct": "process" if direct["mean"] > 0 else "fund",
            "claim_at_zero": "process" if claim["mean"] > 0 else "fund",
            "claim_2553_cutoff": "process" if intercept + slope * claim["mean"] > 0 else "fund",
        }
        best = max(row["grade"]["released_70"] for row in records.values())
        rows[key] = {
            "condition_supported": source["support_condition"], "registered": early,
            "scores": {"direct": direct, "claim": claim},
            "choices": {policy: {"sent": records[role]["sent"],
                                 "release": records[role]["grade"]["released_70"],
                                 "matches_best": records[role]["grade"]["released_70"] == best,
                                 "classified_support": role == "process"}
                        for policy, role in policies.items()},
            "attainable": best, "records": records,
        }
    names = next(iter(rows.values()))["choices"]
    return {
        "official_pdf_sha256": sources["sha256"],
        "cases": rows,
        "mean_oracle_release": round(sum(r["attainable"] for r in rows.values()) / len(rows), 8),
        "summary": {policy: {
            "matches_best": sum(r["choices"][policy]["matches_best"] for r in rows.values()),
            "matches_best_on_untied": sum(r["choices"][policy]["matches_best"] for r in rows.values()
                                         if r["registered"] is not None),
            "support_accuracy": sum(r["choices"][policy]["classified_support"] == r["condition_supported"]
                                    for r in rows.values()),
            "mean_release": round(sum(r["choices"][policy]["release"] for r in rows.values()) / len(rows), 8),
        } for policy in names},
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
