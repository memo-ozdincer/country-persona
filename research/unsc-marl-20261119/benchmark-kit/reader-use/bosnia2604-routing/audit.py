"""Verify case provenance, reconstruct the run and score verbatim span marks."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

from run import ARMS, HERE, PROTOCOL, episode, pins, runner

EVIDENCE = HERE / "evidence"


def read(path):
    return json.loads(path.read_text())


def provenance(root):
    import pyarrow.parquet as pq

    protocol = read(PROTOCOL)
    event = protocol["event"]
    m = read(root / "data/manifests/unbench-full-20260926.json")
    base = root / m["extraction_root"]
    manifest = read(root / "data/manifests/unsc-bench-20260926.json")
    parquet = root / manifest["local_root"] / "adopted/data.parquet"
    assert runner.digest(parquet) == next(f["sha256"] for f in manifest["files"] if f["path"] == "adopted/data.parquet")
    row = pq.ParquetFile(parquet).read().slice(event["unsc_index"], 1).to_pylist()[0]
    assert (row["identifiers"]["symbol"], row["dates"]["vote_date"], row["meeting"]["meeting_record"],
            row["draft_from_file1"]["draft_symbol"]) == (
                event["resolution"], event["date"], event["meeting"], event["draft"]
    )
    assert row["urls_meeting"]["en"] == protocol["sources"]["meeting"]
    assert row["urls_resolution"]["en"] == protocol["sources"]["resolution"]
    with (base / "task2_test_author.csv").open(encoding="utf-8-sig", newline="") as f:
        matches = [(i, r) for i, r in enumerate(csv.DictReader(f)) if r["Original_id"] == event["unbench_event"]]
    with (base / "task2_train_author.csv").open(encoding="utf-8-sig", newline="") as f:
        assert all(r["Original_id"] != event["unbench_event"] for r in csv.DictReader(f))
    assert len(matches) == 15 and {r["Date"] for _, r in matches} == {event["date"]}
    draft = base / "drafts_adopted" / event["unbench_event"] / (event["draft"].replace("/", "_") + "-EN.json")
    votes = {r["Country"].upper(): r["Voting"] for _, r in matches}
    assert set(votes.values()) == {"Y"} and votes == {r["name"].upper(): r["vote"] for r in row["member_state_votes"]}
    return {"event": event, "unbench_author_test_rows": [i for i, _ in matches], "votes": votes,
            "unbench_draft": str(draft.relative_to(root)), "unbench_draft_sha256": runner.digest(draft),
            "unsc_revision": manifest["revision"], "sources": protocol["sources"]}


def masked(key):
    return sha256(("bosnia2604-routing/" + key).encode()).hexdigest()[:10]


def get_rows():
    return {r["id"]: r for r in map(json.loads, (EVIDENCE / "transcript.jsonl").read_text().splitlines())}


def deck(rows):
    return dict(sorted((masked(key), r["output"]) for key, r in rows.items() if key.endswith("/final")))


def score(rows):
    from transformers import AutoTokenizer

    launch, complete = (read(EVIDENCE / x) for x in ("launch.json", "complete.json"))
    assert launch["sha256"] == pins()
    for name in ("transcript", "final_records"):
        filename = name.replace("_", "-") + (".jsonl" if name == "transcript" else ".json")
        assert complete[f"{name}_sha256"] == runner.digest(EVIDENCE / filename)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    seen = set()

    def replay(batch):
        result = {}
        for request in batch:
            key = request["id"]
            record = rows[key]
            assert key not in seen and all(record[k] == v for k, v in request.items())
            assert runner.encode(tokenizer, request) == record["input_ids"]
            tokens = record["output_ids"]
            assert 0 < len(tokens) <= request["cap"] and eos not in tokens[:-1]
            assert (tokens[-1] == eos) == record["ended"]
            assert tokenizer.decode(tokens, skip_special_tokens=True).strip() == record["output"]
            seen.add(key)
            result[key] = record
        return result

    restored, = episode(replay)
    assert seen == rows.keys() and len(seen) == complete["records"] == 12
    assert read(EVIDENCE / "final-records.json") == {restored["family"]: {k: r["output"] for k, r in restored["final"].items()}}
    marks = read(HERE / "marks.json")
    assert marks.keys() == deck(rows).keys()
    protocol = read(PROTOCOL)
    rubric = {key: weight for key, weight, _ in protocol["rubric"]}
    output = {}
    for arm in ARMS:
        key = f"{arm}/final"
        row = rows[key]
        mark = marks[masked(key)]
        assert set(mark["spans"]) == rubric.keys()
        assert set(mark["uncertain"]) <= {k for k, spans in mark["spans"].items() if not spans}
        assert set(mark["failures"]) | mark["release_uncertain"].keys() <= set(protocol["release_failures"])
        assert "failure_span" not in mark or mark["failure_span"] in row["output"]
        assert all(spans and all(span in row["output"] for span in spans) or spans == []
                   for spans in mark["spans"].values())
        steps = [f"{'pooled' if arm == 'solo' else 'local'}/{i}" for i in range(2)] + [f"{arm}/followup", key]
        words = len(row["output"].split())
        assert (words > 120) == ("more than 120 words" in mark["failures"])
        output[arm] = {
            "material_points": sum(rubric[k] for k, spans in mark["spans"].items() if spans),
            "points_if_uncertain_credit": sum(rubric[k] for k, spans in mark["spans"].items()
                                              if spans or k in mark["uncertain"]),
            "release": not (mark["failures"] or mark["release_uncertain"]),
            "failures": mark["failures"], "release_uncertain": mark["release_uncertain"], "words": words,
            "input_tokens": sum(len(rows[s]["input_ids"]) for s in steps),
            "output_tokens": sum(len(rows[s]["output_ids"]) for s in steps),
            "capped_calls": [s for s in steps if not rows[s]["ended"]],
        }
    process = read(HERE / "process-marks.json")
    for key, notes in process["opening_criteria"].items():
        assert notes.keys() <= rubric.keys()
        assert all(span in rows[key]["output"] for span in notes.values())
    for item in process["interactions"]:
        assert item["criterion"] in rubric
        for stage in ("followup", "final"):
            span = item[f"{stage}_span"]
            assert span is None or span in rows[f"{item['arm']}/{stage}"]["output"]
    return {"verified_model_calls": len(seen), "verified_process_interactions": len(process["interactions"]),
            "paths": output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("provenance", "deck", "score"))
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    result = provenance(args.root) if args.action == "provenance" else {"deck": deck, "score": score}[args.action](get_rows())
    print(json.dumps(result, indent=2, ensure_ascii=False))
