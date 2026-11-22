"""Transfer the frozen typed router to a new protected historical case."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import space_transfer_episode as common
import space_transfer_judge as replay_util

ROOT = common.ROOT
TASK = ROOT / "crossbench/unifil-record.json"
REFERENCE = TASK.with_name("unifil-reserve.json")
FROZEN = common.OUT / "space-final-routing-policy.json"
NAME = "unifil-final-transfer"
OUT = common.OUT / NAME
FIELDS = ("brazil", "china", "russia")
PUBLIC_IDS = ("vote", "operative")
BODY_CAP = 128
BODY_WORDS = 75
PUBLIC = (
    "On 31 August 2023, the Security Council voted on France's draft S/2023/641. It adopted resolution 2695 (2023) "
    "by 13 votes to none, with China and Russia abstaining. The existing UNIFIL mandate was extended until "
    "31 August 2024. The resolution reaffirmed UNIFIL's independence in carrying out mandated tasks without "
    "prior permission, while preserving coordination with Lebanon's Government under the status-of-forces agreement."
)
NOTE = (
    "Write one source-faithful sentence for a Security Council record in no more than 32 words. Explicitly name the "
    "speaker's country and preserve all material distinctions in its position. Use the source only. No heading or citations."
)
BODY = (
    "Write only the supplemental paragraph of a Security Council record, at most 75 words. The fixed procedure "
    "will be printed as supplied. Describe each national rationale in the supplemental evidence with explicit "
    "attribution. If both Brazil and China are supplied, state a concrete shared position and the specific "
    "difference about the text. Omit unavailable national views. Use no headings or citations."
)


def packet():
    return json.loads(TASK.read_text())


def sources():
    return {b["id"]: b["text"] for b in packet()["evidence"]}


def notes():
    src = sources()
    for name in FIELDS:
        yield common.request(f"note-{name}", NOTE, {"source": {name: src[name]}}, 64, [name])


def bodies(notes_by_id):
    def request(arm, mask, source):
        allowed = [s for i, s in enumerate(FIELDS) if mask & (1 << i)]
        body = {"fixed_procedure": PUBLIC, "supplemental_evidence": {s: source[s] for s in allowed}}
        return common.request(f"{arm}-{mask}", BODY, body, BODY_CAP, [*PUBLIC_IDS, *allowed])
    for mask in range(1, 8):
        yield request("team", mask, notes_by_id)
    for mask in (1, 3, 7):
        yield request("solo", mask, sources())


def locks():
    paths = (Path(__file__), Path(common.__file__), TASK, REFERENCE, FROZEN, Path(common.runner.__file__))
    return {str(p.resolve().relative_to(ROOT)): common.runner.digest(p) for p in paths}


def check():
    packet_ids = tuple(sources())
    assert packet_ids == (*PUBLIC_IDS, *FIELDS)
    assert len(packet()["rubric"]) == 10
    assert sum(r["weight"] for r in packet()["rubric"]) == 70
    refs = json.loads(REFERENCE.read_text())
    votes = refs["reference_votes"]
    assert len(votes) == 15 and sum(v == "Y" for v in votes.values()) == 13
    assert {c for c, v in votes.items() if v == "A"} == {"CHINA", "RUSSIAN FEDERATION"}
    assert refs["unbench"]["author_train_matching_id_rows"] == 0
    prior = json.loads(FROZEN.read_text())
    assert prior["updates"] == 280 and prior["rubric_sha256"] != common.runner.digest(TASK)
    world = prior["worlds"]["best-contrast"]
    assert world["interactive"]["receipt"] == 3 and world["independent"]["receipt"] == world["erased_receipt"] == 1
    return {"national_note_calls": 3, "equal_budget_final_calls": 10, "declared_bit_order": FIELDS,
            "full_rubric_points": 70, "public_rubric_points": 35, "frozen_policy_sha256": locks()[
                str(FROZEN.relative_to(ROOT))]}


def run(model, directory):
    def episode(generate):
        items = generate(list(notes()))
        transformed = {key: items[f"note-{key}"]["output"] for key in FIELDS}
        assert all(items[f"note-{key}"]["ended"] for key in FIELDS)
        return [{"family": NAME, "final": generate(list(bodies(transformed)))}]
    with patch.multiple(common.runner, episode=episode, locks=locks):
        common.runner.run(model, directory)


def replay(directory):
    launch = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    transcript = directory / "transcript.jsonl"
    rows = list(map(json.loads, transcript.read_text().splitlines()))
    transformed = {r["id"].removeprefix("note-"): r["output"] for r in rows[:3]}
    expected = [*notes(), *bodies(transformed)]
    assert launch["sha256"] == locks()
    assert end["transcript_sha256"] == common.runner.digest(transcript)
    assert len(rows) == end["records"] == len(expected) == 13
    for req, actual in zip(expected, rows, strict=True):
        assert all(actual[k] == v for k, v in req.items())
        assert 0 < len(actual["output_ids"]) <= req["cap"]
    final = directory / "final-records.json"
    assert end["final_records_sha256"] == common.runner.digest(final)
    assert json.loads(final.read_text()) == {NAME: {r["id"]: r["output"] for r in rows[3:]}}
    return {r["id"]: r for r in rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay-tokens"))
    cli.add_argument("--model", type=Path)
    cli.add_argument("--directory", type=Path, default=OUT)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), indent=2))
    elif args.mode == "run":
        check()
        if args.model is None:
            cli.error("run needs --model")
        run(args.model, args.directory)
    else:
        assert len(replay(args.directory)) == replay_util.replay_tokens(args.directory)
        print("All 13 generation traces match the locked inputs and outputs.")
