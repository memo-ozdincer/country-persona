"""Verify exact-span reviews and replay both UNIFIL writers through frozen routes."""
from itertools import combinations
import json
from pathlib import Path
import re
import sys

import receipt_outcomes as compare
import unifil_field_transfer as experiment

roster = experiment.roster
HERE = experiment.HERE
CITATION = re.compile(r"\[([a-z]+(?:, [a-z]+)*)\]")


def passages(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def measure(rows, labels, ids, ideal):
    cards, _, _, public, _, _ = experiment.dossier()
    assert set(labels) == set(rows)
    for key, row in rows.items():
        held = frozenset(row["evidence_ids"])
        review = labels[key]
        text = row["output"]
        fields = review["met"]
        assert fields.keys() <= ideal[held]["licensed_by"].keys() - {"procedure", "disposition"}
        assert all(spans and all(evidence and evidence in text for evidence in spans) for spans in fields.values())
        assert all(flaw["span"] and flaw["span"] in text and flaw["reason"] for flaw in review["issues"])
    banks = {"whole": {}, "fields": {}}
    for size in range(1, 4):
        for packet in combinations(ids, size):
            key = frozenset(packet)
            expected = list(packet) + (["comparison"] if experiment.COMPARE <= key else [])
            for name, parts in (("whole", ["whole/" + ",".join(sorted(key))]),
                                ("fields", ["field/" + p for p in expected])):
                body = "\n\n".join(rows[p]["output"] for p in parts)
                assert all(cards[card] not in public for card in packet)
                issues = [error for p in parts for error in labels[p]["issues"]]
                seen = {"procedure": [public], "disposition": [public]}
                for part in parts:
                    seen.update(labels[part]["met"])
                licensed = ideal[key]["licensed_by"]
                assert seen.keys() <= licensed.keys()
                paragraphs = passages(body)
                expected_tags = [sorted(experiment.COMPARE if part == "comparison" else {part}) for part in expected]
                tags = [[tag for group in CITATION.findall(p) for tag in group.split(", ")] for p in paragraphs]
                form = (tags == expected_tags
                        and all(len(CITATION.sub("", p).split()) <= (25 if f == "comparison" else 36)
                                for p, f in zip(paragraphs, expected)))
                ended = all(rows[p]["ended"] for p in parts)
                banks[name][key] = {
                    "record": public + "\n\n" + body, "evidence_spans": seen, "issues": issues,
                    "points": 7 * len(seen), "licensed_points": ideal[key]["record_points"],
                    "complete": ended, "source_guard_clear": not issues, "form_clear": form,
                    "releasable": ended and not issues and form and seen.keys() == licensed.keys(),
                    "writer_input_tokens": sum(len(rows[p]["input_ids"]) for p in parts),
                    "writer_output_tokens": sum(len(rows[p]["output_ids"]) for p in parts),
                    "writer_calls": len(parts),
                }
    return banks


def outcomes(ids, ideal, mapping, banks):
    old = roster.actor_policy()
    fit = roster.transfer.read(HERE / "specialist-fit-results.json")
    fit = {roster.transfer.immutable(r["local_state"]): r["probabilities"] for r in fit["policy"]}
    ids_to_context = {(r["anchor"], *r["other_cards"]): r for r in mapping["rows"]}
    rows = {name: [] for name in banks}
    for target, anchor in roster.relay.SCENARIOS:
        pending = sorted(set(target) - {anchor})
        context = ids_to_context[(ids[anchor], *(ids[i] for i in pending))]
        prior = roster.distribution(pending, *roster.CONDITIONS["strong_specialist_B"])
        routed = {
            "original": roster.remap(old, prior, target, anchor, context, (0, 1)),
            "joint": roster.remap(fit, prior, target, anchor, context, (1, 0)),
            "canonical_reply": roster.remap(fit, prior, target, anchor, context, (1, 0), True),
            "fixed_script": compare.script(target, anchor, ids, ideal, prior, False),
            "adaptive_script": compare.script(target, anchor, ids, ideal, prior, True),
            "pooled": {frozenset(): (1., 0., 0.)},
        }
        for name, bank in banks.items():
            scores = {route: compare.metrics(target, anchor, ids, dist, bank, ideal)
                      for route, dist in routed.items()}
            for entry in scores.values():
                receipts = [(frozenset(packet.split(",")), weight)
                            for packet, weight in entry["packet_probabilities"].items()]
                entry["metrics"]["writer_calls"] = sum(bank[packet]["writer_calls"] * mass
                                                        for packet, mass in receipts)
                entry["metrics"]["full_target_release_probability"] = sum(
                    mass for packet, mass in receipts if len(packet) == len(target) and bank[packet]["releasable"]
                )
            rows[name].append(scores)
    audit = roster.transfer.read(HERE / "specialist-script-results.json")["families"]["unifil"]["strong_specialist_B"]
    out = {}
    for name, suite in rows.items():
        mean = roster.transfer.mean([{route: row["metrics"] for route, row in item.items()} for item in suite])
        for route, field in (("fixed_script", "known_prior_fixed"), ("adaptive_script", "known_prior_adaptive")):
            assert abs(mean[route]["net_gain_over_verified_anchor"] - audit["stronger_scripts"][field]) < 1e-9
        assert abs(mean["joint"]["net_gain_over_verified_anchor"] - audit["trained_joint"]) < 1e-9
        out[name] = {"mean": mean, "rows": suite}
    return out


def run(directory):
    trace = experiment.replay(directory)
    reviews = json.loads((directory / "annotations.json").read_text())
    assert reviews["transcript_sha256"] == experiment.runner.digest(directory / "transcript.jsonl")
    _, ids, ideal, mapping = next(row for row in roster.datasets() if row[0] == "unifil")
    banks = measure(trace, reviews["records"], ids, ideal)
    return {
        "review": "Same-assistant exact-span review. The authored public vote prefix is shared. "
                  "Only packet receipts with all licensed facts and the requested form can be released.",
        "routes": outcomes(ids, ideal, mapping, banks),
        "packets": {mode: {",".join(sorted(key)): row for key, row in bank.items()} for mode, bank in banks.items()},
    }


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), ensure_ascii=False, indent=2))
