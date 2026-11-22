"""Hold the historical routing policy fixed and verify the native desk receipts."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_record as checked

r, e = checked.r, checked.e
ARCHIVE = HERE.parents[3] / "benchmark-kit" / "reader-use" / "tribunals2422-transfer"
RUN = HERE / "evidence"
CASE = "tribunals"
BASE = (
    "On 27 June 2018 the Council adopted Peru’s draft S/2018/628 as Resolution 2422 (2018), "
    "14–0–1, with Russia abstaining. Serbia participated without a vote. Acting under Chapter VII, "
    "the Council appointed Serge Brammertz as Mechanism Prosecutor from 1 July 2018 through 30 June 2020. "
    "It concluded the progress review and underlined full state cooperation. Resolution 2422 did not order "
    "temporary medical release for Ratko Mladić or make a finding about his treatment."
)


def case_data():
    case = e.cases()[CASE]
    packet = e.read(ARCHIVE / "packet.json")
    blocks = {b["id"]: b["text"] for b in e.evidence(case)}
    expected = {atom["id"]: atom["text"] for desk in packet["cards"] for atom in desk["atoms"]}
    assert {k: blocks[k] for k in expected} == expected
    return case, packet


def requests():
    _, packet = case_data()
    data = {}
    for card in packet["cards"]:
        clauses = {item["id"]: item["text"] for item in card["atoms"]}
        data[card["desk"]] = {"max_output_tokens": 200, "messages": [
            {"role": "system", "content": "Return one JSON object with the same two keys as evidence. Copy each "
             "complete evidence sentence exactly as supplied, without paraphrasing. Do not add any keys or text."},
            {"role": "user", "content": json.dumps({"desk": card["desk"], "evidence": clauses}, ensure_ascii=False)},
        ]}
    return data


def pins():
    files = (Path(__file__), HERE / "protocol.md", HERE / "requests.json", e.HERE / "release.json",
             ARCHIVE / "packet.json", ARCHIVE / "forecast.json", ARCHIVE / "writer-results.json")
    return {str(p.relative_to(HERE.parents[3])): sha256(p.read_bytes()).hexdigest() for p in files}


def collect(generate, directory):
    assert requests() == e.read(HERE / "requests.json")
    for name, request in requests().items():
        r.w.archived.base.suite.append(directory / "calls.jsonl", {"desk": name, "request": request, "reply": generate(request)})
    (directory / "inputs.json").write_text(json.dumps(pins(), indent=2) + "\n")


def admitted():
    _, packet = case_data()
    boxes = [json.loads(line) for line in (RUN / "calls.jsonl").read_text().splitlines()]
    admissions = []
    for card, row in zip(packet["cards"], boxes, strict=True):
        assert row["desk"] == card["desk"]
        choices = r.parse(row["reply"])
        admissions.append([item["id"] for item in card["atoms"] if choices.get(item["id"]) == item["text"]])
    return admissions


def records(method, legal):
    case, packet = case_data()
    cards = [[item["id"] for item in desk["atoms"]] for desk in packet["cards"]]
    atoms = {item["id"]: item for desk in packet["cards"] for item in desk["atoms"]}
    outcomes = {}
    joint = set(packet["joint"]["needs"])
    for mask in range(8):
        available = [key for i, desk in enumerate(legal) if mask & (1 << i)
                     for key in cards[i] if key in desk]
        possibilities = []
        for count in range(len(available) + 1):
            for keys in combinations(available, count):
                words = sum(len(atoms[k]["text"].split()) for k in keys)
                if words > 70 or len(BASE.split()) + words > case["word_cap"]:
                    continue
                routine_score = sum(atoms[k]["points"] for k in keys) + packet["joint"]["points"] * (joint <= set(keys))
                rank = routine_score + (9 * ("srb-release" in keys) if method == "v1.2" else 0)
                possibilities.append((rank, -words, keys))
        _, _, kept = max(possibilities)
        suffix = " ".join(atoms[key]["text"] for key in kept)
        outcomes[mask] = {"available": available, "kept": list(kept),
                          "historical_record": BASE + ("\n\n" + suffix if suffix else "")}
    return outcomes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("requests", "run"))
    if parser.parse_args().mode == "requests":
        e.emit(requests())
    else:
        with patch.object(r.w.archived.base.suite, "collect", collect), patch.object(
                r.w.archived.base, "roster", return_value=dict.fromkeys(requests())):
            r.w.archived.base.run(RUN)
