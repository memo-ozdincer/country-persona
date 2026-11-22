"""Measure role classification across probe and mission wording on the written vote."""
import argparse
from itertools import batched
import json
from pathlib import Path
import sys
from unittest.mock import patch

import corroboration

HERE = Path(__file__).resolve().parent
JERUSALEM = HERE.parent / "jerusalem2017"
sys.path.insert(0, str(JERUSALEM))

import language_partner as partner

GUIDE = (
    "Classify which capacity the assignment concerns. NATIONAL means the speaker's national explanation of a vote "
    "or a national delegation's assessment of a draft. PROCEDURAL means an officer's formal act recording or "
    "transmitting the Council's result. The same person may act in both capacities. Return exactly NATIONAL or PROCEDURAL."
)
ASSIGNMENTS = {
    "us": ("Identify the U.S. national justification for its vote, with its view about return to countries of origin or nationality.",
           "What reason did the American delegation give for opposing the text, and where did it say return should be directed?"),
    "russia": ("Identify Russia's own explanation for its affirmative vote and its objection about repatriation.",
               "Recover how the Russian delegation defended supporting the draft while disagreeing about fighters returning from Syria and Iraq."),
    "indonesia_national": ("Identify Dian Triansyah Djani's policy remarks when speaking for Indonesia.",
                           "What did Djani, speaking for his country, say the Indonesian text would do for Member States?"),
    "council_president": ("Identify the separate administrative act when Djani acted as President of the Security Council.",
                          "Who formally sent the certified result of the written ballot to the Council's members, and in what capacity?"),
}
PROTOCOLS = {"national_desk": "NATIONAL", "procedure_desk": "PROCEDURAL"}


def requests():
    assert set(ASSIGNMENTS) == set(corroboration.KEYS)
    for index, stage in enumerate(("probe", "mission")):
        for key in corroboration.KEYS:
            yield partner.replay.request(f"{stage}/{key}", 24, GUIDE, {"assignment": ASSIGNMENTS[key][index]}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 4):
        rows.update(generate(list(group)))
    return [{"family": corroboration.load()["id"], "final": rows}]


def locks():
    paths = (Path(__file__), HERE / "task.json", HERE / "accession.json", HERE / "corroboration-records.json",
             partner.writer.MODEL, Path(partner.runner.__file__))
    return {path.name: partner.digest(path) for path in paths}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    observations = {
        phase: [rows[f"{phase}/{key}"]["output"] if rows[f"{phase}/{key}"]["ended"] else None
                for key in corroboration.KEYS] for phase in ("probe", "mission")
    }
    assert all(value in PROTOCOLS.values() for branch in observations.values() for value in branch)
    return {"scope": "Frozen Qwen classifies the provenance. The selected desk protocol then renders a generic request "
                     "or deliberate silence. The receiver sees only that bit, after channel loss.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "classes": observations,
            "desks": {name: {phase: [int(value == target) for value in values]
                             for phase, values in observations.items()} for name, target in PROTOCOLS.items()},
            "input_tokens": sum(len(row["input_ids"]) for row in rows.values()),
            "generated_tokens": sum(len(row["output_ids"]) for row in rows.values())}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
