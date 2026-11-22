"""Replay quote-backed partial credit and judge error-localization probes."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

from minurso_atomic_judge import ANCHORS, SELECTED, fixtures, hashes, observations, rubric
from score import score

EVIDENCE = ANCHORS.parent.parent / "evidence"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def manual(annotations):
    groups, parts = rubric()
    result = {}
    for run_name, entries in annotations["runs"].items():
        root = EVIDENCE / run_name
        prior = json.loads((root / "score.json").read_text())
        saved = json.loads((root / "review.json").read_text())
        key = json.loads((root / "judge-key.json").read_text())
        deck = json.loads((root / "judge-packets.json").read_text())
        serialized = json.dumps(deck, sort_keys=True, ensure_ascii=False).encode()
        assert key["judge_packets_sha256"] == sha256(serialized).hexdigest()
        assert key["transcript_sha256"] == digest(root / "transcript.jsonl")
        old = {a["id"]: a["guard"] for a in saved["final"]}
        arms = {}
        for packet in deck["packets"]:
            id_ = packet["id"]
            arm = key["key"][id_]
            row = entries[arm]
            assert row.keys() <= parts.keys()
            evidence = {x["id"]: x["text"] for x in packet["evidence"]}
            units = []
            for part_id, part in parts.items():
                label, span, why = row.get(part_id, ["omitted", "", "This required fact is not stated."])
                assert label in ("met", "omitted", "contradiction", "uncertain")
                assert label in ("met", "omitted") or span
                status = {"omitted": "unmet", "contradiction": "unmet"}.get(label, label)
                units.append({"id": part_id, "status": status, "response": span, "reason": why,
                              "source": [{"block": b, "quote": evidence[b]} for b in part["blocks"]]})
            spec = [{"id": p["id"], "category": "final", "weight": p["weight"],
                     "criterion": p["criterion"]} for p in parts.values()]
            grade = score({**packet, "rubric": spec}, {"id": id_, "units": units, "guard": old[id_]})
            obs = key["diagnostics"][id_]
            assert grade["guard"] == prior["final"][arm]["guard"]
            arms[arm] = {"compound": prior["final"][arm]["final"], "by_part": grade["final"],
                         "groups": {g["id"]: sum(p["weight"] for p in g["parts"]
                                     if row.get(p["id"], ["omitted"])[0] == "met") for g in groups},
                         "states": dict(Counter(row.get(part_id, ["omitted"])[0] for part_id in parts)),
                         "guard": grade["guard"],
                         "strict": grade["strict"] and obs["ended"] and obs["words"] <= 155}
        result[run_name] = arms
    return {"scope": annotations["scope"], "results": result}


def read_model(directory, locked, prompts):
    path = directory / "actions.jsonl"
    end = json.loads((directory / "complete.json").read_text())
    start = json.loads((directory / "launch.json").read_text())
    assert end["sha256"] == digest(path) and start["sha256"] == locked
    records = list(map(json.loads, path.read_text().splitlines()))
    keyed = {tuple(r["observation"]): r for r in records}
    prompts = list(prompts)
    assert len(records) == len(keyed) == end["records"] == len(prompts)
    for probe in prompts:
        row = keyed[probe["observation"]]
        assert row["legal"] == list(probe["legal"]) and row["messages"] == probe["messages"]
        assert len(row["scores"]) == len(row["legal"]) and all(map(isfinite, row["scores"]))
    return keyed


def pick(row):
    labels = [label for label, logit in zip(row["legal"], row["scores"], strict=True)
              if logit == max(row["scores"])]
    return labels[0] if len(labels) == 1 else None


def summary(directory):
    keyed = read_model(directory, hashes(), observations())
    outcomes = []
    for name, _, authored in fixtures():
        for part in SELECTED:
            decisions = [pick(keyed[name, part, index]) for index in range(2)]
            expected = authored.get(part, 1)
            # The first deletion leaves an independent mention in the reason sentence.
            if name == "anchor-omitted" and part == "nonparticipation":
                expected = 1
            outcomes.append({"candidate": name, "part": part, "truth": expected,
                             "fixture_label": authored.get(part, 1), "choices": decisions})
    return {"scope": "Exposed authored contrasts. The supported answer remains B in both orders. "
                     "One recorded omission foil retains a later supporting mention and is adjudicated locally.",
            "actions_sha256": digest(directory / "actions.jsonl"),
            "total": len(outcomes),
            "correct_both": sum(r["choices"] == [r["truth"]] * 2 for r in outcomes),
            "agreed_supported": sum(r["choices"] == [1, 1] for r in outcomes),
            "supported_position_baseline": sum(r["truth"] == 1 for r in outcomes),
            "contradictions_both": sum(r["truth"] == 2 and r["choices"] == [2, 2] for r in outcomes),
            "contradictions_total": sum(r["truth"] == 2 for r in outcomes),
            "contradictions_unanimously_accepted": sum(r["truth"] == 2 and r["choices"] == [1, 1]
                                                        for r in outcomes),
            "outcomes": outcomes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("manual", "model"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    result = manual(json.loads(args.path.read_text())) if args.mode == "manual" else summary(args.path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
