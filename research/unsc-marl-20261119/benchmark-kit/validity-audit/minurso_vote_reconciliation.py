"""Test a narrow authoritative-roll-call check on archived natural revisions."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import minurso_deliberation as base

EVIDENCE = Path(__file__).resolve().parent.parent / "evidence"
ARCHIVES = {"original": EVIDENCE / "minurso-deliberation", "named": EVIDENCE / "minurso-deliberation-named"}
FAMILY = "western-sahara-reconciled"
CLAIM = re.compile(
    r"^\s*(?:Algeria|the Algerian delegation)\s+(?:formally\s+)?"
    r"(?P<vote>abstained|voted in favour|voted in favor|voted against|did not participate)"
    r"\s+(?:on\s+the\s+vote\s+on|on|in the vote on)\s+"
    r"(?:Resolution\s+2756\b|S/2024/796\b|MAIN\b)", re.IGNORECASE
)
# The source text is already public to the chair. The audit asks only whether
# this one unambiguous assertion contradicts that source.
EXPECTED = "did not participate"


def reconcile(text, public):
    assert "one member not participating (Algeria)" in public["MAIN"]
    kept = []
    removed = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        match = CLAIM.match(sentence)
        if match and match["vote"].lower() != EXPECTED:
            removed.append({"span": sentence, "source": "MAIN", "observed_vote": match["vote"]})
        else:
            kept.append(sentence)
    if not removed:
        return text, removed
    return " ".join(kept), removed


def traces():
    result = {}
    for label, directory in ARCHIVES.items():
        launch = json.loads((directory / "launch.json").read_text())
        path = directory / "transcript.jsonl"
        done = json.loads((directory / "complete.json").read_text())
        assert done["transcript_sha256"] == base.runner.digest(path)
        end = json.loads((directory / "final-records.json").read_text())
        assert done["final_records_sha256"] == base.runner.digest(directory / "final-records.json")
        by_id = {row["id"]: row for row in map(json.loads, path.read_text().splitlines())}
        assert len(by_id) == done["records"] == 8
        for arm in base.ARMS:
            original = by_id[f"chair-{arm}"]
            assert end[base.FAMILY][original["id"]] == original["output"]
            body = json.loads(original["messages"][1]["content"])
            previous = body["national_drafts"]
            assert list(previous) == list(base.DRAFT_IDS)
            assert all(previous[draft] == by_id[turn]["output"]
                       for draft, turn in zip(base.DRAFT_IDS, original["seen"], strict=True))
            result[f"{label}-{arm}"] = original, body
    return result


def requests():
    for variant, (original, body) in traces().items():
        updated, audit = {}, {}
        for key, text in body["national_drafts"].items():
            updated[key], audit[key] = reconcile(text, body["public_evidence"])
        packet = {**body, "national_drafts": updated}
        request = base.message(variant, original["messages"][0]["content"], packet,
                               original["evidence_ids"], original["seen"], original["cap"])
        yield request, audit


def locks():
    files = [Path(__file__), Path(base.__file__), Path(base.runner.__file__), base.PACK, base.JUDGE]
    files.extend(f / a for f in ARCHIVES.values() for a in ("transcript.jsonl", "complete.json", "final-records.json"))
    return {"/".join(p.parts[-2:]): base.runner.digest(p) for p in files}


def episode(generate):
    return [{"family": FAMILY, "final": generate([r for r, _ in requests()])}]


def check():
    pairs = list(requests())
    assert len(pairs) == 4
    assert all(len(audit["DZ-DRAFT"]) == 1 and not audit["CH-DRAFT"] for _, audit in pairs)
    public = base.case()["docket"]
    negatives = (
        "Algeria did not participate on Resolution 2756 (2024).",
        "Algeria abstained on S/2024/798.",
        "Switzerland abstained on S/2024/798.",
        "Did Algeria abstain on Resolution 2756 (2024)?",
        "In an earlier meeting, Algeria abstained on a different resolution.",
    )
    assert all(reconcile(t, public) == (t, []) for t in negatives)
    return {"reconciled": {row["id"]: audit for row, audit in pairs}, "hashes": locks()}


def replay(directory, verify_tokens=True):
    launch = json.loads((directory / "launch.json").read_text())
    done = json.loads((directory / "complete.json").read_text())
    archive = directory / "transcript.jsonl"
    assert launch["sha256"] == locks() and done["transcript_sha256"] == base.runner.digest(archive)
    rows = list(map(json.loads, archive.read_text().splitlines()))
    assert len(rows) == done["records"] == 4
    tokenizer = None
    if verify_tokens:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for row, (expected, _) in zip(rows, requests(), strict=True):
        assert all(row[k] == v for k, v in expected.items())
        if tokenizer is not None:
            assert base.runner.encode(tokenizer, expected) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1]
            assert (ids[-1] == eos) == row["ended"]
            assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
    finals = directory / "final-records.json"
    assert done["final_records_sha256"] == base.runner.digest(finals)
    assert json.loads(finals.read_text()) == {FAMILY: {row["id"]: row["output"] for row in rows}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    elif args.mode == "run":
        if args.directory is None or args.model is None:
            cli.error("run requires --model and directory")
        check()
        with patch.multiple(base.runner, episode=episode, locks=locks):
            base.runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), ensure_ascii=False, indent=2))
