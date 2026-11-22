"""Compare peer, independent and solo writing from the same dossier."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_prospective_2593 as source

EVIDENCE = source.HERE / "facilitator-matched-2593-evidence"
FAMILY = "facilitator-matched-2593"
ARMS = ("independent", "peer", "solo")
RUNNER = source.RUNNER
NOTE = (
    "Prepare a documentary working note of at most 52 words for a Security Council meeting record. "
    "Your assigned focus is one delegation. Preserve every distinct material fact in its authorized source. "
    "Other sources and working notes, if present, help you spot distinctions or missing links. "
    "Attribute claims to their documented speaker. Do not copy information from another speaker into your "
    "assigned speaker's account or infer the contents of a joint proposal. State a cross-speaker relation "
    "only if the authorized source establishes it. Return only the note."
)
FINAL = (
    "Write a source-faithful Security Council meeting record in at most 210 words. Give the decision, "
    "vote and draft sponsors, then the operative provisions and delegation accounts. Preserve the operative "
    "force of each Council action. Keep the three national positions separate, identify the relation between "
    "the two abstainers' explanations and distinguish their stated reasons from the Council's decision. "
    "Ground every material claim in the public Council facts or the authorized national sources. "
    "Use the working notes as suggestions and check them against those sources. Return only the record."
)


def dossier():
    packet = source.packet()
    cards = {c["speaker"]: c["source"] for c in packet["cards"]}
    return packet["public"], cards


def note(key, speaker, extra=None):
    public, cards = dossier()
    payload = {"assigned_speaker": speaker, "authorized_source": cards[speaker]}
    if extra:
        payload.update(extra)
    return source.live.prompt(key, 92, NOTE, payload)


def local():
    _, cards = dossier()
    for index, speaker in enumerate(tuple(cards)[:2]):
        yield note(f"private/open{index}", speaker)
    public, cards = dossier()
    yield note("solo/open0", next(iter(cards)), {"public_council_facts": public, "national_sources": cards})


def audits(rows):
    public, cards = dossier()
    speakers = tuple(cards)
    earlier = {speakers[i]: rows[f"private/open{i}"]["output"] for i in range(2)}
    yield note("independent/last", speakers[2])
    yield note("peer/last", speakers[2], {"earlier_working_notes": earlier})
    yield next_solo(rows, 1)
    if "solo/open1" in rows:
        yield next_solo(rows, 2)


def next_solo(rows, index):
    public, cards = dossier()
    speakers = tuple(cards)
    return note(f"solo/open{index}", speakers[index],
                {"public_council_facts": public, "national_sources": cards,
                 "earlier_working_notes": {speakers[i]: rows[f"solo/open{i}"]["output"] for i in range(index)}})


def finals(rows):
    public, cards = dossier()
    for arm in ARMS:
        ids = trace(arm)[:-1]
        notes = {speaker: rows[key]["output"] for speaker, key in zip(cards, ids, strict=True)}
        yield source.live.prompt(f"{arm}/final", 384, FINAL, {"public_council_facts": public,
                                 "national_sources": cards, "working_notes": notes})


def trace(arm):
    starts = ["solo/open0", "solo/open1", "solo/open2"] if arm == "solo" else [
        "private/open0", "private/open1", f"{arm}/last"]
    return [*starts, f"{arm}/final"]


def episode(generate):
    rows = generate(list(local()))
    rows.update(generate(list(audits(rows))))
    rows.update(generate([next_solo(rows, 2)]))
    rows.update(generate(list(finals(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    return {**source.pins(), **{str(p.relative_to(source.HERE.parents[1])): RUNNER.digest(p) for p in
                              (Path(__file__).resolve(), EVIDENCE / "protocol.md")}}


def verify(directory):
    base = source.live.common.reused.previous.prior
    with patch.multiple(base, local=local, audits=audits, syntheses=finals, pins=pins, FAMILY=FAMILY):
        return base.read(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
