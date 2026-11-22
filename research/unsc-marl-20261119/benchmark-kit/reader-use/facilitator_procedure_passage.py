"""Test an intact procedural sentence against the excerpted tally failure."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_passage_routing_identity as prior

study, replay, atoms, trained = prior.study, prior.replay, prior.atoms, prior.trained
HERE, RUNNER = study.HERE, study.RUNNER
EVIDENCE = HERE / "facilitator-procedure-passage-evidence"
FAMILY = "facilitator-procedure-passage-2504"
SYSTEM = (
    "Choose the passages from the authorized local source that support the listed fields. The question is not evidence. "
    "One passage may support more than one field. Omit a passage when it is missing. "
    "Use only the supplied IDs. Return a space-separated list of passage IDs, or EMPTY if none support any field."
)


def local():
    packet, cards = study.sources()["2504"]
    procedure = cards[0]["source"]
    parts = procedure.split(". ")
    assert len(parts) == 3
    sequence, tally = parts[0] + ".", parts[1] + "."
    assert sequence in procedure and tally in procedure
    for key, context, _ in study.cases():
        if not key.startswith("2504/") or not key.endswith("/1"):
            continue
        withheld = key == "2504/4/1"
        passages = {"VN": sequence, "LP": packet["public"][0]}
        if not withheld:
            passages["DM"] = tally
        yield study.syria.fit.live.live.prompt(key, 50, SYSTEM, {"fields": context["fields"],
                                                            "question": context["question"], "passages": passages})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    paths = (Path(__file__).resolve(), EVIDENCE / "protocol.md", study.EVIDENCE / "identity.json",
             Path(study.__file__).resolve(), study.FIELDS, study.syria.case.PACKET, Path(RUNNER.__file__).resolve())
    return {str(p.relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def verify(directory):
    base = study.syria.fit.live.live.common.reused.previous.prior
    with patch.multiple(base, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return base.read(directory)


def score(rows):
    identity = trained.read(study.EVIDENCE / "identity.json")
    collected = deepcopy(identity["admission"])
    verdicts = {}
    for prompt in local():
        key = prompt["id"]
        row = rows[key]
        options = json.loads(prompt["messages"][-1]["content"])["passages"]
        tokens = set(row["output"].split()) if row["ended"] else set()
        trusted = tokens & set(options) & {"VN", "DM"}
        cert = {f: options[label] for f, label in (("1", "VN"), ("2", "DM"), ("3", "DM")) if label in trusted}
        assert all(v in options.values() for v in cert.values())
        withheld = key == "2504/4/1"
        if withheld:
            assert "2" not in cert and "3" not in cert
        passed = len(cert) == 3
        doc = collected["records"][key]
        doc.update({"evidence_emitted": cert, "field_pass": {str(i): str(i) in cert for i in range(1, 4)},
                    "delivery": passed, "format": row["ended"], "raw_answer": row["output"],
                    "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])})
        if not withheld:
            collected["matrices"]["2504"][int(key.split("/")[1])][1] = int(passed)
        verdicts[key] = {"reply": row["output"], "offered": options, "certified": cert, "delivery": passed,
                         "discarded_ids": sorted(tokens - trusted - {"EMPTY"})}
    weights = trained.read(HERE / "facilitator-measured-channel-evidence/fits.json")
    collected["withheld_controls"]["2504/4/1"] = {"fields_two_and_three_withheld": True,
        "valid_fields_delivered": sorted(collected["records"]["2504/4/1"]["evidence_emitted"])}
    return {"new_outputs": verdicts, "original_procedural_column": [m[1] for m in identity["admission"]["matrices"]["2504"]],
            "new_procedural_column": [m[1] for m in collected["matrices"]["2504"]],
            "whole_routing": replay.run(collected, weights)["2504"],
            "field_routing": atoms.run(collected, weights)["2504"]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert len(list(local())) == 5
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps(score(verify(args.directory)), ensure_ascii=False, indent=2))
