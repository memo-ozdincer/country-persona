"""Score the two language-only records and replay named exchange witnesses."""
import argparse
import json
from pathlib import Path
import re
import sys

from minurso_deliberation import ARMS, DRAFT_IDS, HEADINGS, JUDGE, ROLES, case, replay, runner
from minurso_receipt_scores import PRIVATE_GROUPS, citation_ids

sys.path.insert(0, str(JUDGE.parent))
from score import score
sys.path.pop(0)


def schema():
    definitions = json.loads(JUDGE.read_text())["groups"]
    parts = {p["id"]: (p, PRIVATE_GROUPS.get(group["id"], 0))
             for group in definitions for p in group["parts"]}
    grading = [{"id": k, "category": "final", "criterion": p["criterion"], "weight": p["weight"]}
               for k, (p, _) in parts.items()]
    return parts, grading


def historical_sources():
    fixture = case()
    return {**fixture["docket"],
            **{key: v for account in fixture["delegate_evidence"].values() for key, v in account.items()}}


def grade_final(final, annotation, visible, calls):
    official = historical_sources()
    sources = [{"id": k, "text": v} for k, v in official.items()]
    parts, grading = schema()
    text = final["output"]
    met = annotation["met"]
    uncertain = annotation.get("uncertain", {})
    assert (met.keys() | uncertain.keys()) <= parts.keys()
    assert not (met.keys() & uncertain.keys())
    candidate = {"id": final["id"], "mode": "FINAL", "task": "Score the dated historical record.",
                 "answer": text, "rubric": grading, "evidence": sources}
    units, trace, citations_missing, possible_additions = [], {}, [], {}
    for key, (part, private) in parts.items():
        claim = met.get(key, uncertain.get(key))
        if claim is None:
            units.append({"id": key, "status": "unmet", "response": "", "source": [],
                          "reason": "Unstated or does not preserve all of this part."})
            continue
        out, ids, witness = claim
        assert ids and all(i in part["blocks"] for i in ids)
        status = "met" if key in met else "uncertain"
        units.append({"id": key, "status": status, "response": out,
                      "reason": "Reviewed exact quote." if status == "met" else "The context permits more than one interpretation.",
                      "source": [{"block": b, "quote": official[b]} for b in ids]})
        chain = trace if status == "met" else possible_additions
        if witness is not None:
            turn, quote = witness
            assert private and turn == final["seen"][private - 1] and turn in visible
            assert quote.strip() and quote in visible[turn]
            chain[key] = {"turn": turn, "quote": quote}
        elif not private:
            chain[key] = {"public": ids}
        labels = {DRAFT_IDS[private - 1]} if private else set(ids)
        if status == "met" and not any(citation_ids(line) & labels for line in text.splitlines() if out in line):
            citations_missing.append(key)
    scored = score(candidate, {"id": final["id"], "units": units, "guard": annotation["guard"]})
    parenthetical = set(re.findall(r"\(([A-Z]{2,}(?:-[A-Z]+)?)\)", text))
    unknown = sorted((citation_ids(text) | parenthetical) - set(final["evidence_ids"]))
    release = final["ended"] and len(text.split()) <= 155 and scored["guard"] == "clear" and not unknown
    metrics = {
        "historical_points": scored["final"]["lower"],
        "grounded_points": sum(parts[k][0]["weight"] for k in trace),
        "missing_citations": citations_missing, "off_packet_citations": unknown,
        "guard": scored["guard"], "basic_release_eligible": release,
        "strict": release and len(trace) == len(parts) and not citations_missing
        and [line.split(":", 1)[0] for line in text.splitlines() if line.strip()] == list(HEADINGS),
        "proof_chain": trace, "finish": [r["ended"] for r in calls], "words": len(text.split()),
        "input_tokens": sum(len(r["input_ids"]) for r in calls),
        "output_tokens": sum(len(r["output_ids"]) for r in calls),
    }
    if "uncertain" in annotation:
        metrics["historical_bounds"] = scored["final"]
        metrics["grounded_upper"] = metrics["grounded_points"] + sum(
            parts[k][0]["weight"] for k in possible_additions)
        metrics["uncertain_proof_chain"] = possible_additions
    return metrics


def readout(directory, review):
    rows = {r["id"]: r for r in replay(directory, verify_tokens=False)}
    assert review["transcript_sha256"] == runner.digest(directory / "transcript.jsonl")
    assert set(review["arms"]) == set(ARMS)
    sources = [{"id": k, "text": v} for k, v in historical_sources().items()]
    report = {}
    for arm in ARMS:
        final = rows[f"chair-{arm}"]
        visible = {turn: rows[turn]["output"] for turn in final["seen"]}
        calls = [rows[f"open-{i}"] for i in range(2)] + [rows[f"{arm}-{i}"] for i in range(2)] + [final]
        report[arm] = grade_final(final, review["arms"][arm], visible, calls)

    opportunities = [{"id": str(i), "peer": rows[f"open-{1-i}"]["output"],
                      "opening": rows[f"open-{i}"]["output"],
                      "revision": rows[f"peer-{i}"]["output"],
                      "solo_revision": rows[f"independent-{i}"]["output"]} for i in range(2)]
    mechanism = {"id": "exchange-witness", "mode": "MECHANISM", "evidence": sources,
                 "task": "Identify supported uptake of a peer question or claim, compared with the independent revision.",
                 "opportunities": opportunities}
    checked = score(mechanism, {"id": "exchange-witness", "opportunities": review["mechanism"]})
    material = {}
    for arm in ARMS:
        relevant = {f"open-{i}" for i in range(2)} | {f"{arm}-{i}" for i in range(2)}
        ideas = review["ideas"][arm]
        assert len({r["id"] for r in ideas}) == len(ideas)
        counts = {role: {"supported": 0, "unsupported": 0} for role in ROLES}
        for idea in ideas:
            assert idea["status"] in ("supported", "unsupported") and idea["mentions"]
            role_indices = set()
            for turn, quote in idea["mentions"].items():
                assert turn in relevant and quote.strip() and quote in rows[turn]["output"]
                role_indices.add(int(turn[-1]))
            for index in role_indices:
                counts[ROLES[index]][idea["status"]] += 1
        material[arm] = {"delegate_turns": len(relevant), "ideas_per_delegate": counts, "labeled_ideas": len(ideas)}
    return {"scope": review["scope"], "annotations_from": review["transcript_sha256"],
            "arms": report, "mechanism": checked, "partial_idea_inventory": material}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    print(json.dumps(readout(args.directory, json.loads(args.review.read_text())), indent=2, ensure_ascii=False))
