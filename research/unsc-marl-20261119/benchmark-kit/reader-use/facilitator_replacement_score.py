"""Score disposition, supported drafting and release separately for paired facilitator briefs."""
import argparse
import json
from pathlib import Path
import re
from collections import Counter

import facilitator_replacement as study

IDS = re.compile(r"\[([A-Za-z0-9-]+)\]")


def required(row):
    return {sid for sid, relation in row["source_relations"].items() if relation != "unknown"}


def score(directory):
    raw = study.replay(directory)
    labels = study.prior.delivery.load(directory / "annotations.json")
    assert labels["transcript_sha256"] == study.runner.digest(directory / "transcript.jsonl")
    assert raw.keys() == labels["rows"].keys()
    items = study.prior.inputs()
    results = {}
    for arm in study.ARMS:
        records = []
        for case, answer in zip(items["inputs"], items["keys"], strict=True):
            key = f"{case['id']:02}/{arm}"
            row = raw[key]
            annotation = labels["rows"][key]
            text = row["output"]
            head, mark, brief = text.partition("|")
            action_match = re.match(r"(retain|revise|withhold)\b", text, re.IGNORECASE)
            decision = action_match.group(1).casefold() if action_match else None
            brief = brief.strip()
            format_ok = bool(mark and head.strip().casefold() == decision and len(brief.split()) <= 48 and brief
                             and "\n" not in brief and row["ended"])
            preserved = annotation["preserved"]
            needs = required(answer)
            assert preserved.keys() <= case["sources"].keys()
            assert all(s in text and s for s in preserved.values())
            assert all(span and span in text and why for span, why in annotation["issues"])
            ids = set(IDS.findall(brief))
            cited_positions = needs | set(annotation.get("additional_citations_needed", []))
            assert cited_positions <= case["sources"].keys()
            source_clear = not annotation["issues"] and ids <= case["sources"].keys()
            attribution_complete = needs <= preserved.keys() and cited_positions <= ids
            evidence_limits_clear = annotation["limits_clear"]
            strict = (format_ok and decision == answer["decision"] and source_clear
                      and attribution_complete and evidence_limits_clear)
            records.append({"id": case["id"], "proposed": case["proposed_sentence"], "expected": answer["decision"],
                            "decision": decision, "brief": brief, "format_ok": format_ok,
                            "disposition_right": decision == answer["decision"], "known_sides_required": sorted(needs),
                            "known_sides_preserved": preserved, "ids": sorted(ids), "issues": annotation["issues"],
                            "limits_clear": evidence_limits_clear, "source_clear": source_clear,
                            "attribution_complete": attribution_complete, "strict": strict,
                            "output_tokens": len(row["output_ids"])})
        counts = Counter()
        for item in records:
            for k in ("format_ok", "disposition_right", "source_clear", "attribution_complete", "limits_clear", "strict"):
                counts[k] += item[k]
            counts["retain_with_wrong_disposition"] += item["decision"] == "retain" and item["expected"] != "retain"
            counts["retain_without_release_support"] += item["decision"] == "retain" and (
                item["expected"] != "retain" or not item["source_clear"] or not item["attribution_complete"])
        by_required = {name: {"cases": sum(r["expected"] == name for r in records),
                              "strict": sum(r["expected"] == name and r["strict"] for r in records)}
                       for name in study.prior.ACTIONS}
        replay = {}
        for roster in ("overlap", "split"):
            for peer in (True, False):
                probs = study.prior.delivery.exact_receipt_probabilities(roster, peer)
                replay[f"{roster}/{'visible' if peer else 'erased'}"] = {
                    "strict": sum(probs[r["id"] % 4] / 6 for r in records if r["strict"]),
                    "valid_published_replacement": sum(probs[r["id"] % 4] / 6 for r in records
                                                       if r["strict"] and r["expected"] == "retain"),
                    "valid_contradiction_replacement": sum(probs[r["id"] % 4] / 6 for r in records
                                                           if r["strict"] and r["expected"] == "revise")}
        citation_only = [r["id"] for r in records if r["format_ok"] and r["disposition_right"]
                         and r["source_clear"] and r["limits_clear"] and not r["strict"]
                         and set(r["known_sides_required"]) <= r["known_sides_preserved"].keys()]
        results[arm] = {"counts": dict(counts), "by_required": by_required, "replay": replay,
                        "citation_only_failures": citation_only, "records": records}
    return {"review": labels["scope"], "arms": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
