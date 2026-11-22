"""Diagnose relative ranking and threshold transfer using archived logits."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parents[1] / "judge/evidence/authority/archive-binary/format-audit.json"
VENEZUELA = HERE / "evidence/authority/metrics.json"


def midpoint(rows):
    highest_clear = max(margin for expected, margin in rows.values() if expected == "clear")
    lowest_failed = min(margin for expected, margin in rows.values() if expected == "failed")
    return (highest_clear + lowest_failed) / 2


def evaluate(rows, threshold):
    return {
        "threshold": threshold,
        "false_rejects": [
            key for key, (expected, margin) in rows.items()
            if expected == "clear" and margin > threshold
        ],
        "false_clears": [
            key for key, (expected, margin) in rows.items()
            if expected == "failed" and margin < threshold
        ],
        "ties": [key for key, (_, margin) in rows.items() if margin == threshold],
    }


def compare():
    archived = json.loads(ARCHIVE.read_text())["cases"]
    transfer = json.loads(VENEZUELA.read_text())["cases"]
    archive_rows = {
        key: (row["expected"], row["binary_average_margin"]) for key, row in archived.items()
    }
    venezuela_rows = {
        key: (row["expected"], row["pooled_margin"]) for key, row in transfer.items()
    }
    gaps = {
        key: margin - venezuela_rows[key.replace("/failed", "/clear")][1]
        for key, (expected, margin) in venezuela_rows.items() if expected == "failed"
    }
    return {
        "scope": "Retrospective diagnostics on existing logits. The zero threshold remains locked.",
        "venezuela_pair_margin_gaps": gaps,
        "archive_midpoint_applied_to_venezuela": evaluate(venezuela_rows, midpoint(archive_rows)),
        "venezuela_midpoint_applied_to_archive": evaluate(archive_rows, midpoint(venezuela_rows)),
    }


if __name__ == "__main__":
    print(json.dumps(compare(), indent=2))
