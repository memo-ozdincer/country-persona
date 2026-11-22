"""Measure compositional coverage of procedural and national roles."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import coverage_logits as base

prior, old, READ = base.prior, base.old, base.READ
OUT = HERE / "evidence"
archived_records = prior.records

ATOMS = {
    "role": {
        "announcement": "The record attributes the announcement of the vote result or adoption to the Council President or chair in a procedural capacity.",
        "national_explanation": "The record attributes the explanation of India's abstention to India speaking in its national capacity.",
    },
    "uk": {
        "sponsorship": "The record identifies the United Kingdom as the country that submitted or sponsored the draft.",
        "affirmative": "The record explicitly states that the United Kingdom voted in favour of the draft.",
        "rationale": "The record gives the United Kingdom's stated rationale for the draft or its support, such as the aims it emphasized or the consultations it cited.",
    },
}


def records():
    native = archived_records()
    pair = native["myanmar/pair"]
    full = native["myanmar/control"]
    pair_lines = [text for _, text in pair["paragraphs"]]
    assert len(pair_lines) == 4 and pair_lines[2].startswith("India as a delegation")
    assert pair_lines[1].startswith("United Kingdom")
    results = {}

    def add(key, lines, role=None, uk=None):
        assert len(" ".join(lines).split()) <= 150, key
        targets = {}
        if role is not None:
            targets["role"] = dict(zip(ATOMS["role"], role, strict=True))
        if uk is not None:
            targets["uk"] = dict(zip(ATOMS["uk"], uk, strict=True))
        results[key] = {"candidate_paragraphs": [[i, line] for i, line in enumerate(lines, 1)],
                        "target_components": targets}

    add("archived-pair", pair_lines, ("unmet", "met"), ("met", "met", "met"))
    add("archived-full", [text for _, text in full["paragraphs"]], ("met", "met"), ("met", "met", "met"))
    for key, line, expected in (
            ("insert-announcement", "Council procedure — The President called the vote and announced adoption.", "met"),
            ("insert-paraphrase", "In the chair, India declared the result and the measure adopted.", "met"),
            ("insert-title", "India held the Council presidency.", "unmet"),
            ("insert-national-announcement", "India's national delegation called the vote and announced adoption.", "unmet")):
        add(key, [*pair_lines[:3], line, pair_lines[3]], (expected, "met"))
    add("swap-explanation-capacity", [*pair_lines[:2],
        "The Council President called the vote and announced adoption, then explained India's abstention as Council President.",
        pair_lines[3]], ("met", "unmet"))
    head = pair_lines[0].replace(" The United Kingdom voted in favour.", "")
    assert head != pair_lines[0]
    add("remove-uk-vote", [head, *pair_lines[1:]], uk=("met", "unmet", "met"))
    add("remove-uk-rationale", [pair_lines[0], "The United Kingdom submitted the draft.", *pair_lines[2:]],
        uk=("met", "met", "unmet"))
    return results


def plan():
    source = {r["id"]: r["rule"] for r in archived_records()["myanmar/pair"]["criteria"]}
    requests = {}
    for case, record in records().items():
        for criterion in record["target_components"]:
            predicates = {"compound": source[criterion]} | ATOMS[criterion]
            for atom, rule in predicates.items():
                for labelset, mapping in base.LABELS.items():
                    ident = f"{case}/{criterion}/{atom}/{labelset}"
                    payload = {"candidate_paragraphs": record["candidate_paragraphs"], "criterion": rule,
                               "answer_letters": {letter: base.DEFINITIONS[meaning] for letter, meaning in mapping.items()}}
                    requests[ident] = {"id": ident, "max_output_tokens": 2, "messages": [
                        {"role": "system", "content": base.SYSTEM},
                        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
    assert len(requests) == 74
    pins = (Path(__file__).resolve(), HERE / "protocol.md", Path(base.__file__), Path(prior.__file__),
            PARENT / "plan.json", PARENT / "results.json", old.MYANMAR)
    return {"requests": requests, "sha256": {str(path.relative_to(base.t.STUDY)): old.digest(path) for path in pins}}


def execute(mode):
    with patch.multiple(base, HERE=HERE, OUT=OUT, plan=plan), patch.object(prior, "records", return_value=records()):
        return {"run": base.run, "verify": base.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        execute(mode)
    else:
        print(json.dumps(plan() if mode == "plan" else execute(mode), indent=2, ensure_ascii=False))
