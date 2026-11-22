"""Generate only a ranked decision explanation in a fixed final memo."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_ranked_final as final
from relay_ranked_final_reference import grade_group
from relay_compromise_audit import oracle

CAP = 66
SYSTEM = (
    "Write one short factual paragraph explaining a fixed fictional workshop disposition. "
    "Use only the supplied certificate. Reproduce all compared numbers exactly. "
    "Return prose only, without a heading or list."
)


def envelope(packet):
    heading = "Workshop status: " + packet["checked_status"]
    claims = [f"{c['owner']} ({c['verification']}) submitted {grade_group(c)}."
              for c in packet["received_cards"]]
    if packet["correction"]:
        c = packet["correction"]
        claims.append(f"The {c['owner']} clarified that {c['package']} is a fallback (grade {c['grade']}).")
    authority = ["The workshop has no official authority.",
                 *(f"{s['label']}: {s['quote']}" for s in packet["historical_evidence"])]
    return heading, " ".join(claims), " ".join(authority)


def certificate(packet):
    verdict = packet["checked_status"]
    cards = packet["received_cards"]
    base = {"disposition": verdict, "provisional": any(c["verification"] == "reported" for c in cards)}
    if verdict == "UNRESOLVED":
        missing, = set(packet["possible_card_holders"]) - {c["owner"] for c in cards}
        return {**base, "missing_owner": missing,
                "reason": "A missing scorecard prevents determining whether any package is acceptable to both.",
                "next_step": "Request the missing card."}
    left, right = [card["grades"] for card in cards]
    if verdict == "IMPASSE":
        assert not set(left) & set(right)
        return {**base, "first_acceptable": sorted(left), "second_acceptable": sorted(right),
                "first_owner": cards[0]["owner"], "second_owner": cards[1]["owner"],
                "next_step": "Refer the impasse for further discussion."}
    options = sorted(left.keys() & right.keys())
    best = oracle(options, tuple(left[k] for k in options), tuple(right[k] for k in options))
    assert verdict in best
    alternative = min((best - {verdict}) or (set(options) - {verdict}))
    def payoff(package):
        values = left[package], right[package]
        return {"package": package, "lower_grade": min(values), "sum": sum(values)}
    first, second = payoff(verdict), payoff(alternative)
    reason = ("exact tie, either package is allowed" if first["lower_grade"] == second["lower_grade"]
              and first["sum"] == second["sum"] else "higher lower grade" if first["lower_grade"] > second["lower_grade"]
              else "higher sum breaks an equal lower grade")
    return {**base, "selected": first, "alternative": second, "decisive_comparison": reason}


def suite():
    for row in final.suite():
        packet = row["expected"]
        frame = envelope(packet)
        remaining = 120 - sum(len(part.split()) for part in frame)
        proof = certificate(packet)
        request = {**proof, "word_limit": min(35, remaining),
                   "instruction": "State the comparison or evidence gap and its consequence in plain prose. "
                                  "Retain provisional wording where required. Do not discuss past proceedings."}
        yield {**row, "expected": {"certificate": proof, "frame": frame, "word_limit": request["word_limit"]},
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": json.dumps(request, ensure_ascii=False)}]}


def sources():
    return {**final.sources(), Path(__file__).name: sha256(Path(__file__).read_bytes()).hexdigest()}


@contextmanager
def scenario():
    g = final.generation
    with patch.object(g, "suite", new=suite), patch.object(g, "sources", new=sources), \
         patch.object(g, "WORLDS", new=final.ROOTS), patch.object(g, "CAP", new=CAP):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    with scenario():
        final.generation.run(args.model, args.directory)
