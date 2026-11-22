"""Verify whether the final writer already had sufficient disclosed constraints."""
import argparse
import json
from pathlib import Path

from run import FAMILY, ROOT

OPTIONS = set("ABCD")


def evaluate(run, annotation_path):
    rows = {r["id"]: r for line in (run / "transcript.jsonl").read_text().splitlines() for r in [json.loads(line)]}
    annotations = json.loads(annotation_path.read_text())
    submissions = annotations["submissions"]
    for record_id, r in submissions.items():
        assert r["quote"].strip() and r["quote"] in rows[record_id]["output"]
        accept, exclude = set(r["accept"]), set(r["exclude"])
        assert accept | exclude == OPTIONS and not accept & exclude
    references = json.loads((ROOT / "references.json").read_text())["families"][FAMILY]["workshop_refs_only"]
    result = {}
    for variant in ("overlap", "impasse"):
        result[variant] = {}
        for arm in ("solo", "peer"):
            record = rows[f"final-{arm}-{variant}"]
            left, right = (submissions[d] for d in record["dependencies"])
            derived = set(left["accept"]) & set(right["accept"])
            covered = set(left["exclude"]) | set(right["exclude"])
            certificate = sorted(derived)[0] if len(derived) == 1 else "IMPASSE" if covered == OPTIONS else None
            # The truth audit is after deriving the certificate from visible
            # claims. It neither supplies missing claims nor selects an action.
            ref = references[variant]
            assert [left["accept"], right["accept"]] == ref["allowed_by_role"]
            assert sorted(derived) == ref["joint_packages"]
            result[variant][arm] = {"sources": record["dependencies"], "visible_compatible": sorted(derived),
                                   "visible_excluded": sorted(covered), "determinate_decision": certificate}
    return {"scope": annotations["scope"], "cases": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("run", type=Path)
    cli.add_argument("annotations", type=Path)
    args = cli.parse_args()
    print(json.dumps(evaluate(args.run, args.annotations), indent=2))
