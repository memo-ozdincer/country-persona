"""Check whether UNSC-Bench closes measured gaps in the UNBench release."""
import argparse
from collections import Counter
import json
from pathlib import Path

import pyarrow.parquet as pq
from country_persona.io import digest, sha256, write_json
from country_persona.unsc_bench import TARGETS, normalize_record


def audit(root, unbench_root):
    records, configs = [], {}
    for config in ("adopted", "vetoed"):
        path = root / config / "data.parquet"
        rows = pq.read_table(path).to_pylist()
        configs[config] = {"rows": len(rows), "sha256": sha256(path)}
        records.extend(normalize_record(row, config, index) for index, row in enumerate(rows))
    coverage = {}
    for country, code in TARGETS.items():
        views = [(r, v) for r in records for v in r["votes"] if v["country"] == country]
        coverage[code] = {
            "all_years": dict(Counter(v["vote"] for _, v in views)),
            "since_1990": dict(Counter(v["vote"] for r, v in views if r["date"] >= "1990-01-01")),
            "since_1990_without_detected_conflicts": dict(Counter(v["vote"] for r, v in views if r["date"] >= "1990-01-01" and not r["issues"])),
            "negative_events": [{k: r[k] for k in ("date", "draft_symbol", "config", "row_index", "record_url")} for r, v in views if v["vote"] == "N"],
        }
    # Folder IDs cannot be compared across collections. Use source symbols and
    # exact whitespace-normalized text; this is only a lower bound on overlap.
    ub_symbols, ub_texts = set(), set()
    for path in unbench_root.glob("*/*/*EN.json"):
        row = json.loads(path.read_text())
        if row.get("ID"):
            ub_symbols.add(row["ID"].strip().upper())
        ub_texts.add(digest(" ".join(row["Content"].split())))
    repeated = Counter(r["draft_symbol"] for r in records if r["draft_symbol"])
    report = {
        "schema_version": 1, "configs": configs, "events": len(records),
        "all_country_vote_rows": sum(len(r["votes"]) for r in records),
        "target_coverage": coverage,
        "quality_issues": [{k: r[k] for k in ("config", "row_index", "draft_symbol", "issues")} for r in records if r["issues"]],
        "issue_counts": dict(Counter(issue for r in records for issue in r["issues"])),
        "duplicate_draft_symbols": {k: v for k, v in repeated.items() if v > 1},
        "unbench_overlap_lower_bound": {
            "events_with_same_draft_symbol": sum(bool(r["draft_symbol"] and r["draft_symbol"].strip().upper() in ub_symbols) for r in records),
            "events_with_same_exact_normalized_text": sum(digest(" ".join((r["draft_text"] or "").split())) in ub_texts for r in records)},
        "limitations": ["Country casing and two explicitly listed name aliases normalized; historical states are not merged.",
                        "English draft text is available but not cleared for OCR, version or outcome leakage.",
                        "Do not use resolution_text, meeting_text, summaries or votes in prediction prompts.",
                        "Translations are not assumed independently verified or equivalent to their English source.",
                        "No semantic event-family split, time-cutoff audit or primary-record label verification is complete.",
                        "Country/year/class-selected examples are diagnostic challenge data, not a natural-prevalence test."]}
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--unbench-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.root, args.unbench_root)
    write_json(args.output, report)
    print(json.dumps(report, indent=2))
