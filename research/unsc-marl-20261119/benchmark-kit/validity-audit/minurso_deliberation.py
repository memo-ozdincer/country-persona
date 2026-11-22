"""Run a matched independent versus peer-visible natural-language revision experiment."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner
from minurso_receipt_writer import CAP, HEADINGS, JUDGE, PACK, case

FAMILY = "western-sahara-language-deliberation"
ARMS = ("independent", "peer")
ROLES = ("Algeria", "Switzerland")
DELEGATE_CAP = 128
OPEN = (
    "Write your draft national account for the chair in two or three sentences, then ask the other delegation one "
    "specific question about its historical position which would improve the final record. Use your own national "
    "evidence and the public dossier. Use evidence IDs. No introductory prose. At most 65 words in total."
)
REVISE = (
    "Write your final proposed national account in at most 55 words. Audit your own draft against the delivered "
    "evidence. If another draft is visible, answer any question to your delegation that you can answer from your "
    "own evidence, and correct any material confusion about your delegation. Preserve the key claims from your "
    "own evidence with IDs. Keep statements, reasons and votes distinct. Output only the revised national account."
)
CHAIR = (
    "Write the final historical record using only the evidence actually delivered below. The national drafts may contain "
    "mistakes. Use them for actual national positions only when the attribution and proposition are explicit. "
    "Use the public dossier for vote tallies, scope of adopted authority and proposal status. Include the five requested "
    "headings and cite MAIN, AMEND, TEXT, DZ-DRAFT or CH-DRAFT on the lines they support. Keep distinct instruments and "
    "qualifiers. Omit information that the public dossier and national drafts do not establish. No preamble or afterword. "
    "At most 155 words."
)
DRAFT_IDS = ("DZ-DRAFT", "CH-DRAFT")


def message(id_, system, body, evidence_ids, seen, cap):
    return {"id": id_, "evidence_ids": list(evidence_ids), "seen": list(seen), "cap": cap,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def episode(generate):
    source = case()
    public = source["docket"]
    role_evidence = [{**public, **source["delegate_evidence"][name]} for name in ROLES]
    spec = [f"Prepare a retrospective {name} national account. Separate Council acts from national positions."
            for name in ROLES]
    opens = [message(f"open-{i}", spec[i], {"evidence": evidence, "task": OPEN},
                     evidence, [], DELEGATE_CAP)
             for i, evidence in enumerate(role_evidence)]
    openings = generate(opens)
    changes = []
    for arm in ARMS:
        for i, evidence in enumerate(role_evidence):
            own = (f"open-{i}",)
            seen = own if arm == "independent" else (*own, f"open-{1-i}")
            drafts = {ROLES[int(key[-1])]: openings[key]["output"] for key in seen}
            changes.append(message(f"{arm}-{i}", spec[i], {"evidence": evidence, "task": REVISE, "drafts": drafts},
                                   evidence, seen, DELEGATE_CAP))
    revisions = generate(changes)
    final_requests = []
    for arm in ARMS:
        seen = [f"{arm}-{i}" for i in range(2)]
        deliver = {k: revisions[v]["output"] for k, v in zip(DRAFT_IDS, seen, strict=True)}
        final_requests.append(message(f"chair-{arm}", CHAIR, {"headings": HEADINGS, "public_evidence": public,
                                                             "national_drafts": deliver},
                                      (*public, *DRAFT_IDS), seen, CAP))
    return [{"family": FAMILY, "final": generate(final_requests)}]


def locks():
    return {f.name: runner.digest(f) for f in (Path(__file__), Path(runner.__file__), PACK, JUDGE,
                                                 Path(__file__).with_name("minurso_receipt_writer.py"))}


def check():
    rows = {}
    def capture(batch):
        result = {r["id"]: {**r, "output": f"mock {r['id']}"} for r in batch}
        rows.update(result)
        return result
    episode(capture)
    assert len(rows) == 8
    for i in range(2):
        independent, peer = (rows[f"{a}-{i}"] for a in ARMS)
        assert independent["seen"] == peer["seen"][:1] == [f"open-{i}"]
        assert set(peer["seen"]) == {"open-0", "open-1"}
        assert independent["evidence_ids"] == peer["evidence_ids"]
        before, after = (json.loads(r["messages"][1]["content"]) for r in (independent, peer))
        assert before["task"] == after["task"] and before["evidence"] == after["evidence"]
        assert set(before["drafts"]) == {ROLES[i]} and set(after["drafts"]) == set(ROLES)
    for a in ARMS:
        assert set(rows[f"chair-{a}"]["evidence_ids"]) == {*case()["docket"], *DRAFT_IDS}
    return {"calls": len(rows), "arm_output_ceiling": 4 * DELEGATE_CAP + CAP, "hashes": locks()}


def replay(directory, verify_tokens=True):
    start = json.loads((directory / "launch.json").read_text())
    finish = json.loads((directory / "complete.json").read_text())
    trace = directory / "transcript.jsonl"
    assert start["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(trace)
    raw = list(map(json.loads, trace.read_text().splitlines()))
    rows = {r["id"]: r for r in raw}
    assert len(raw) == len(rows) == finish["records"] == 8
    tokenizer = None
    if verify_tokens:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(start["model"], local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids("<|im_end|>")

    def read(batch):
        output = {}
        for ref in batch:
            row = rows.pop(ref["id"])
            assert all(row[k] == v for k, v in ref.items())
            if tokenizer is not None:
                assert runner.encode(tokenizer, ref) == row["input_ids"]
                ids = row["output_ids"]
                assert 0 < len(ids) <= ref["cap"] and eos not in ids[:-1]
                assert (ids[-1] == eos) == row["ended"]
                assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
            output[ref["id"]] = row
        return output

    item, = episode(read)
    finals = directory / "final-records.json"
    assert not rows and runner.digest(finals) == finish["final_records_sha256"]
    assert json.loads(finals.read_text()) == {FAMILY: {k: v["output"] for k, v in item["final"].items()}}
    return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "run", "replay"))
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), indent=2))
    elif args.mode == "run":
        if args.model is None or args.directory is None:
            parser.error("run requires directory and model")
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), indent=2, ensure_ascii=False))
