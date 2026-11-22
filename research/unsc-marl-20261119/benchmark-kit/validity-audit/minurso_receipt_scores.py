"""Score receipt-aware candidate records and compare frozen communication with silence."""
import argparse
from itertools import product
import json
from pathlib import Path
import re
import sys

import numpy as np

from duplicate_card_noisy_reader_fit import ANNOUNCEMENTS, compile_table, optimize, values
from duplicate_card_routes import exact
from duplicate_card_semantic_review import EVIDENCE, MASKS, MESSAGE_COST, RECEIPT, SIGNAL_COST, digest, mask_weight
from minurso_receipt_writer import HEADINGS, JUDGE, case, locks, requests

sys.path.insert(0, str(JUDGE.parent))
from score import score
sys.path.pop(0)

# Public summaries establish the proposals and vote outcomes. The national
# explanations and attribution require their national evidence cards.
PRIVATE_GROUPS = {"reservation": 1, "national_capacity": 2}
VALID_IDS = re.compile(r"\[(?:[A-Za-z]+(?:-[A-Za-z]+)?)(?:\s*[,;]\s*[A-Za-z]+(?:-[A-Za-z]+)?)*\]")
NO_SIGNAL = (ANNOUNCEMENTS[0],) * 2
PRIVATE = np.array(list(product(range(4), repeat=2)))


def citation_ids(text):
    return {key for match in VALID_IDS.findall(text) for key in re.split(r"\s*[,;]\s*", match[1:-1])}


def read(directory, annotations):
    trace = directory / "transcript.jsonl"
    end = json.loads((directory / "complete.json").read_text())
    start = json.loads((directory / "launch.json").read_text())
    assert end["transcript_sha256"] == digest(trace) == annotations["transcript_sha256"]
    assert start["sha256"] == locks()
    records = list(map(json.loads, trace.read_text().splitlines()))
    assert len(records) == end["records"] == 4
    final = directory / "final-records.json"
    assert end["final_records_sha256"] == digest(final)
    assert next(iter(json.loads(final.read_text()).values())) == {r["id"]: r["output"] for r in records}
    for row, request in zip(records, requests(), strict=True):
        assert all(row[k] == v for k, v in request.items())
    return records


def add_readout(directory, annotations):
    groups = json.loads(JUDGE.read_text())["groups"]
    rubrics = {p["id"]: (p, PRIVATE_GROUPS.get(g["id"], 0)) for g in groups for p in g["parts"]}
    rubric = [{"id": k, "criterion": p["criterion"], "category": "final", "weight": p["weight"]}
              for k, (p, _) in rubrics.items()]
    source = case()
    blocks = {**source["docket"], **{key: v for g in source["delegate_evidence"].values() for key, v in g.items()}}
    archive = read(directory, annotations)
    assert set(annotations["rows"]) == {r["id"] for r in archive}
    out = []
    for mask, row in enumerate(archive):
        review = annotations["rows"][row["id"]]
        text = row["output"]
        allowed = set(row["evidence_ids"])
        met = review["met"]
        assert met.keys() <= rubrics.keys()
        units = []
        for key, (part, required) in rubrics.items():
            response, cites = met.get(key, ("", []))
            assert all(c in part["blocks"] and c in allowed for c in cites)
            assert not response or not required or mask & required
            units.append({"id": key, "status": "met" if key in met else "unmet",
                          "response": response, "reason": "Exact reviewed coverage." if key in met else
                          "Incomplete, incorrect, or outside the delivered view.",
                          "source": [{"block": c, "quote": blocks[c]} for c in cites]})
        guard = review["guard"]
        packet = {"id": row["id"], "mode": "FINAL", "task": "Score the actually delivered evidence only.",
                  "rubric": rubric, "answer": text, "evidence": [{"id": k, "text": blocks[k]} for k in sorted(allowed)]}
        reported = score(packet, {"id": row["id"], "units": units, "guard": guard})
        word_count = len(text.split())
        unknown = sorted(citation_ids(text) - allowed)
        finished = row["ended"] and word_count <= 155
        earned = reported["final"]["lower"]
        cite_misses = [k for k, (span, evidence) in met.items() if not any(
            citation_ids(line).intersection(evidence) for line in text.splitlines() if span in line)]
        heading_names = re.findall(r"^\s*(?:[-*]|\d+\.)?\s*\**([A-Za-z]+)\**\s*:",
                                   text, flags=re.MULTILINE)
        ceiling = sum(p["weight"] for p, needed in rubrics.values() if not needed or mask & needed)
        eligible = finished and guard["status"] == "clear" and not unknown
        out.append({"mask": mask, "id": row["id"], "raw_points": earned, "met": sorted(met),
                    "reference_ceiling": ceiling,
                    "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"]),
                    "guard": reported["guard"], "words": word_count, "ended": row["ended"],
                    "missing_citations_on_met_parts": sorted(cite_misses), "off_packet_citations": unknown,
                    "headings": heading_names, "headings_exact": heading_names == list(HEADINGS),
                    "strict_for_packet": eligible and earned == ceiling and not cite_misses
                    and heading_names == list(HEADINGS),
                    "eligible_points": earned if eligible else 0})
    return out


