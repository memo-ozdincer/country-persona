"""Score which criteria change when the note gains or loses its qualifier."""
import argparse
from hashlib import sha256
import json

from run_swap import EVIDENCE, HERE, audit, original, pins, requests
from score_protected import identifier, read_rows, verify_generation


def masked(key):
    return sha256(("qualification-swap/" + key).encode()).hexdigest()[:10]


def score(rows):
    inputs = verify_generation(EVIDENCE, rows, requests(), "bosnia2604-qualification-swap", pins())
    prior = read_rows(original.EVIDENCE)
    stats = audit.read(original.HERE / "results.json")["arms"]
    weights = {k: w for k, w, _ in audit.read(audit.PROTOCOL)["rubric"]
               if k not in {"decision", "authority", "civilian_scope"}}
    marks = audit.read(HERE / "marks.json")
    assert marks.keys() == {masked(k) for k in rows}
    original_inputs = {r["id"]: r for r in original.requests()}
    original_marks = audit.read(original.HERE / "marks.json")
    result = {}
    for key, response in rows.items():
        arm = key.split("/")[0]
        body = response["output"]
        mark = marks[masked(key)]
        assert set(mark["spans"]) == weights.keys()
        assert all(span and span in body for spans in mark["spans"].values() for span in spans)
        assert all(span and span in body for span in mark["failures"].values())
        initial_note = json.loads(original_inputs[key]["messages"][1]["content"])["supplement"]["note"]
        edited_note = json.loads(inputs[key]["messages"][1]["content"])["supplement"]["note"]
        assert ("if needed" in initial_note) != ("if needed" in edited_note)
        body_points = sum(weights[k] for k, spans in mark["spans"].items() if spans)
        initial = stats[arm]["protected"]
        result[arm] = {
            "qualification_in_supplement": ["if needed" in initial_note, "if needed" in edited_note],
            "qualification_credited": [bool(original_marks[identifier(key)]["spans"]["uk_powers"]), bool(mark["spans"]["uk_powers"])],
            "delegate_points": [initial["delegate_points"], body_points],
            "release": [initial["release"], not (mark["failures"] or mark["release_uncertain"])],
            "word_count": len(original.assemble(body).split()),
            "input_token_delta": len(response["input_ids"]) - len(prior[key]["input_ids"]),
        }
        assert result[arm]["word_count"] <= 120
    return {"replayed_calls": len(rows), "arms": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score"))
    data = read_rows(EVIDENCE)
    output = dict(sorted((masked(k), original.assemble(row["output"])) for k, row in data.items()))         if cli.parse_args().mode == "deck" else score(data)
    print(json.dumps(output, ensure_ascii=False, indent=2))
