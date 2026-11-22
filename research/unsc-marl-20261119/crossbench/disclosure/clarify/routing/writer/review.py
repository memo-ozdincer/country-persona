"""Build evidence-matched final-judge packets and check the writer contract."""
import argparse
import json
from pathlib import Path
import re
import sys

from run import HEADINGS, HERE, WORDS, digest, suite

JUDGE = HERE.parents[4] / "judge"
sys.path.insert(0, str(JUDGE))
from score import score

def materialize(run):
    paths = {r["id"]: r for r in suite()}
    complete = json.loads((run/"complete.json").read_text())
    transcript = run/"transcript.jsonl"
    assert complete["sha256"] == digest(transcript) and complete["updates"] == 0
    rows = [json.loads(line) for line in transcript.read_text().splitlines()]
    assert set(r["id"] for r in rows) == set(paths) and len(rows) == len(paths) == complete["records"]
    return rows


def contract(row):
    lines = row["output"].splitlines()
    parsed = {}
    for line in lines:
        match = re.fullmatch(r"([A-Za-z]+): +(.+)", line.strip())
        if match:
            parsed[match[1]] = match[2]
    expected = row["expected_state"]
    public = json.loads(row["messages"][1]["content"])
    options = public["checked_public_evidence"]["verified_options"]
    expected_lines = [f"{expected} {option}" for option in options] if options else [expected]
    words = len(row["output"].split())
    line = parsed.get("Workshop", "")
    return {"headings": tuple(parsed) == HEADINGS and len(lines) == len(HEADINGS),
            "exact_disposition_line": line in expected_lines,
            "supported_disposition_prefix":any(re.match(re.escape(term)+r"(?:\b|$)",line) for term in expected_lines),
            "words":words, "word_limit_met":words <= WORDS, "ended":row["stop"] == "eos"}


def packet(row, opaque):
    text = row["output"]
    public = json.loads(row["messages"][1]["content"])
    proof = public["checked_public_evidence"]
    blocks = [{"id":item["id"],"text":item["fact"]} for item in public["history"]]
    if "historical_instrument" in public:
        blocks.append({"id":"historical-instrument","text":json.dumps(public["historical_instrument"],ensure_ascii=False)})
    positions = []
    for claim in public["admitted_disclosures"]:
        sign, package = next((f, v[0]) for f, v in (("accepts",claim["accepts"]),("excludes",claim["excludes"])) if v)
        positions.append({"id":claim["id"],"text":f"{claim['role']} {sign} option {package}."})
    blocks.extend(positions)
    blocks.append({"id":"scope","text":public["scope"]})
    cases = {
        "AGREEMENT_POSSIBLE": "Name the certified package and give its correct convener, public report and interval. Limit compatibility to the workshop.",
        "IMPASSE": "Explain that each one of the seven packages has a documented exclusion from at least one role. Do not infer that either role lacks acceptable packages.",
        "UNRESOLVED": "Name each open package and explain the missing compatible or excluding disclosure. The admitted evidence does not certify agreement or impasse.",
    }
    blocks.append({"id":"public-proof","text":json.dumps(proof,sort_keys=True,ensure_ascii=False)})
    for option in public["packages"]:
        blocks.append({"id":f"package-{option['id']}","text":json.dumps(option,ensure_ascii=False)})
    rubric = {
        "disposition": "Correctly state the draft number, resolution number, tally, both historical votes and the verified workshop disposition.",
        "operative": cases[proof["state"]],
        "positions": "Attribute one correct and relevant scoped signed claim to each workshop role, and cite each actual claim ID.",
        "unresolved": "Preserve India's recorded Monitoring Team and reporting concerns, and do not overstate their satisfaction. Preserve any uncertainty material to the stated disposition, including which unresolved package matters in an unresolved record. An agreement record must avoid unsupported claims of uniqueness.",
        "authority": "Describe the workshop options as fictional proposals with no change to the adopted resolution or new official national decision.",
    }
    return {"id":opaque,"mode":"FINAL","task":public["task"],"answer":text,"evidence":blocks,
            "rubric":[{"id":key,"category":"final","weight":14,"rule":rule} for key,rule in rubric.items()]}


def create(run):
    rows = sorted(materialize(run), key=lambda row:digest_text(row["id"]))
    return [{"model_id":row["id"],"mechanics":contract(row),"packet":packet(row,f"record-{i+1:02d}")}
            for i,row in enumerate(rows)]


def digest_text(value):
    from hashlib import sha256
    return sha256(("workshop-final-20261119:"+value).encode()).hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    p.add_argument("--verdicts",type=Path)
    args = p.parse_args()
    deck = create(args.run)
    if args.verdicts:
        by_id = {v["id"]:v for v in json.loads(args.verdicts.read_text())}
        assert set(by_id) == {r["packet"]["id"] for r in deck}
        deck = [{"model_id":r["model_id"],"mechanics":r["mechanics"],
                 "calibration":score(r["packet"], by_id[r["packet"]["id"]])} for r in deck]
    print(json.dumps(deck,indent=2,ensure_ascii=False))