def matrix_by_loss(points, loss):
    reward = np.zeros((3, 3))
    for keep in MASKS:
        delivered = np.bitwise_or.outer(np.arange(3) * keep[0], np.arange(3) * keep[1])
        reward += mask_weight(keep, loss) * np.asarray(points)[delivered]
    return reward - MESSAGE_COST * np.add.outer([0, 1, 1], [0, 1, 1])


def play(table, prior, points, loss):
    left, right = PRIVATE.T
    a, b = table[0, left, 0], table[1, right, 0]
    gross = receipt = bills = 0.
    for seen in MASKS:
        x = table[0, left, 1 + 2 * a + b * seen[0]]
        y = table[1, right, 1 + 2 * b + a * seen[1]]
        assert np.all(x & left == x) and np.all(y & right == y)
        frequency = mask_weight(seen, loss)
        bills += frequency * (prior @ ((x != 0).astype(int) + (y != 0)))
        for keep in MASKS:
            delivered = (x * keep[0]) | (y * keep[1])
            mass = frequency * mask_weight(keep, loss) * prior
            gross += mass @ np.asarray(points)[delivered]
            receipt += mass @ (delivered == 3)
    announcements = prior @ (a + b)
    return {"net": float(gross - MESSAGE_COST * bills - SIGNAL_COST * announcements),
            "record_points": float(gross), "both_receipts": float(receipt),
            "mean_deliveries": float(bills), "mean_announcements": float(announcements)}


def rollout(receipts):
    raw = [r["raw_points"] for r in receipts]
    valid = [r["eligible_points"] for r in receipts]
    ceiling = [r["reference_ceiling"] for r in receipts]
    table_dir = EVIDENCE
    buffer = np.asarray(json.loads((table_dir / "buffered-fit.json").read_text())["trained_tables"]["matched"])
    suite = json.loads((table_dir / "outcome-policy.json").read_text())["training"]
    new = np.asarray(suite["tables"][list(suite["profiles"]).index("both_useful")])
    prior_data = json.loads((table_dir / "dprk-routes.json").read_text())["arms"]
    variations = []
    for label, source, loss in product(("guarded_actual", "raw_actual", "reference_ceiling"), prior_data, (0., .1, .25)):
        prior = np.array([r["probability"] for r in prior_data[source]["silent"]["worlds"]])
        points = {"guarded_actual": valid, "raw_actual": raw, "reference_ceiling": ceiling}[label]
        matrix = matrix_by_loss(points, loss)
        case = (prior, prior[:, None, None] * matrix, loss)
        opt, silent = optimize([case])
        quiet = values(*case, NO_SIGNAL)
        silent_pair = np.unravel_index(quiet.argmax(), quiet.shape)
        arms = {"frozen_buffer": buffer, "frozen_additive": new,
                "optimal_silence": compile_table(NO_SIGNAL, silent_pair),
                "optional_ceiling": opt["mean"]["table"]}
        evaluated = {k: play(t, prior, points, loss) for k, t in arms.items()}
        assert np.isclose(evaluated["optimal_silence"]["net"], silent[0])
        assert np.isclose(evaluated["optional_ceiling"]["net"], opt["mean"]["objective"])
        if loss == 0:
            direct = exact(prior, matrix, SIGNAL_COST)
            assert np.isclose(evaluated["optional_ceiling"]["net"], direct["optional"][0])
        assert all(r["net"] <= evaluated["optional_ceiling"]["net"] + 1e-9 for r in evaluated.values())
        variations.append({"reward": label, "prior": source, "loss": loss, "arms": evaluated})
    return variations


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("annotations", type=Path)
    args = cli.parse_args()
    data = json.loads(args.annotations.read_text())
    receipts = add_readout(args.directory, data)
    print(json.dumps({"scope": data["scope"], "transcript_sha256": data["transcript_sha256"],
                      "annotations_sha256": digest(args.annotations),
                      "receipts": receipts, "rollout": rollout(receipts)}, indent=2))
