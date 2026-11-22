"""Review first-pass fields and whole-packet records on their admitted sources."""
from itertools import combinations
import json
from pathlib import Path
import re

import writer

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
CITE = re.compile(r"\[([A-Z0-9]+(?:, *[A-Z0-9]+)*)\]")


def load(path):
    return json.loads(path.read_text())


def source_index(case):
    return {name: frozenset(s.strip() for s in rule[0].split(",")) for name, rule in case["rules"].items()}


def verified_bank(case):
    names = list(case["sources"])
    reference = load(HERE / "reference.json")
    dependencies = source_index(case)
    bank = {}
    for size in range(5):
        for packet in combinations(names, size):
            arrived = {"VOTE", *packet}
            enabled = {key: sorted(srcs) for key, srcs in dependencies.items() if srcs <= arrived}
            parts = [case["public"], *(reference[key] for key in packet)]
            if "overlap" in enabled:
                parts.append(reference["overlap"])
            record = "\n\n".join(parts)
            assert len(record.split()) <= 185
            bank[frozenset(packet)] = {"record_points": 7 * len(enabled), "record": record, "proof": enabled}
    assert bank[frozenset(names)]["record_points"] == 70
    return bank


def checked(row, label, allowed):
    text = row["output"]
    cited = {key.strip() for match in CITE.findall(text) for key in match.split(",")}
    assert set(label["met"]) <= allowed
    assert all(spans and all(span in text for span in spans) for spans in label["met"].values())
    assert all(error["span"] in text and error["reason"] for error in label["guard_issues"])
    return {"text": text, "met": label["met"], "issues": label["guard_issues"], "ended": row["ended"],
            "cited": cited, "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"]),
            "cap": row["cap"]}


def compose(pieces, case, names, expected):
    seen = {"VOTE", *names}
    body = "\n\n".join([case["public"], *(item["text"] for item in pieces)])
    met = {"procedure": [case["public"]]}
    for item in pieces:
        assert not met.keys() & item["met"].keys()
        met.update(item["met"])
    for span in (x for spans in met.values() for x in spans):
        assert span in body
    assert met.keys() <= expected.keys()
    issues = [error for item in pieces for error in item["issues"]]
    cited = set.union({"VOTE"}, *(row["cited"] for row in pieces))
    per_field = all(item["cited"] <= seen and item["cited"] for item in pieces)
    words = len(body.split())
    complete = all(item["ended"] for item in pieces)
    release = not issues and words <= 185 and complete and cited == seen and per_field
    return {"record": body, "points": 7 * len(met), "available_points": 7 * len(expected), "words": words,
            "semantic_guard_clear": not issues, "cited_ids_clear": cited == seen and per_field,
            "complete": complete, "release": release, "all_delivered_criteria": met.keys() == expected.keys(),
            "met": met, "missing": sorted(expected.keys() - met.keys()), "guard_issues": issues,
            "calls": len(pieces), "input_tokens": sum(item["input_tokens"] for item in pieces),
            "output_tokens": sum(item["output_tokens"] for item in pieces),
            "sum_of_caps": sum(item["cap"] for item in pieces)}


def run():
    case = load(writer.CASE)
    rows = writer.replay(EVIDENCE)
    labels = load(HERE / "annotations.json")
    assert set(labels["records"]) == rows.keys()
    assert labels["transcript_sha256"] == writer.runner.digest(EVIDENCE / "transcript.jsonl")
    bank = verified_bank(case)
    actual = {}
    for name, row in rows.items():
        if name == "overlap":
            allowed = {"overlap"}
        elif name in case["sources"]:
            allowed = bank[frozenset({name})]["proof"].keys() - {"procedure"}
        else:
            allowed = bank[frozenset(row["evidence_ids"])]["proof"].keys() - {"procedure"}
        actual[name] = checked(row, labels["records"][name], allowed)

    packets = {}
    for packet, reference in bank.items():
        if not 1 <= len(packet) <= 3:
            continue
        enabled = [actual[i] for i in case["sources"] if i in packet]
        if "overlap" in reference["proof"]:
            enabled.append(actual["overlap"])
        packets[",".join(sorted(packet))] = compose(enabled, case, packet, reference["proof"])
    comparison = {}
    for label, members in writer.PACKETS.items():
        name = ",".join(sorted(members))
        comparative = compose([actual[label]], case, members, bank[frozenset(members)]["proof"])
        comparison[label] = {"separate_fields": packets[name], "whole_packet": comparative}
    return {"scope": "First-pass outputs on a new project docket. Same-assistant exact-span review, no "
                     "selection among field variants, and one previously authored public vote line per record.",
            "raw_fields": {name: {**obj, "cited": sorted(obj["cited"])} for name, obj in actual.items()},
            "field_packets": packets, "matched_receipts": comparison,
            "verified_bank": {",".join(sorted(ids)): ref for ids, ref in bank.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
