"""Render a blinded judge request and validate quote-grounded judgments."""
import argparse
import json
from pathlib import Path

PROMPT = Path(__file__).with_name("instructions.md")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def by_id(rows):
    result = {row["id"]: row for row in rows}
    require(len(result) == len(rows), "Duplicate IDs")
    return result


def request(packet):
    common = {k: packet[k] for k in ("id", "mode", "task", "evidence")}
    if packet["mode"] == "FINAL":
        return {**common, "rubric": packet["rubric"], "answer": packet["answer"]}
    require(packet["mode"] == "MECHANISM", "Unknown request mode")
    return {**common, "opportunities": packet["opportunities"]}


def citations(items, blocks):
    require(isinstance(items, list), "Citations must be a list")
    for item in items:
        require(set(item) == {"block", "quote"}, "Malformed citation")
        quote, key = item["quote"], item["block"]
        require(isinstance(quote, str) and quote.strip() and key in blocks and quote in blocks[key]["text"],
                "Citation is absent from its identified source block")


def span(value, text, needed):
    require(isinstance(value, str) and (not value or value.strip() and value in text),
            "Claim span is absent from the candidate text")
    require(not needed or bool(value), "Candidate text span required")


def reason(entry):
    require(isinstance(entry["reason"], str) and bool(entry["reason"].strip()), "Reason is required")


def bounds(graded, rubric, category):
    specs = [spec for spec in rubric if spec["category"] == category]
    lower = sum(spec["weight"] for spec in specs if graded[spec["id"]]["status"] == "met")
    uncertain = sum(spec["weight"] for spec in specs if graded[spec["id"]]["status"] == "uncertain")
    return {"lower": lower, "upper": lower + uncertain, "possible": sum(spec["weight"] for spec in specs)}


def score(packet, verdict):
    packet = request(packet)
    blocks = by_id(packet["evidence"])
    require(verdict["id"] == packet["id"], "Judgment ID mismatch")
    if packet["mode"] == "MECHANISM":
        require(set(verdict) == {"id", "opportunities"}, "Malformed mechanism response")
        opportunities, outcomes = by_id(packet["opportunities"]), by_id(verdict["opportunities"])
        require(opportunities.keys() == outcomes.keys(), "Opportunity IDs must match")
        for key, outcome in outcomes.items():
            item = opportunities[key]
            require(set(outcome) == {"id", "status", "peer_specific", "peer", "revision", "source", "reason"},
                    "Malformed opportunity grade")
            status = outcome["status"]
            require(status in {"used", "challenged", "ignored", "adopted_unsupported", "uncertain"},
                    "Unknown opportunity status")
            require(type(outcome["peer_specific"]) is bool, "peer_specific must be boolean")
            span(outcome["peer"], item["peer"], True)
            actionable = status in {"used", "challenged", "adopted_unsupported"}
            span(outcome["revision"], item["revision"], actionable)
            citations(outcome["source"], blocks)
            reason(outcome)
            require(not actionable or outcome["source"], "Actionable grade requires source evidence")
            require(not outcome["peer_specific"] or (status in {"used", "challenged"}
                    and all(isinstance(item.get(k), str) and item[k].strip() for k in ("opening", "solo_revision"))),
                    "Peer-specific credit requires a valid action and matched history")
        return {"opportunities": len(outcomes), "credited": sum(r["peer_specific"] for r in outcomes.values())}

    require(set(verdict) == {"id", "units", "guard"}, "Malformed final response")
    graded = by_id(verdict["units"])
    rubric = packet["rubric"]
    require(set(graded) == set(by_id(rubric)), "Criterion IDs must match")
    require(all(r["category"] in {"final", "points", "arguments"}
                and type(r["weight"]) is int and r["weight"] > 0 for r in rubric), "Invalid criterion weight")
    require(sum(r["weight"] for r in rubric if r["category"] == "final") == 70,
            "Final criterion weights must total 70")
    for unit in graded.values():
        require(set(unit) == {"id", "status", "source", "response", "reason"}, "Malformed criterion grade")
        require(unit["status"] in {"met", "unmet", "uncertain"}, "Unknown criterion status")
        citations(unit["source"], blocks)
        span(unit["response"], packet["answer"], unit["status"] == "met")
        reason(unit)
        require(unit["status"] != "met" or unit["source"], "A met unit requires source evidence")
    guard = verdict["guard"]
    require(set(guard) == {"status", "source", "response", "reason"}, "Malformed guard")
    require(guard["status"] in {"clear", "failed", "uncertain"}, "Unknown guard status")
    citations(guard["source"], blocks)
    span(guard["response"], packet["answer"], guard["status"] == "failed")
    require(guard["status"] != "failed" or guard["source"], "A guard failure requires source or task evidence")
    reason(guard)
    result = {c: bounds(graded, rubric, c) for c in ("final", "points", "arguments")}
    result["guard"] = guard["status"]
    result["strict"] = guard["status"] == "clear" and result["final"]["lower"] == result["final"]["possible"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--verdict", type=Path)
    args = parser.parse_args()
    packet = json.loads(args.packet.read_text())
    if args.verdict:
        result = score(packet, json.loads(args.verdict.read_text()))
    else:
        result = {"system": PROMPT.read_text(), "user": request(packet)}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
