"""Verify the run and make judge packets with no experimental condition in the final packets."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import source_record_episode as scenario
from source_record_minurso import JUDGE, PACK, locks
from source_record_run import digest, encode

sys.path.insert(0, str(JUDGE.parent))
from score import score

TASK = json.loads(PACK.read_text())
CASE, = TASK["cases"]


def source_blocks():
    dicts = [CASE["docket"], *CASE["delegate_evidence"].values()]
    return [{"id": key, "text": text, "location": CASE["sources"][key]}
            for group in dicts for key, text in group.items()]


def final_packet(id_, answer):
    return {"id": id_, "mode": "FINAL",
            "task": TASK["protocol"]["shared_task"] + " " + CASE["guard"],
            "evidence": source_blocks(), "rubric": CASE["rubric"], "answer": answer}


def json_digest(obj):
    return sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def anchors():
    ref = CASE["reference"]
    foils = (
        ("nonparticipation", "Algeria did not participate [MAIN].", "Algeria abstained [MAIN].", "adoption"),
        ("amendment", "S/2024/798, to consider expanding MINURSO for rights monitoring, failed 5–0–10",
         "S/2024/798, to consider expanding MINURSO for rights monitoring, passed 5–0–10", "amendments"),
        ("capacity", "Speaking nationally, Baeriswyl said Switzerland",
         "The Council, speaking through Baeriswyl,", "national_capacity"),
        ("authority", "It did not add the monitoring functions [TEXT].",
         "It added the monitoring functions [TEXT].", "authority"),
    )
    result = [{"packet": final_packet("anchor-base", ref), "expected": {"guard": "clear", "lower": 70}}]
    for name, original, changed, dimension in foils:
        assert ref.count(original) == 1
        result.append({"packet": final_packet(f"anchor-{name}", ref.replace(original, changed)),
                       "expected": {"guard": "failed", "lower": 56, "unmet": dimension}})
    return result


def verified_episode(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    path = directory / "transcript.jsonl"
    assert launch["sha256"] == locks() and complete["transcript_sha256"] == digest(path)
    rows = list(map(json.loads, path.read_text().splitlines()))
    by_id = {row["id"]: row for row in rows}
    assert len(by_id) == len(rows) == complete["records"] == 13
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")

    def reuse(batch):
        verified = {}
        for request in batch:
            row = by_id.pop(request["id"])
            assert all(row[k] == json.loads(json.dumps(val)) for k, val in request.items())
            assert encode(tokenizer, request) == row["input_ids"]
            out = row["output_ids"]
            assert 0 < len(out) <= request["cap"] and eos not in out[:-1]
            assert tokenizer.decode(out, skip_special_tokens=True).strip() == row["output"]
            assert (out[-1] == eos) == row["ended"]
            verified[row["id"]] = row
        return verified

    with patch.object(scenario, "PACK", PACK):
        item, = scenario.episode(reuse)
    assert not by_id
    finals = directory / "final-records.json"
    assert complete["final_records_sha256"] == digest(finals)
    assert json.loads(finals.read_text()) == {item["family"]: {k: v["output"] for k, v in item["final"].items()}}
    return item, complete["transcript_sha256"]


def decks(directory):
    item, seal = verified_episode(directory)
    packets, key, diagnostics = [], {}, {}
    name = item["family"]
    for id_, row in item["final"].items():
        _, arm, _ = id_.split("/")
        opaque = sha256(f"{seal}/{id_}".encode()).hexdigest()[:16]
        packets.append(final_packet(opaque, row["output"]))
        key[opaque] = arm
        prefix = "pooled_solo" if arm == "pooled_solo" else "common"
        path = [row, *[r for k, r in item["openings"].items() if f"/{prefix}/" in k],
                *[r for k, r in item["revisions"].items() if f"/{arm}/" in k]]
        diagnostics[opaque] = {
            "calls": len(path), "ceiling": sum(r["cap"] for r in path),
            "input_tokens": sum(len(r["input_ids"]) for r in path),
            "output_tokens": sum(len(r["output_ids"]) for r in path),
            "ended": row["ended"], "words": len(row["output"].split()),
        }

    opportunities = []
    for role, peer in ((1, 2), (2, 1)):
        def text(kind, position, stage):
            return item[stage + "s"][f"{name}/{kind}/{stage}_{position}"]["output"]

        opportunities.append({
            "id": f"recipient-{role}",
            "peer": text("common", peer, "opening"), "opening": text("common", role, "opening"),
            "revision": text("interactive", role, "revision"),
            "solo_revision": text("independent_drafts", role, "revision"),
            "instruction": "Within the delivered opening, identify a material correction or transfer of evidence. "
                           "If the recipient only repeats prior facts or ignores the novel idea, withhold credit.",
        })
    mechanism = {"id": "paired-revisions", "mode": "MECHANISM", "task": TASK["protocol"]["shared_task"],
                 "evidence": source_blocks(), "opportunities": opportunities}
    deck = {"packets": sorted(packets, key=lambda p: p["id"]), "mechanism": mechanism}
    return deck, {
        "key": key, "diagnostics": diagnostics, "transcript_sha256": seal, "judge_packets_sha256": json_digest(deck),
    }


def consolidate(directory, review):
    deck = json.loads((directory / "judge-packets.json").read_text())
    ledger = json.loads((directory / "judge-key.json").read_text())
    assert ledger["transcript_sha256"] == digest(directory / "transcript.jsonl")
    assert ledger["judge_packets_sha256"] == json_digest(deck)
    verdicts = {v["id"]: v for v in review["final"]}
    assert len(verdicts) == len(review["final"]) == len(deck["packets"])
    result = {}
    for packet in deck["packets"]:
        id_ = packet["id"]
        value = score(packet, verdicts[id_])
        diag = ledger["diagnostics"][id_]
        result[ledger["key"][id_]] = {**value, **diag,
                                     "strict": value["strict"] and diag["ended"] and diag["words"] <= 155}
    return {"review_scope": review["scope"], "final": result,
            "mechanism": score(deck["mechanism"], review["mechanism"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("anchors", "deck", "score"))
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    if args.mode == "anchors":
        print(json.dumps(anchors(), indent=2, ensure_ascii=False))
    elif args.mode == "deck":
        deck, key = decks(args.directory)
        for file, content in (("judge-packets.json", deck), ("judge-key.json", key)):
            (args.directory / file).write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n")
    else:
        result = consolidate(args.directory, json.loads(args.review.read_text()))
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
