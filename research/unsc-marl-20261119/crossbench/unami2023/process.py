"""Replay a bounded source-idea inventory against the UNAMI working notes."""
from collections import Counter
import json
import re

from episode import ARMS, HERE, runner

PATTERNS = {
    "adoption": r"(?:adopted (?:unanimously )?|adopt )(?:United States draft S/2023/378 as )?(?:resolution )?2682 \(2023\)",
    "unanimity": r"unanimously adopted|15 in favour",
    "mandate-deadline": r"mandate until 31 May 2024",
    "dialogue-and-reconciliation": r"inclusive political dialogue and reconciliation",
    "participation-and-input": r"participation of women, alongside civil society and youth input",
    "four-month-reporting": r"report [^.\n]*? every four months",
    "review-deadline": r"independent strategic review of UNAMI (?:was mandated |to conclude )?by 31 March 2024",
    "threat-assessment": r"assess(?:ing)? (?:current )?threats",
    "task-relevance": r"mandate relevance|relevance of UNAMI(?:'s)? tasks",
    "make-recommendations": r"recommend(?:ing)? changes to (?:the )?mandate, structure, and staffing|"
                            r"recommendations (?:regarding|on) mandate, structure, staffing",
    "regional-cooperation": r"(?:ways to )?support Iraq in strengthening regional cooperation",
    "full-consultation-boundary": r"consult Iraq, UN agencies, Member States, regional organizations, "
                                  r"independent experts, civil society, and Kuwait",
    "no-national-explanations": r"No national explanation of vote appears in this meeting record",
}
PROMOTION = r"participation of women, civil society, and youth"
TRANSCRIPT = HERE / "evidence" / "transcript.jsonl"


def ideas(row):
    spans = {}
    for key, pattern in PATTERNS.items():
        search = re.search(pattern, row["output"], re.IGNORECASE)
        if search:
            spans[key] = search.group()
    return spans


def run():
    records = {r["id"].split("/", 1)[1]: r for r in map(json.loads, TRANSCRIPT.read_text().splitlines())}
    final = {}
    for arm in ARMS:
        initial = "pooled_solo" if arm == "pooled_solo" else "common"
        labels = [f"{initial}/opening_{j}" for j in range(2)] + [f"{arm}/revision_{j}" for j in range(2)]
        labels.append(f"{arm}/chair")
        selected = [records[label] for label in labels]
        slots = [ideas(row) for row in selected]
        peer_trace = []
        if arm == "interactive":
            for j in range(2):
                opening, peer, revision = selected[j], selected[1-j], selected[j+2]
                assert revision["seen"] == [opening["id"], peer["id"]]
                independent = records[f"independent_drafts/revision_{j}"]
                own_recurrence = slots[j+2].keys() & slots[j].keys()
                peer_specific = slots[j+2].keys() & slots[1-j].keys() - own_recurrence - ideas(independent).keys()
                peer_trace.append({"recipient": revision["id"], "visible_peer": peer["id"],
                                   "peer_specific_matches": sorted(peer_specific),
                                   "own_opening_ideas_repeated": sorted(own_recurrence)})
        final[arm] = {"working_turns": 4, "synthesis_turns": 1,
                      "working_idea_counts_by_slot": [len(slots[j].keys() | slots[j+2].keys()) for j in range(2)],
                      "peer_successor_checks": peer_trace,
                      "matched_spans": dict(zip(labels, slots, strict=True)),
                      "participation_promotions": [label for label, row in zip(labels, selected, strict=True)
                                                   if re.search(PROMOTION, row["output"])],
                      "input_tokens": sum(len(row["input_ids"]) for row in selected),
                      "output_tokens": sum(len(row["output_ids"]) for row in selected),
                      "cap_hits": [label for label, row in zip(labels, selected, strict=True) if not row["ended"]]}
    return {"scope": "Exact substring evidence for a fixed authored inventory. Counts are lower bounds for these "
                     "source ideas, and omit other ideas and unsupported propositions. The two solo slots are one analyst.",
            "transcript_sha256": runner.digest(TRANSCRIPT), "results": final}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
