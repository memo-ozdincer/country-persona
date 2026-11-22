"""Validate peer constraint retention and grade exact final records."""
import argparse

import replay

E = replay.E
HERE = replay.HERE


def examples():
    rows = E.read(HERE / "evidence/episodes.json")
    for row, (key, case, order, original, opening, projected) in zip(rows, replay.contexts(), strict=True):
        calls = [opening, dict(original[1], **row["note"]["response"]), dict(original[2], **row["final"]["response"])]
        assert row["episode"] == key
        fact = dict(projected, span=opening["text"])
        yield key, case, order, calls, fact


def deck(kind):
    contents = []
    for key, case, order, calls, fact in examples():
        if kind == "reply":
            contents.append({"id": key, "speaker": calls[1]["speaker"], "reply": calls[1]["text"],
                             "projection": fact["span"]})
        else:
            contents.append(E.final_packet(case, calls))
    return sorted(contents, key=lambda item: item["id"])


def comparison(replies, finals):
    old = E.read(replay.BASE / "results.json")["episodes"]
    rows = {}
    for key, case, order, calls, fact in examples():
        f = E.final_packet(case, calls)
        notes = replay.review.public_readout(case, calls, [fact, *replies[key]])
        final = E.final_score(case, calls, finals[f["id"]])
        independent, original = (old[key.replace("/peer/", "/" + arm + "/")] for arm in ("independent", "peer"))

        def metrics(notes, final, tokens):
            return {"own_requirement_retained": notes["speaker_own_requirement_present"]["1"],
                    "false_endorsements": notes["false_endorsements"],
                    "notes_state": notes["ledger"]["state"],
                    "certifies_key": notes["certifies_key"],
                    "requirements_inference": notes["requirements_only_inference"],
                    "requirements_recover_key": notes["requirements_recover_key"],
                    "exact_decision": final["mechanical"],
                    "words": final["words"], "raw_70": final["raw_70"],
                    "guard": final["guard"], "released_70": final["released_70"],
                    "second_and_final_input_tokens": tokens}

        rows[key] = {
            "independent": metrics(independent["notes"], independent, independent["input_tokens"] - calls[0]["input_tokens"]),
            "raw_peer": metrics(original["notes"], original, original["input_tokens"] - calls[0]["input_tokens"]),
            "constraint_only_peer": metrics(notes, final, sum(r["input_tokens"] for r in calls[1:])),
            "details": {"notes": notes, "final_review_id": f["id"]},
        }
    by_arm = {}
    for name in ("independent", "raw_peer", "constraint_only_peer"):
        selected = [row[name] for row in rows.values()]
        by_arm[name] = {
            "records": len(selected),
            "own_requirement_retained": sum(x["own_requirement_retained"] for x in selected),
            "false_endorsements": sum(x["false_endorsements"] for x in selected),
            "requirements_recover_key": sum(x["requirements_recover_key"] for x in selected),
            "strict_certificates": sum(x["certifies_key"] for x in selected),
            "exact_decisions": sum(x["exact_decision"]["accepted"] for x in selected),
            "raw_70_total": sum(x["raw_70"][0] for x in selected),
            "released_70_total": sum(x["released_70"] for x in selected),
        }
    return {"conditions": rows, "summary": by_arm}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("reply", "final", "score"))
    args = parser.parse_args()
    if args.mode == "score":
        E.emit(comparison(E.read(HERE / "reply-marks.json"), E.read(HERE / "final-marks.json")))
    else:
        E.emit(deck(args.mode))
