"""Use v1 final scoring for the four clarified-format writer outputs."""
import argparse
import json

import format_replay as replay

E, HERE = replay.E, replay.HERE


def rows():
    baseline = {row["id"]: row for row in map(
        json.loads, (HERE / "evidence/episodes.jsonl").read_text().splitlines())}
    for line in (HERE / "format-evidence/records.jsonl").read_text().splitlines():
        row = json.loads(line)
        old = baseline[row["id"]]
        case = replay.transfer.cases()[row["id"].split("/")[0]]
        ev = [old["first"]["response"], old["second"]["response"], row["response"]]
        yield row["id"], case, ev


def deck():
    output = {p["id"]: p for p in (E.final_packet(case, calls) for _, case, calls in rows())}
    return [output[k] for k in sorted(output)]


def compare():
    original = E.read(HERE / "results.json")["conditions"]
    marks = E.read(HERE / "format-marks.json")
    assert set(marks) == {r["id"] for r in deck()}
    output = {}
    for key, case, calls in rows():
        opaque = E.final_packet(case, calls)
        current = E.final_score(case, calls, marks[opaque["id"]])
        old = original[key]["arms"]["with_certificate"]
        output[key] = {"original": old, "format_clarified": current | {"blind_id": opaque["id"]}}
    scores = [r["format_clarified"] for r in output.values()]
    return {"episodes": output,
            "mechanical_correct": sum(r["mechanical"]["accepted"] for r in scores),
            "released": sum(r["release"] for r in scores), "strict": sum(r["strict"] for r in scores),
            "released_70_total": sum(r["released_70"] for r in scores)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score"))
    args = cli.parse_args()
    E.emit(deck() if args.mode == "deck" else compare())
