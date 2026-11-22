"""Apply the frozen Qwen scope interface and admission heads to Myanmar."""
import argparse
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
FIT = HERE.parent / "reporting-2739/learned-admission"
RELEASE = HERE.parents[1] / "benchmark-v1.5"
OUT = HERE / "evidence"
sys.path.insert(0, str(FIT))
import held
import team

e = held.e
CASE = next(row for row in e.read(RELEASE / "cases.json") if row["id"] == "myanmar")
BLOCKS = e.judge.by_id(e.evidence(CASE))
SPECS = (
    ("uk-position", "supports", "uk",
     "The United Kingdom submitted the draft and welcomed its adoption after consultations with Council members, ASEAN members and regional partners. It emphasized ending violence, humanitarian access and support for ASEAN efforts."),
    ("india-position", "supports", "india",
     "India praised the United Kingdom's consultation and advocated quiet, constructive diplomacy in light of neighbouring countries' concerns."),
    ("chair-role", "supports", "chair",
     "India held the Council presidency. The President called the vote and announced adoption. India's representative separately explained the national abstention before resuming presidential duties."),
    ("humanitarian-terms", "supports", "mandate",
     "The resolution demands an immediate end to violence and calls for humanitarian access."),
    ("oral-report", "supports", "mandate",
     "The Council recognized ASEAN's central role and requested that the Secretary-General or his Special Envoy coordinate with the ASEAN Special Envoy and report orally to the Council by 15 March 2023 on United Nations support for the Five-Point Consensus."),
    ("india-voted-yes", "contradicts", "vote",
     "India voted in favour of adopting resolution 2669 (2022)."),
    ("written-public-report", "contradicts", "mandate",
     "The reporting instruction due 15 March 2023 required a written public report instead of an oral report to the Council."),
    ("india-opposed-asean", "unknown", "india",
     "India's abstention expressed its opposition to ASEAN taking a leading role."),
)
OWN = {"uk": 1, "mandate": 1, "india": 2, "chair": 2, "vote": 2}


def fixtures():
    return [{"id": name, "expected": label, "source": block, "witness": BLOCKS[block]["text"],
             "assertion": assertion, "owner": OWN[block]} for name, label, block, assertion in SPECS]


def asks():
    for row in fixtures():
        payload = {"quoted_premise": row["witness"], "passage_for_references": BLOCKS[row["source"]]["text"],
                   "assertion": row["assertion"]}
        for request in held.archived.protocol.encoded(("held", row["id"]), held.archived.TASK,
                                                       payload, held.archived.OPTIONS):
            yield request | {"observation": list(request["observation"]), "legal": list(request["legal"]),
                             "max_output_tokens": 2}


def plan():
    paths = (Path(__file__), HERE / "protocol.md", FIT / "fit.json", FIT / "held.py",
             FIT / "team.py", RELEASE / "release.json", RELEASE / "cases.json",
             Path(held.archived.__file__), Path(held.archived.protocol.__file__))
    fit = e.read(FIT / "fit.json")["frozen"]
    assert CASE["family"] not in fit["training_families"]
    return {"fixtures": fixtures(), "requests": list(asks()), "frozen_training_families": fit["training_families"],
            "sha256": {str(f.relative_to(team.STUDY)): team.pin(f) for f in paths}}


def lock():
    assert plan() == e.read(HERE / "plan.json")


def call(run):
    with patch.multiple(held, CASE=CASE, HERE=HERE, OUT=OUT, asks=asks, lock=lock):
        return run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        call(held.run)
    else:
        e.emit(plan() if mode == "plan" else call(held.verify))
