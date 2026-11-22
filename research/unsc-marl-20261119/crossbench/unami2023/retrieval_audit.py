"""Measure how much known proof survives shortening candidate text."""
from collections import Counter
import json
from math import log
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SENTENCES = re.compile(r"\S.*?(?:(?<=[.!?])\s+(?=[A-Z])|\Z)", re.S)
TOKEN = re.compile(r"[\w/]+")
IGNORE = frozenset("a an the in on as for at by to and or of is are was were its their it "
                   "that what had has should with about does will which up each gives states "
                   "explicitly identifies names says".split())


def load(path):
    return json.loads(path.read_text())


def words(text):
    return set(TOKEN.findall(text.lower())) - IGNORE


def segment(candidate):
    return [(m.start(), m.end(), m.group()) for m in SENTENCES.finditer(candidate)]


def citation_windows(sentences, source_ids):
    # Archived packets contain [SOURCE], (SOURCE), or '; SOURCE)'.
    citation = re.compile(r"(?<=[\[(,;: ])(?:" + "|".join(map(re.escape, source_ids)) + r")(?=[\]),; ])")
    return [window for window in sentences if citation.search(window[2])]


def ranked_windows(sentences, criterion, source_ids):
    query = words(criterion)
    available = [words(row[2]) for row in sentences]
    frequency = Counter(word for row in available for word in row)
    hits = {row[0] for row in citation_windows(sentences, source_ids)}

    def relevance(i):
        terms = query & available[i]
        return (sum(1 + log((1 + len(sentences)) / (1 + frequency[word])) for word in terms)
                + (0.75 if sentences[i][0] in hits else 0), -i)

    return [sentences[i] for i in sorted(range(len(sentences)), key=relevance, reverse=True)]


def unami():
    specs = load(HERE / "case.json")["rules"]
    review = load(HERE / "annotations.json")["records"]
    final = next(iter(load(HERE / "evidence/final-records.json").values()))
    for name, text in final.items():
        for state in ("met", "contradicted"):
            for field, witnesses in review[name][state].items():
                source_id, criterion = specs[field]
                yield f"{name}/{field}", text, state, (source_id,), criterion, witnesses


def minurso():
    parts = ROOT / "judge/minurso-atomic-rubric.json"
    proposals = ROOT / "benchmark-kit/evidence"
    paper = load(proposals / "source-record-minurso/atomic-annotations.json")
    spec = {p["id"]: p for group in load(parts)["groups"] for p in group["parts"]}
    for run, arms in paper["runs"].items():
        opaque = load(proposals / run / "judge-key.json")["key"]
        packets = load(proposals / run / "judge-packets.json")["packets"]
        for packet in packets:
            arm = opaque[packet["id"]]
            for field, (state, span, _) in arms[arm].items():
                if state not in ("met", "contradiction"):
                    continue
                part = spec[field]
                yield (f"{run}/{arm}/{field}", packet["answer"],
                       "contradicted" if state == "contradiction" else state, part["blocks"], part["criterion"], [span])


def survives(candidate, witnesses, selected):
    def contains(span):
        return any(span in candidate[start:end] for start, end, _ in selected)
    return all(contains(span) for span in witnesses)


def run():
    families = {}
    for family, records in (("UNAMI", unami()), ("MINURSO", minurso())):
        details = []
        for name, candidate, status, blocks, requirement, witnesses in records:
            assert all(w in candidate for w in witnesses) and witnesses
            sentences = segment(candidate)
            ranked = ranked_windows(sentences, requirement, blocks)
            options = {"whole": [(0, len(candidate), candidate)],
                       "all_sentences": sentences, "citations_only": citation_windows(sentences, blocks),
                       **{f"ranked_{k}": ranked[:k] for k in (1, 2, 3)}}
            details.append({"id": name, "status": status, "reviewer_spans": witnesses,
                            "retrieval": {mode: {"contains_all_spans": survives(candidate, witnesses, selected),
                                                 "characters": sum(len(text) for _, _, text in selected),
                                                 "spans": [text for _, _, text in selected]}
                                          for mode, selected in options.items()}})
        families[family] = {
            "units": len(details),
            "by_status": dict(Counter(x["status"] for x in details)),
            "summary": {
                mode: {"met": sum(row["status"] == "met" and row["retrieval"][mode]["contains_all_spans"] for row in details),
                       "contradicted": sum(row["status"] == "contradicted" and row["retrieval"][mode]["contains_all_spans"]
                                           for row in details),
                       "character_share": round(sum(row["retrieval"][mode]["characters"] for row in details) /
                                                sum(row["retrieval"]["whole"]["characters"] for row in details), 4)}
                for mode in details[0]["retrieval"]},
            "misses": {mode: [row["id"] for row in details if not row["retrieval"][mode]["contains_all_spans"]]
                       for mode in details[0]["retrieval"]},
        }
    return {"scope": "Retrospective verification that candidate passages retain manually identified exact evidence. "
                     "No label inference and no guarantee the manual annotations exhaust all valid witnesses.",
            "by_family": families}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
