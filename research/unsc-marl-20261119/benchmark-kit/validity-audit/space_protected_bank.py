"""Generate protected Outer Space records for every receipt with frozen routing tables."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import space_atomic_guard as guard
import space_transfer_episode as study
import space_transfer_judge as baseline

NAME = "space-protected-receipt-bank"
OUT = study.OUT / NAME
OLD = study.OUT / study.NAME
POLICY = study.OUT / "space-final-routing-policy.json"
BODY_CAP = 128
BODY_WORDS = 75
PUBLIC = (
    "On 24 April 2024, China and Russia's amendment S/2024/323 failed 7–7–1 for insufficient affirmative votes. "
    "Japan voted no and China yes. The separate vote on the Japan–US draft S/2024/302 was 13–1–1. Russia's "
    "permanent-member veto blocked adoption. Japan voted yes and China abstained. The April votes created no "
    "new Council authorization."
)
SYSTEM = (
    "Write only the supplemental paragraph of a Security Council record, at most 75 words. The fixed April "
    "paragraph will already be printed. Leave its procedure and roll call to that paragraph. Describe each "
    "national rationale actually in the supplemental evidence, with explicit attribution. If both national "
    "accounts are supplied, identify evidenced shared ground and the concrete disagreement. If the May vote "
    "is supplied, explicitly state its date, symbol, separate stage, tally and reason it failed. "
    "Omit unavailable facts and cite no IDs. Return the supplemental paragraph only."
)


def archived():
    rows, _ = baseline.audit_generation(OLD, POLICY)
    notes = {}
    for key in study.FIELDS[:2]:
        candidates = {r["output"] for r in rows.values() if r["evidence_ids"] == [key] and r["ended"]}
        note, = candidates
        notes[key] = note
    contest = json.loads(POLICY.read_text())["worlds"]
    assert contest["best-contrast"]["interactive"]["receipt"] == 3
    assert contest["best-contrast"]["erased_receipt"] == contest["best-contrast"]["independent"]["receipt"] == 1
    assert contest["lowest-contrast"]["interactive"]["receipt"] == contest["lowest-contrast"]["independent"]["receipt"] == 3
    return notes


def may_request():
    key = study.FIELDS[2]
    return study.request("may-note", study.NOTE_PROMPT,
                         {"task": study.GUIDES[2], "source": {key: study.blocks()[key]}},
                         study.NOTE_CAP, [key])


def body_requests(recovered):
    def item(mode, mask, source):
        allowed = [name for i, name in enumerate(study.FIELDS) if mask & (1 << i)]
        body = {"fixed_april_paragraph": PUBLIC, "supplemental_evidence": {name: source[name] for name in allowed}}
        return study.request(f"{mode}-{mask}", SYSTEM, body, BODY_CAP, [*study.PUBLIC, *allowed])

    for mask in range(1, 8):
        yield item("team", mask, recovered)
    for mask in (1, 3, 7):
        yield item("solo", mask, study.blocks())


def locks():
    paths = (Path(__file__), Path(study.__file__), Path(baseline.__file__), Path(guard.__file__),
             Path(study.runner.__file__), study.TASK, study.PROVENANCE, OLD / "transcript.jsonl", POLICY)
    return {str(p.resolve().relative_to(study.ROOT)): study.runner.digest(p) for p in paths}


def check():
    refs = json.loads(study.PROVENANCE.read_text())["retrospective_references"]
    for key, yes, no, abstain in (("S/2024/323", 7, 7, 1), ("S/2024/302", 13, 1, 1)):
        vote = refs[key]["votes"]
        assert [sum(x == side for x in vote.values()) for side in "YNA"] == [yes, no, abstain]
        assert (vote["JAPAN"], vote["CHINA"]) == (("N", "Y") if key.endswith("323") else ("Y", "A"))
    assert refs["S/2024/302"]["votes"]["RUSSIAN FEDERATION"] == "N"
    assert len(PUBLIC.split()) + BODY_WORDS <= 140
    return {"notes_reused": archived(), "body_calls": 10, "body_cap": BODY_CAP}


def run(model, directory):
    notes = archived()

    def episode(generate):
        may = generate([may_request()])["may-note"]
        assert may["ended"]
        finals = generate(list(body_requests({**notes, study.FIELDS[2]: may["output"]})))
        return [{"family": NAME, "final": finals}]

    with patch.multiple(study.runner, episode=episode, locks=locks):
        study.runner.run(model, directory)


def replay(directory):
    launch = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    transcript = directory / "transcript.jsonl"
    records = list(map(json.loads, transcript.read_text().splitlines()))
    expected = [may_request(), *body_requests({**archived(), study.FIELDS[2]: records[0]["output"]})]
    assert launch["sha256"] == locks() and study.runner.digest(transcript) == end["transcript_sha256"]
    assert len(records) == end["records"] == len(expected) == 11
    for actual, req in zip(records, expected, strict=True):
        assert all(actual[k] == v for k, v in req.items())
        assert 0 < len(actual["output_ids"]) <= req["cap"]
    output = directory / "final-records.json"
    assert study.runner.digest(output) == end["final_records_sha256"]
    assert json.loads(output.read_text()) == {NAME: {r["id"]: r["output"] for r in records[1:]}}
    return {r["id"]: r for r in records}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("check", "run", "replay"))
    p.add_argument("--model", type=Path)
    p.add_argument("--directory", type=Path, default=OUT)
    args = p.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    elif args.mode == "run":
        if args.model is None:
            p.error("run requires --model")
        check()
        run(args.model, args.directory)
    else:
        rows = replay(args.directory)
        assert baseline.replay_tokens(args.directory) == len(rows)
        print(json.dumps({k: {"ended": r["ended"], "words": len(r["output"].split())}
                          for k, r in rows.items()}, indent=2))
