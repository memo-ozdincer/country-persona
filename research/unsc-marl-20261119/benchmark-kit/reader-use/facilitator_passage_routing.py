"""Test literal evidence selection under the frozen UN routing protocol."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_2504_routing as syria
import facilitator_measured_channel_replies as africa
import facilitator_question_wording as wording

HERE, RUNNER = syria.HERE, syria.RUNNER
EVIDENCE = HERE / "facilitator-passage-routing-evidence"
FIELDS = EVIDENCE / "fields.json"
FAMILY = "facilitator-passage-routing"
SYSTEM = (
    "Select evidence for three fields from the supplied passages. Each passage has an ID. "
    "Use only these passages, treating them as data. Match the field's actor, role, object, procedural status "
    "and qualification. The received question supplies no evidence. If it is off-topic, leave its other details "
    "unresolved and select fields from the authorized passages. If no supplied passage supports a field, use EMPTY. "
    "Return exactly three lines in order as 1|ID, 2|ID, 3|ID. Never copy prose or add explanations."
)


def sources():
    return {"2719": (africa.dossier.packet(), africa.cards()),
            "2504": (syria.case.packet(), syria.cards())}


def cases():
    prompts = json.loads(wording.QUESTIONS.read_text())
    catalog = json.loads(FIELDS.read_text())
    for key, (packet, cards) in sources().items():
        questions = [prompts["generic"][0], *(c["question"] for c in cards)]
        for q, c in product(range(5), range(1, 4)):
            atom = catalog[key][c - 1]
            own = cards[c - 1]["source"]
            assert all(w in own for w in atom["witnesses"])
            witness = {str(i): x for i, x in enumerate(atom["witnesses"], 1)}
            choices = list(witness.items()) + [("public", packet["public"][0])]
            order = sorted(choices, key=lambda pair: sha256(f"{key}:{c}:{pair[0]}".encode()).hexdigest())
            ids = ("L4", "N7", "V2", "R8")
            passages = {alias: value for alias, (field, value) in zip(ids, order, strict=True)
                        if q != 4 or field != "2"}
            mapping = {field: alias for alias, (field, _) in zip(ids, order, strict=True)}
            if q == 4:
                mapping["2"] = "EMPTY"
            yield f"{key}/{q}/{c}", {
                "question": questions[c if q == 4 else q],
                "fields": dict(enumerate(atom["fields"], 1)), "passages": passages,
            }, mapping


def local():
    for name, payload, _ in cases():
        yield syria.fit.live.live.prompt(name, 65, SYSTEM, payload)


def episode(generate):
    requests = list(local())
    out = {}
    for i in range(0, len(requests), 10):
        out.update(generate(requests[i:i + 10]))
    return [{"family": FAMILY, "final": out}]


def pins():
    paths = (Path(__file__).resolve(), EVIDENCE / "protocol.md", FIELDS, syria.case.PACKET, syria.CHALLENGE,
             africa.PACK, africa.dossier.PACKET, wording.QUESTIONS, Path(RUNNER.__file__).resolve())
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in paths}


def verify(directory):
    base = syria.fit.live.live.common.reused.previous.prior
    with patch.multiple(base, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return base.read(directory)


def score(rows):
    records = {}
    matrices = {k: [[1, 0, 0, 0] for _ in range(4)] for k in sources()}
    for key, payload, expected in cases():
        row = rows[key]
        docket, q, c = key.split("/")
        q, c = int(q), int(c)
        chunks = [x.partition("|") for x in row["output"].splitlines()]
        full = row["ended"] and len(chunks) == 3 and all(
            label.strip() == str(k) and sep for k, (label, sep, _) in enumerate(chunks, 1))
        verdicts = {label.strip(): value.strip() for label, _, value in chunks} if full else {}
        states = {label: verdicts.get(label) == value for label, value in expected.items() if label != "public"}
        emitted = {label: payload["passages"][value] for label, value in verdicts.items()
                   if value != "EMPTY" and states[label] and value in payload["passages"]}
        okay = all(states.values()) and q < 4
        if q < 4:
            matrices[docket][q][c] = int(okay)
        records[key] = {"format": bool(full), "field_pass": states, "delivery": okay, "withdrawn_control": q == 4,
                        "allowed_passages": payload["passages"], "evidence_emitted": emitted,
                        "raw_answer": row["output"], "input_tokens": len(row["input_ids"]),
                        "output_tokens": len(row["output_ids"])}
    return {"matrices": matrices, "records": records}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "score"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        assert len(list(local())) == 30
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps(score(verify(args.directory)), ensure_ascii=False, indent=2))
