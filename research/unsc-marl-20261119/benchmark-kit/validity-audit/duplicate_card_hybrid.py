"""Replay the verified model national accounts with the archived public reference."""
import argparse
import json
from pathlib import Path
import re

from duplicate_card_modular import compose
from duplicate_card_modular_review import score
from duplicate_card_records import HEAD, TAIL
from duplicate_card_score import ASSIGNED, summarize_routes


def cited_ids(record):
    return {source.strip() for part in re.findall(r"\[([^\[\]\n]+)\]", record) for source in part.split(",")}


def run(directory):
    reviewed = score(directory)
    rows = compose(directory)["records"]
    marks = {r["id"].split("/")[-2]: r for r in reviewed["packet_scores"]}
    records, packets = [], {}
    for row in rows:
        receipt = row["receipt"]
        evidence = row["evidence"]
        scores = marks[receipt]
        roles = {key: card for key, card in ASSIGNED.items() if card in evidence}
        assert all(unit in scores["met_units"] for unit in roles)
        assert row["ended"] and scores["critical_guard"] == "clear"
        clauses = []
        citations_added = []
        for card, text in zip(roles.values(), row["component_texts"][1:], strict=True):
            assert cited_ids(text) <= {card}
            if card not in cited_ids(text):
                clauses.append(f"{text} [{card}]")
                citations_added.append(card)
            else:
                clauses.append(text)
        record = "\n\n".join([HEAD, *clauses, TAIL])
        words = len(record.split())
        assert words <= 160
        assert cited_ids(record) == set(evidence)
        expected = 56 + 7 * len(roles)
        public_units = ["D1", "D2", "A1", "A2", "C1", "C2", "S1", "S2"]
        records.append({"receipt": receipt, "record": record, "words": words,
                        "verbatim_model_clauses": row["component_texts"][1:],
                        "renderer_appended_ids": citations_added, "source_ids": list(evidence),
                        "excluded_public_citation_ids": sorted(cited_ids(row["component_texts"][0]) - set(evidence)),
                        "authored_public_units": public_units, "reviewed_national_units": list(roles),
                        "authored_plus_reviewed_points": expected})
        packets[frozenset(roles.values())] = {
            "floor": expected, "ceiling": expected, "met_units": [*public_units, *roles],
            "critical_guard": "clear", "under_limit": words <= 160, "words": words, "ended": True,
        }
    return {"scope": "Same-case hybrid composition. The archived public reference is authored. "
                     "The national clauses are unchanged model outputs with a source tag appended when missing. "
                     "Criterion scores combine authored public units and same-assistant reviewed model units.",
            "transcript_sha256": reviewed["transcript_sha256"],
            "annotation_sha256": reviewed["annotation_sha256"], "records": records, "arms": summarize_routes(packets)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory), ensure_ascii=False, indent=2))
