"""Check the frozen judge's JSON and compare it with exact-span reviews."""
import argparse
import json

import audit
import judge
from run import runner

VERDICTS = {"met", "unmet", "uncertain"}


def parse(output):
    lines = output.splitlines()
    if lines and lines[0] in ("```json", "```"):
        output = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(output)


def run(study):
    from transformers import AutoTokenizer

    files = study.DIRECTORY
    launch, complete = [audit.read(files / name) for name in ("launch.json", "complete.json")]
    trace = files / "transcript.jsonl"
    finals = files / "final-records.json"
    assert launch["sha256"] == study.pins()
    assert complete["transcript_sha256"] == runner.digest(trace)
    assert complete["final_records_sha256"] == runner.digest(finals)
    records = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    verified = set()

    def replay(requests):
        for req in requests:
            key = req["id"]
            row = records[key]
            assert key not in verified and all(row[k] == v for k, v in req.items())
            assert runner.encode(tokenizer, req) == row["input_ids"]
            tokens = row["output_ids"]
            assert 0 < len(tokens) <= req["cap"] and eos not in tokens[:-1]
            assert (tokens[-1] == eos) == row["ended"]
            assert tokenizer.decode(tokens, skip_special_tokens=True).strip() == row["output"]
            verified.add(key)
        return records

    result, = study.episode(replay)
    assert verified == records.keys() and complete["records"] == len(verified) == 4
    assert audit.read(finals) == {result["family"]: {k: r["output"] for k, r in records.items()}}
    deck = audit.deck(audit.get_rows())
    rubric = {name: points for name, points, _ in audit.read(judge.PROTOCOL)["rubric"]}
    reviewed = audit.read(audit.HERE / "marks.json")
    comparison = {}
    for key, row in records.items():
        case = {"ended": row["ended"], "tokens": len(row["output_ids"])}
        try:
            parsed = parse(row["output"])
        except json.JSONDecodeError as error:
            case["schema_error"] = f"Invalid JSON at character {error.pos}: {error.msg}"
        else:
            criteria = parsed.get("criteria") if isinstance(parsed, dict) else None
            if not isinstance(criteria, dict) or set(criteria) != rubric.keys() or not all(
                isinstance(item, dict) and item.get("verdict") in VERDICTS
                and isinstance(item.get("spans"), list) and all(isinstance(s, str) for s in item["spans"])
                and isinstance(item.get("reason"), str) for item in criteria.values()
            ) or not isinstance(parsed.get("release_failures"), list):
                case["schema_error"] = "Missing or malformed criteria or release failures"
            else:
                met = {name for name, item in criteria.items() if item["verdict"] == "met"}
                valid = {name for name in met if criteria[name]["spans"]
                         and all(span and span in deck[key] for span in criteria[name]["spans"])}
                target = {name for name, spans in reviewed[key]["spans"].items() if spans}
                faults = parsed["release_failures"]
                valid_faults = [
                    report for report in faults
                    if isinstance(report, dict) and isinstance(report.get("type"), str)
                    and isinstance(report.get("span"), str) and report["span"] and report["span"] in deck[key]
                ]
                case.update({
                    "raw_points": sum(rubric[name] for name in met),
                    "span_validated_points": sum(rubric[name] for name in valid),
                    "extra_met_vs_review": sorted(valid - target),
                    "missing_met_vs_review": sorted(target - valid),
                    "invalid_span_criteria": sorted(met - valid),
                    "judge_release_failures": faults,
                    "release_failures_with_exact_spans": valid_faults,
                    "review_release_failures": reviewed[key]["failures"],
                    "review_release_uncertain": reviewed[key]["release_uncertain"],
                })
        comparison[key] = case
    return {"verified_judgments": len(verified), "candidates": comparison}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    if parser.parse_args().compact:
        import judge_compact
        study = judge_compact
    else:
        study = judge
    print(json.dumps(run(study), indent=2, ensure_ascii=False))
