"""Test frozen documentary readers and final records on two new meeting families."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as transfer
import facilitator_witness_writer as writer

HERE = transfer.HERE
PACK = HERE / "facilitator-new-meetings.json"
FAMILY = "facilitator-new-meetings"
runner = transfer.runner
chair = transfer.chair
witness = transfer.witness


def panels():
    for family, meeting in chair.load(PACK).items():
        for index, (proposal, predicate, truth) in enumerate(meeting["proposals"]):
            yield f"{family}-{index}", proposal, predicate, tuple(truth), meeting["sources"]


def source_rows():
    for panel, _, predicate, truth, cards in panels():
        for i, ((speaker, source), gold) in enumerate(zip(cards, truth, strict=True), 1):
            yield f"{panel}/S{i}", speaker, f"{speaker} {predicate}.", source, gold


def requests():
    task = witness.requests()[0]["messages"][0]["content"]
    for key, speaker, claim, source, _ in source_rows():
        yield transfer.prompt(f"{key}/read", witness.CAP, task, {"claim": claim, "source": source})
        yield transfer.prompt(f"{key}/field", writer.CAP, writer.TASK,
                              {"speaker": speaker, "one_speaker_assertion": claim, "source": source})


def syntheses(rows):
    for panel, proposal, _, _, cards in panels():
        sources = {f"S{i}": source for i, (_, source) in enumerate(cards, 1)}
        payload = {"proposed_sentence": proposal, "documentary_passages": sources}
        yield transfer.prompt(f"{panel}/3/pooled", chair.CAP, chair.TASK, payload)
        drafts = {sid: rows[f"{panel}/{sid}/field"]["output"] for sid in sources}
        task = chair.TASK + " Independent desk drafts may help organize the brief. Verify them against their source."
        yield transfer.prompt(f"{panel}/3/independent", chair.CAP, task, payload | {"independent_drafts": drafts})


def episode(generate):
    groups = defaultdict(list)
    for item in requests():
        groups[item["id"].rsplit("/", 1)[1]].append(item)
    final = {}
    for batch in groups.values():
        final.update(generate(batch))
    final.update(generate(list(syntheses(final))))
    return [{"family": FAMILY, "final": final}]


def pins():
    archive = transfer.pins()
    for path in (Path(__file__), PACK, Path(writer.__file__), Path(witness.__file__)):
        archive[str(path.resolve().relative_to(HERE.parents[1]))] = runner.digest(path)
    return archive


def verify(directory):
    with patch.multiple(transfer, local=requests, audits=lambda rows: (), syntheses=syntheses,
                        pins=pins, FAMILY=FAMILY):
        return transfer.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
