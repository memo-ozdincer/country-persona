"""Verify compositional replay and score delegation statements separately."""
import argparse
from hashlib import sha256
import json

from run_protected import EVIDENCE, HERE, PROTOCOL, assemble, audit, pins, requests, runner


def identifier(key):
    return sha256(("protected-record/" + key).encode()).hexdigest()[:10]


def read_rows(directory=EVIDENCE):
    raw = (directory / "transcript.jsonl").read_text().splitlines()
    rows = {r["id"]: r for r in map(json.loads, raw)}
    assert len(raw) == len(rows)
    return rows


def deck(rows):
    return dict(sorted((identifier(key), assemble(row["output"])) for key, row in rows.items()))


def verify_generation(directory, rows, requested, family, input_pins):
    from transformers import AutoTokenizer

    launch, complete = (audit.read(directory / f"{name}.json") for name in ("launch", "complete"))
    assert launch["sha256"] == input_pins
    for filename, field in (("transcript.jsonl", "transcript_sha256"),
                            ("final-records.json", "final_records_sha256")):
        assert runner.digest(directory / filename) == complete[field]
    expected = {family: {key: row["output"] for key, row in rows.items()}}
    assert audit.read(directory / "final-records.json") == expected
    inputs = {r["id"]: r for r in requested}
    assert inputs.keys() == rows.keys() and len(rows) == complete["records"]
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for key, row in rows.items():
        req = inputs[key]
        assert all(row[k] == v for k, v in req.items())
        assert runner.encode(tokenizer, req) == row["input_ids"]
        tokens = row["output_ids"]
        assert 0 < len(tokens) <= req["cap"] and eos not in tokens[:-1]
        assert row["ended"] == (tokens[-1] == eos)
        assert tokenizer.decode(tokens, skip_special_tokens=True).strip() == row["output"]
    return inputs


def score(rows):
    inputs = verify_generation(EVIDENCE, rows, requests(), "bosnia2604-delegate-sections", pins())
    assert len(rows) == 4
    marks = audit.read(HERE / "marks.json")
    assert marks.keys() == deck(rows).keys()
    event = audit.read(audit.PROTOCOL)
    rubric = {key: weight for key, weight, _ in event["rubric"]}
    anchor = audit.read(PROTOCOL)["anchor"]
    anchor_points = sum(rubric.pop(key) for key in ("decision", "authority", "civilian_scope"))
    assert anchor_points == 40 and sum(rubric.values()) == 30
    opened = audit.read(HERE / "input-spans.json")
    before = audit.read(HERE.parent / "results.json")["paths"]
    clarified = audit.read(HERE.parent / "plain-anchor/results.json")["arms"]
    result = {}
    for key, row in rows.items():
        req = inputs[key]
        tokens, body = row["output_ids"], row["output"]
        record = assemble(body)
        assert record == anchor + "\n\n" + body
        arm, _ = key.split("/")
        available = dict(opened["solo_openings" if arm == "solo" else "shared_team_openings"])
        if arm == "adaptive":
            available.update(opened["adaptive_supplement"])
        payload = json.loads(req["messages"][1]["content"])
        assert available.keys() <= rubric.keys()
        assert all(span and span in payload[part][owner] for part, owner, span in available.values())
        mark = marks[identifier(key)]
        spans = mark["spans"]
        assert spans.keys() == rubric.keys()
        assert all(span and span in body for cited in spans.values() for span in cited)
        assert set(mark["uncertain"]) <= {k for k, v in spans.items() if not v}
        failures, uncertainty = mark["failures"], mark["release_uncertain"]
        assert set(failures) | uncertainty.keys() <= set(event["release_failures"])
        assert all(span and span in record for span in failures.values())
        overlength = len(record.split()) > 120
        assert overlength == ("more than 120 words" in failures)
        met = {k for k, v in spans.items() if v}
        earned = sum(rubric[k] for k in met)
        source_supported = sum(rubric[k] for k in met & available.keys())
        passes = not (failures or uncertainty)
        result[arm] = {
            "original": {"points": before[arm]["material_points"], "release": before[arm]["release"]},
            "clarified": {"points": clarified[arm]["new_points"], "release": clarified[arm]["release"]},
            "protected": {"points": anchor_points + earned, "release": passes,
                          "guarded_points": anchor_points + earned if passes else 0,
                          "delegate_points": earned,
                          "strictly_available_delegate_points": sum(rubric[k] for k in available),
                          "available_delegate_points_retained": source_supported,
                          "scored_without_strict_note_support": sorted(met - available.keys()),
                          "available_criteria_dropped": sorted(available.keys() - met),
                          "failures": failures, "release_uncertain": uncertainty,
                          "uncertain_criteria": mark["uncertain"], "ended": row["ended"],
                          "body_words": len(body.split()), "record_words": len(record.split()),
                          "two_body_paragraphs": len(body.split("\n\n")) == 2,
                          "both_delegations_named": all(name in body for name in event["desks"]),
                          "body_input_tokens": len(row["input_ids"]), "body_output_tokens": len(tokens)},
        }
    return {"replayed_calls": len(rows), "provided_public_points_per_record": anchor_points, "arms": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("deck", "score", "records"))
    options = parser.parse_args()
    data = read_rows()
    result = {"deck": deck, "score": score, "records": lambda rows: {
        key: assemble(row["output"]) for key, row in rows.items()
    }}[options.mode](data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
