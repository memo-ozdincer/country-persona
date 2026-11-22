"""Assemble source-local model output and replay the frozen packet routes."""
from collections import Counter, defaultdict
import json
from pathlib import Path

from receipt_outcomes import CITATION, EVIDENCE, final_review, writer
import field_writer as generator

HERE = Path(__file__).resolve().parent
FIELDS = HERE / "field-evidence"
REQUIRED = {
    "OPERATIVE": {"renewal", "further"},
    "ADDITIONAL": {"eln", "emc"},
    "BRAZIL": {"brazil_capacity", "brazil_hope"},
    "A3": {"a3_condition", "a3_ethnic"},
    "overlap": {"common_ground"},
}


def approved_fields():
    outputs = generator.replay(FIELDS)
    return review_fields(outputs, FIELDS / "transcript.jsonl", HERE / "field-annotations.json")


def review_fields(outputs, trace, annotation_file):
    review = json.loads(annotation_file.read_text())
    assert review["transcript_sha256"] == writer.runner.digest(trace)
    assert outputs.keys() == review["fields"].keys() and outputs.keys() <= REQUIRED.keys()
    endpoint = {}
    for field, row in outputs.items():
        annotation = review["fields"][field]
        body = row["output"]
        allowed = set(row["evidence_ids"])
        actual = {key for phrase in CITATION.findall(body) for key in phrase.split(", ")}
        assert set(annotation["met"]) <= REQUIRED[field]
        assert all(spans and all(span in body for span in spans) for spans in annotation["met"].values())
        assert all(issue["span"] in body and issue["reason"] for issue in annotation["guard_issues"])
        endpoint[field] = {"text": body, "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"]),
                           "complete": row["ended"], "citation_ids_clear": actual == allowed,
                           "semantic_clear": not annotation["guard_issues"], **annotation}
    return endpoint


def assemble(packet, fields, reference, prefix, rules):
    ids = packet.split(",")
    chosen = [name for name in REQUIRED if name in ids]
    if generator.SOURCES <= set(ids):
        chosen.append("overlap")
    blocks = [fields[name] for name in chosen]
    record = "\n\n".join([prefix, *(block["text"] for block in blocks)])
    met = {"procedure": [prefix]}
    guards = []
    for block in blocks:
        assert not met.keys() & block["met"].keys()
        met.update(block["met"])
        guards.extend(block["guard_issues"])
    assert met.keys() <= reference["proof"].keys()
    assessment = final_review(rules, {"output": record, "ended": all(b["complete"] for b in blocks)},
                              {"met": met, "guard_issues": guards})
    citation_clear = all(block["citation_ids_clear"] for block in blocks)
    permitted = (assessment["complete"] and assessment["source_guard_clear"]
                 and assessment["word_count"] <= 185 and citation_clear)
    return {**assessment, "cited_sources_clear": citation_clear, "release": permitted, "record": record,
            "delivered_criteria_complete": met.keys() == reference["proof"].keys(),
            "writers": len(blocks), "input_tokens": sum(b["input_tokens"] for b in blocks),
            "output_tokens": sum(b["output_tokens"] for b in blocks),
            "semantic_issues": guards}


def replay_routes(base, assembled):
    outcomes = {}
    for condition, schedule in base["routes"].items():
        rows = {}
        for route_id in schedule["mean"]:
            average = defaultdict(float)
            n = len(schedule["rows"])
            for case in schedule["rows"]:
                for packet, mass in case[route_id]["packet_probabilities"].items():
                    row = assembled[packet]
                    weight = mass / n
                    average["record_points"] += weight * row["points"]
                    average["release_probability"] += weight * row["release"]
                    average["released_points"] += weight * row["points"] * row["release"]
                    average["writer_calls"] += weight * row["writers"]
                    average["input_tokens"] += weight * row["input_tokens"]
                    average["output_tokens"] += weight * row["output_tokens"]
                    average["delivered_criteria_complete"] += weight * row["delivered_criteria_complete"]
            before = schedule["mean"][route_id]
            rows[route_id] = {**average,
                              "raw_change": average["record_points"] - before["record_points"],
                              "release_change": average["release_probability"] - before["release_probability"],
                              "released_score_change": average["released_points"] - before["released_record_points"]}
        outcomes[condition] = rows
    return outcomes


def run():
    fields = approved_fields()
    dossier = json.loads(writer.CASE.read_text())
    original = json.loads((EVIDENCE / "results.json").read_text())
    _, verified = writer.compile_bank()
    prefix = verified[frozenset()]["text"]
    built = {name: assemble(name, fields, verified[frozenset(name.split(","))], prefix, dossier["rules"])
             for name in original["bank"]}
    assert len(built) == 14
    diagnosis = Counter(rule_id for record in built.values() for rule_id in record["evidence_spans"])
    return {"scope": "The final body concatenates five individually generated field types with an authored roll call. "
                     "The comparison is generated and available only with its three underlying sources. "
                     "One to four model calls are used per packet. The original route probabilities "
                     "and simulated desk labels do not change. Semantics are reviewed by the same assistant.",
            "fields": fields, "packets": built, "retained_counts": dict(diagnosis),
            "route_outcomes": replay_routes(original, built)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
