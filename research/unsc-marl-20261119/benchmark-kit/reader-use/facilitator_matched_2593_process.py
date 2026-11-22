"""Count source-supported ideas and trace potential cross-desk uptake."""
import argparse
import json
from pathlib import Path

import facilitator_matched_2593_score as score

study = score.study
EVIDENCE = study.EVIDENCE


def evaluate(rows):
    owners = score.load(EVIDENCE / "idea-key.json")
    known = {idea for ideas in owners.values() for idea in ideas}
    annotations = score.load(EVIDENCE / "idea-review.json")
    assert rows.keys() == annotations.keys()
    for key, spans in annotations.items():
        assert spans.keys() <= known
        assert all(span and span in rows[key]["output"] for span in spans.values())
    per_arm = {}
    for arm in study.ARMS:
        ids = study.trace(arm)
        first = set()
        notes = {}
        for speaker, key in zip(owners, ids[:-1], strict=True):
            introduced = set(annotations[key]) - first
            notes[speaker] = {"note": key, "new_supported_ideas": sorted(introduced),
                              "reused_supported_ideas": sorted(set(annotations[key]) & first),
                              "first_mentions_retained_in_final": sorted(introduced & annotations[ids[-1]].keys())}
            first.update(annotations[key])
        per_arm[arm] = {"writing_calls": len(ids), "notes": notes,
                        "supported_final_ideas": sorted(annotations[ids[-1]]),
                        "final_ideas_absent_in_notes": sorted(set(annotations[ids[-1]]) - first)}
    peer = set(annotations["peer/last"])
    independent = set(annotations["independent/last"])
    peer_openers = set(annotations["private/open0"]) | set(annotations["private/open1"])
    return {"arms": per_arm, "matched_last_note_added_ideas": sorted(peer - independent),
            "matched_last_note_lost_ideas": sorted(independent - peer),
            "supported_uptake_candidates": sorted((peer - independent) & peer_openers),
            "supported_uptake_candidates_in_peer_final": sorted((peer - independent) & peer_openers
                                                               & annotations["peer/final"].keys())}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(evaluate(study.verify(cli.parse_args().directory)), indent=2))
