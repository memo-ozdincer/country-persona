"""Measure logged turns and a source-reviewed inventory of atomic ideas."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

PHASE = {"initial": 0, "revision": 1, "synthesis": 2}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def measure(transcript, inventory):
    require(hashlib.sha256(transcript.read_bytes()).hexdigest() == inventory["transcript_sha256"],
            "Transcript checksum mismatch")
    records = [json.loads(line) for line in transcript.read_text().splitlines()]
    rows = [r for r in records if r["split_group"] == inventory["scenario"]
            and r["condition"] == inventory["condition"]]
    turns = {r["response_id"]: r for r in rows}
    require(turns and len(turns) == len(rows), "Response IDs must be nonempty and unique")
    for row in rows:
        known = set(row["depends_on_response_ids"])
        require(known <= turns.keys(), "A visible turn is missing from this condition")
        require(all(PHASE[turns[k]["stage"]] < PHASE[row["stage"]] for k in known),
                "Visibility must run from an earlier phase")
    used_ideas = set()
    mentioned = defaultdict(set)
    introduced = defaultdict(set)
    added_in_revision = defaultdict(set)
    visible_cross_role = defaultdict(set)
    same_role_retained = defaultdict(set)
    final = set()
    guard_chain = []
    for idea in inventory["ideas"]:
        key = idea["id"]
        require(key not in used_ideas, f"Duplicate idea: {key}")
        used_ideas.add(key)
        require(idea["status"] in {"supported", "unsupported", "uncertain"}, f"Unknown status: {key}")
        cites = {m["turn"]: m["quote"] for m in idea["mentions"]}
        require(cites and len(cites) == len(idea["mentions"]), f"Missing or repeated turn: {key}")
        for turn, quote in cites.items():
            require(turn in turns and isinstance(quote, str) and bool(quote.strip()) and quote in turns[turn]["output"],
                    f"Missing quote for {key} in {turn}")
        first_phase = min(PHASE[turns[t]["stage"]] for t in cites)
        for turn in cites:
            row = turns[turn]
            phase, role = PHASE[row["stage"]], row["country"]
            if phase == 2:
                final.add(key)
                continue
            mentioned[role].add(key)
            ancestors = [turns[t] for t in row["depends_on_response_ids"] if t in cites]
            if phase == first_phase:
                introduced[role].add(key)
                if phase == 1:
                    added_in_revision[role].add(key)
            elif any(t["country"] == role for t in ancestors):
                same_role_retained[role].add(key)
            elif any(t["country"] != role for t in ancestors):
                # This checks exposure and observed recurrence. A paired solo
                # comparison is required to claim a peer contribution.
                visible_cross_role[role].add(key)
        if idea.get("promotes"):
            prior = next((item for item in inventory["ideas"] if item["id"] == idea["promotes"]), None)
            require(prior and prior["status"] == "supported" and idea["status"] == "unsupported",
                    "A promotion must point to a supported claim")
            source_turns = {m["turn"] for m in prior["mentions"]}
            require(any(source_turns & set(turns[t]["depends_on_response_ids"]) for t in cites),
                    "No prior span was visible for the reported promotion")
            guard_chain.append({"bounded_idea": prior["id"], "stronger_unsupported_idea": key})

    support = {i["id"]: i["status"] for i in inventory["ideas"]}
    agent_rows = [r for r in rows if r["stage"] != "synthesis"]
    roles = sorted({r["country"] for r in agent_rows})
    return {
        "scope": inventory["scope"], "scenario": inventory["scenario"], "condition": inventory["condition"],
        "all_logged_generations": len(rows), "agent_turns": len(agent_rows),
        "phase_counts": dict(Counter(r["stage"] for r in rows)),
        "by_agent": {role: {
            "turns": sum(r["country"] == role for r in agent_rows),
            "generated_tokens": sum(r["generated_tokens"] for r in agent_rows if r["country"] == role),
            "distinct_ideas_mentioned": len(mentioned[role]),
            "distinct_supported_ideas_mentioned": sum(support[k] == "supported" for k in mentioned[role]),
            "first_phase_ideas": sorted(introduced[role]),
            "supported_first_phase_count": sum(support[k] == "supported" for k in introduced[role]),
            "group_new_ideas_in_revision": sorted(added_in_revision[role]),
            "same_agent_repeat": sorted(same_role_retained[role]),
            "visible_cross_agent_recurrence": sorted(visible_cross_role[role]),
        } for role in roles},
        "distinct_ideas_in_inventory": len(used_ideas), "ideas_in_final": sorted(final),
        "supported_in_final": sum(support[k] == "supported" for k in final),
        "unsupported_in_final": sum(support[k] == "unsupported" for k in final),
        "strengthened_beyond_evidence": guard_chain,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.transcript, json.loads(args.inventory.read_text())), indent=2, ensure_ascii=False))
