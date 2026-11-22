"""Replay the paired anchor change and score source-span annotations."""
import argparse
from hashlib import sha256
import json

from run_anchor import EVIDENCE, HERE, audit, pins, requests, runner


def identifier(key):
    return sha256(("plain-anchor/" + key).encode()).hexdigest()[:10]


def records():
    rows = (EVIDENCE / "transcript.jsonl").read_text().splitlines()
    result = {row["id"]: row for row in map(json.loads, rows)}
    assert len(result) == len(rows)
    return result


def compare(rows):
    from transformers import AutoTokenizer

    original = audit.get_rows()
    launch = audit.read(EVIDENCE / "launch.json")
    complete = audit.read(EVIDENCE / "complete.json")
    assert launch["sha256"] == pins()
    assert complete["transcript_sha256"] == runner.digest(EVIDENCE / "transcript.jsonl")
    assert complete["final_records_sha256"] == runner.digest(EVIDENCE / "final-records.json")
    expected_records = {key: row["output"] for key, row in rows.items()}
    assert audit.read(EVIDENCE / "final-records.json") == {"bosnia2604-plain-anchor": expected_records}
    request_rows = {row["id"]: row for row in requests()}
    assert rows.keys() == request_rows.keys()
    assert len(rows) == complete["records"] == 4

    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    mark = audit.read(HERE / "marks.json")
    assert mark.keys() == {identifier(key) for key in rows}
    initial_marks = audit.read(HERE.parent / "marks.json")
    initial_scores = audit.read(HERE.parent / "results.json")["paths"]
    protocol = audit.read(audit.PROTOCOL)
    weights = {key: weight for key, weight, _ in protocol["rubric"]}
    release_failures = set(protocol["release_failures"])

    result = {}
    for key, row in rows.items():
        request = request_rows[key]
        assert all(row[k] == v for k, v in request.items())
        assert runner.encode(tokenizer, request) == row["input_ids"]
        out = row["output_ids"]
        assert 0 < len(out) <= request["cap"] and eos not in out[:-1]
        assert row["ended"] == (out[-1] == eos)
        text = row["output"]
        assert tokenizer.decode(out, skip_special_tokens=True).strip() == text

        grade = mark[identifier(key)]
        good = grade["spans"]
        assert good.keys() == weights.keys()
        assert all(span and span in text for spans in good.values() for span in spans)
        assert set(grade["uncertain"]) <= {k for k, spans in good.items() if not spans}
        failures = grade["failures"]
        uncertain_release = grade["release_uncertain"]
        assert set(failures) | uncertain_release.keys() <= release_failures
        assert all(span and span in text for span in failures.values())
        words = len(text.split())
        assert (words > 120) == ("more than 120 words" in failures)
        arm, _ = key.split("/")
        initial = initial_marks[audit.masked(key)]["spans"]
        score = sum(weights[k] for k, v in good.items() if v)
        previous = initial_scores[arm]["material_points"]
        result[arm] = {
            "old_points": previous,
            "new_points": score,
            "delta": score - previous,
            "new_points_if_uncertain_credit": score + sum(weights[k] for k in grade["uncertain"]),
            "gained": [k for k in good if good[k] and not initial[k]],
            "lost": [k for k in good if initial[k] and not good[k]],
            "old_release": initial_scores[arm]["release"],
            "release": not (failures or uncertain_release),
            "old_guarded_points": previous if initial_scores[arm]["release"] else 0,
            "new_guarded_points": score if not (failures or uncertain_release) else 0,
            "failures": failures,
            "release_uncertain": uncertain_release,
            "final_input_token_delta": len(row["input_ids"]) - len(original[key]["input_ids"]),
            "final_output_tokens": len(out), "ended": row["ended"], "words": words,
        }
    contrasts = {
        comparison: {metric: result["adaptive"][metric] - result[comparison][metric]
                     for metric in ("old_points", "new_points", "old_guarded_points", "new_guarded_points")}
        for comparison in result if comparison != "adaptive"
    }
    return {"calls_replayed": len(rows), "arms": result, "adaptive_minus_comparison": contrasts}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score"))
    opts = cli.parse_args()
    data = records()
    output = (
        dict(sorted((identifier(key), row["output"]) for key, row in data.items()))
        if opts.mode == "deck" else compare(data)
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
