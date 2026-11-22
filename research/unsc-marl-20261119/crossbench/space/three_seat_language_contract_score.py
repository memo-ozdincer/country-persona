"""Audit declaration force, exact evidence spans and downstream decisions."""
import json
from pathlib import Path
import re
from unittest.mock import patch

import torch

import three_seat_language_contract as contract
import three_seat_language_score as previous

HERE = Path(__file__).resolve().parent
POSITIVES = HERE / "evidence/three-seat-positive-fit.json"
FORCE = HERE / "three-seat-language-contract-review.json"
GRADE = {"zero": 0, "one": 1, "two": 2, "three": 3, **{str(i): i for i in range(4)}}
PACKAGE_PATTERN = re.compile(r"\b(?:package(?: identifier| identified as)?|grade for)\s+([A-C])\b", re.I)
BARE_SUBJECT = re.compile(r"^([A-C])\s+(?:is\b|has been (?:confirmed|assigned)\b)")
GRADE_PATTERN = re.compile(r"\b(?:[0-3]|zero|one|two|three)\b", re.I)


def evidence(row):
    output = row["output"]
    if row["ended"] and output == "NONE":
        return None, {"correct_shape": True, "quoted": None, "quote_clear": True}
    line, newline, quoted = output.partition("\n")
    value, valid = previous.parsed({**row, "output": line})
    if not valid or value is None or not newline:
        return None, {"correct_shape": False, "quoted": None, "quote_clear": False}
    quote = quoted.strip()
    if len(quote) >= 2 and (quote[0], quote[-1]) in {('"', '"'), ("'", "'"), ("“", "”")}:
        quote = quote[1:-1]
    source = json.loads(row["messages"][1]["content"])["delegate_message"]
    options = {name.upper() for name in PACKAGE_PATTERN.findall(quote)}
    explicit_package = set(options)
    subject = BARE_SUBJECT.match(quote)
    if subject:
        options.add(subject[1])
    digits = {GRADE[word.lower()] for word in GRADE_PATTERN.findall(quote)}
    letter = "ABC"[value[0]]
    clear = bool(quote) and "\n" not in quote and quote in source and options == {letter} and digits == {value[1]}
    return (value if clear else None), {"correct_shape": True, "quoted": quote, "quote_clear": clear,
                                          "quote_names_package_explicitly": explicit_package == {letter},
                                          "ungated_tuple": value}


def records(raw):
    old = json.loads((contract.old.ROOT / "results.json").read_text())
    assessment = json.loads(FORCE.read_text())
    trace = contract.ROOT / "transcript.jsonl"
    assert assessment["transcript_sha256"] == contract.runner.digest(trace)
    reviewed = assessment["messages"]
    result = []
    for (letter, grade), before in zip(contract.old.VOCABULARY, old["recorded_messages"], strict=True):
        key = f"{letter}{grade}"
        intended = ("ABC".index(letter), grade)
        written = raw[f"write/{key}"]["output"]
        label = reviewed[key]
        assert label["span"] in written and label["span"]
        classic, valid = previous.parsed(raw[f"classic/{key}"])
        extracted, proof = evidence(raw[f"evidence/{key}"])
        result.append({"intended": intended, "text": written, "review": label,
                       "base_exact": before["exact"], "old_reader": classic, "old_reader_valid": valid,
                       "old_reader_right": valid and classic == intended,
                       "evidence_reader": extracted, "evidence_reader_right": extracted == intended,
                       "quote_check": proof,
                       "tokens": {"writer": len(raw[f"write/{key}"]["output_ids"]),
                                  "classic": len(raw[f"classic/{key}"]["output_ids"]),
                                  "evidence": len(raw[f"evidence/{key}"]["output_ids"])}})
    controls = []
    for key, (_, intended) in (contract.NEW_CONTROLS | {"previous_c_zero": ("", None)}).items():
        row = raw[f"evidence/{key}"]
        decoded, check = evidence(row)
        wanted = None if intended is None else ("ABC".index(intended[0]), intended[1])
        controls.append({"label": key, "wanted": wanted, "reported_value": decoded, "output": row["output"],
                         "parser_correct": decoded == wanted, "explicit_none": row["output"] == "NONE",
                         "quote_check": check})
    return result, controls


def gate_controls():
    cases = {
        "plain_self_report": ("My current grade for package A is one.", "A 1\npackage A is one", (0, 1)),
        "selects_one_of_two": ("My grade for package A is one. My grade for package B is two.",
                               "A 1\npackage A is one", None),
        "quotes_peer": ("The other delegate reported that package C is zero. I have supplied no grade.",
                        "C 0\npackage C is zero", None),
        "quotes_withdrawn_grade": ("The previous grade for package C is two. I withdraw that grade.",
                                   "C 2\npackage C is two", None),
    }
    report = []
    for label, (message, authored_output, expected) in cases.items():
        verified, checks = evidence({"ended": True, "output": authored_output, "messages": [
            {}, {"content": json.dumps({"delegate_message": message})}]})
        report.append({"case": label, "message": message, "authored_reader_output": authored_output,
                       "accepted": verified, "should_admit": expected, "agrees": verified == expected,
                       "checks": checks})
    return report


def run():
    torch.set_num_threads(1)
    raw = contract.replay(contract.ROOT)
    readbacks, controls = records(raw)
    fit = json.loads(POSITIVES.read_text())
    reg = json.loads(previous.trained.REGISTRY.read_text())
    entries = {row["draw"]: row for row in reg["accepted"]}
    weights = torch.as_tensor(fit["weights"], dtype=torch.float64)
    canonical = {note["intended"]: note["intended"] for note in readbacks}
    classic = {note["intended"]: note["old_reader"] for note in readbacks}
    with_evidence = {note["intended"]: note["evidence_reader"] for note in readbacks}
    tables = {"typed": canonical, "new_writer_old_reader": classic, "new_writer_quote_reader": with_evidence,
              "new_writer_strict_review": {note["intended"]: note["evidence_reader"]
                                          if note["review"]["confirmed"] else None for note in readbacks}}
    scores = []
    for saved in fit["reserved"]:
        key = saved["grid_id"]
        with patch.dict(previous.shared.FIXTURES, {"target": previous.trained.fixture(entries[key])}):
            data = previous.trained.data_for(previous.shared.Grid("target"))
            p = data.probabilities(weights).numpy()
            rates = {name: previous.projection(data, p, mapping, "bound") for name, mapping in tables.items()}
        assert abs(rates["typed"]["net"] - saved["results"]["fitted"]["net"]) < 1e-9
        scores.append({"grid_id": key, "independent_net": saved["results"]["exact_independent"]["net"],
                       "projection": rates})
    return {
        "scope": "Frozen Qwen writer and readers using the same finite typed actions. The quote gate validates "
                 "exact phrasing, package and number. Same-assistant review tests commitment force separately. "
                 "All decisions still use the frozen exact policy and verifier.",
        "confirmed_declarations": sum(note["review"]["confirmed"] for note in readbacks),
        "messages": readbacks, "controls": controls, "authored_quote_gate_controls": gate_controls(), "scores": scores,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
