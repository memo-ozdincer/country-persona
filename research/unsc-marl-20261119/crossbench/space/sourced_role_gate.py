"""Replay a separate-field veto over the archived global confirmations."""
from collections import defaultdict
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAIMS = HERE / "sourced-confirmation-evidence/adjudicated.json"
ROLES = HERE / "sourced-role-binding-evidence/results.json"


def run():
    original = json.loads(CLAIMS.read_text())
    arms = json.loads(ROLES.read_text())
    vetoes = defaultdict(list)
    for field, checks in arms["fields"].items():
        local = tuple(checks["source"]["inputs"])
        for kind, answer in arms["comparisons"][field].items():
            text, = checks[kind]["inputs"]
            vetoes[local, text].append((field, answer))
    results = {}
    for method in ("direct", "scoped"):
        issued = []
        for case in original["records"]:
            key = (tuple(case["passages"].values()), case["proposed"])
            checks = vetoes.get(key, ())
            proposed = case[method]["stable"]
            is_confirm = bool(proposed) and proposed[0] == "confirm"
            blocked = is_confirm and any(result in {"mismatch", "defer"} for _, result in checks)
            issued.append({"id": case["id"], "raw": proposed, "used_field_checks": checks,
                           "issued_confirmation": is_confirm and not blocked, "blocked": blocked,
                           "supported_confirmation": case["expected"][0] == "confirm",
                           "original_proposal_supported": proposed == case["expected"]})
        results[method] = {
            "blocked_confirmations": sum(r["blocked"] for r in issued),
            "valid_confirmations_remaining": sum(r["issued_confirmation"] and r["original_proposal_supported"]
                                                for r in issued),
            "unsupported_remaining": sum(r["issued_confirmation"] and not r["original_proposal_supported"]
                                         for r in issued),
            "records": issued,
        }
    return {"scope": "Posthoc replay. Separate field results are reused only when both source and proposed text "
                     "match an evaluated view exactly. The targeted fields were chosen after the broad pilot. "
                     "A mismatch or unresolved field can veto confirmation without proving contradiction.",
            "results": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
