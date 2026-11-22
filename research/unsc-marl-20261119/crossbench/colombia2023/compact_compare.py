"""Compare roles, evidence, process and final criteria across note prompts."""
import json

from run import HERE, runner

BASE = HERE / "evidence"
SHORT = HERE / "compact-evidence"


def read(path):
    return json.loads(path.read_text())


def turns(directory):
    return {row["id"]: row for row in map(json.loads, (directory / "transcript.jsonl").read_text().splitlines())}


def run():
    old_rows, new_rows = turns(BASE), turns(SHORT)
    assert old_rows.keys() == new_rows.keys() and len(old_rows) == 13
    digest_fields = ("model", "device", "torch", "transformers")
    base_launch, new_launch = (read(d / "launch.json") for d in (BASE, SHORT))
    assert all(base_launch[k] == new_launch[k] for k in digest_fields)
    notes = []
    for name, old in old_rows.items():
        current = new_rows[name]
        for field in ("cap", "seen", "evidence_ids"):
            assert old[field] == current[field]
        assert old["messages"][0] == current["messages"][0]
        p_old, p_new = (json.loads(row["messages"][1]["content"]) for row in (old, current))
        assert p_old["sources"] == p_new["sources"]
        if name.endswith("/chair"):
            assert p_old["task"] == p_new["task"]
        else:
            notes.append({"turn": name, "old_words": len(old["output"].split()), "new_words": len(current["output"].split()),
                          "old_ended": old["ended"], "new_ended": current["ended"],
                          "tokens": [len(old["output_ids"]), len(current["output_ids"])]})

    family = next(iter(new_rows)).split("/", 1)[0]
    a, b = (json.loads(new_rows[f"{family}/{arm}/chair"]["messages"][1]["content"])
            for arm in ("independent_drafts", "interactive"))
    note_match = [left == right for left, right in zip(a.pop("working_notes"), b.pop("working_notes"), strict=True)]
    assert a == b
    old, new = (read(d / "results.json")["records"] for d in (BASE, SHORT))
    assert old.keys() == new.keys()
    outcome = {}
    for arm in new:
        a, b = old[arm], new[arm]
        met, updated = a["evidence_spans"].keys(), b["evidence_spans"].keys()
        outcome[arm] = {"old_points": a["points"], "compact_points": b["points"],
                        "newly_supported": sorted(updated - met), "lost": sorted(met - updated),
                        "old_guard_clear": a["source_guard_clear"], "compact_guard_clear": b["source_guard_clear"],
                        "old_complete": a["complete"], "compact_complete": b["complete"],
                        "input_tokens": [a["input_tokens"], b["input_tokens"]],
                        "output_tokens": [a["output_tokens"], b["output_tokens"]],
                        "ideas_by_slot": [a["distinct_tracked_ideas_by_working_slot"], b["distinct_tracked_ideas_by_working_slot"]],
                        "peer_scores": [a["interactions_of_10"], b["interactions_of_10"]]}
    return {"scope": "Matched frozen model and case. Only the note prompt treatment changes. Final prompts keep full dossier "
                     "and synthesis instructions. Different generated notes reach the final writer.",
            "locked_transcripts": {d.name: runner.digest(d / "transcript.jsonl") for d in (BASE, SHORT)},
            "working_note_ends": [sum(n[phase] for n in notes) for phase in ("old_ended", "new_ended")],
            "notes_by_turn": notes, "compact_chair_identical_note_by_slot": note_match, "final_records": outcome}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
