"""Recover missing national evidence through a source-owner quote request."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from minurso_deliberation_review import grade_final, historical_sources
from minurso_protected_record import render
from minurso_vote_reconciliation import EVIDENCE, base, requests
from source_record_run import digest

PARENT = EVIDENCE / "minurso-vote-reconciliation"
FAMILY = "western-sahara-source-owner-recovery"
TASK = (
    "You are the Algerian evidence custodian. A previous draft was quarantined because its formal vote claim "
    "conflicted with the official roll call. Recover only the two requested historical statements from your own evidence. "
    "For each field copy one continuous verbatim span from the specified source. Do not paraphrase or add an explanation. "
    "Write exactly two lines with the field names, a colon and the quote. Use MISSING if the source does not answer."
)
FIELDS = {
    "Monitoring": ("DZ-A", "argued that MINURSO should have a human-rights monitoring component",
                   "Which monitoring function did Bendjama argue for?"),
    "Penholder": ("DZ-B", "explained Algeria's deliberate non-participation on the final resolution and said "
                         "the penholder had disregarded Algeria's views",
                  "What explanation did Bendjama give for not participating?"),
}


def recovery_requests():
    official = base.case()["delegate_evidence"]["Algeria"]
    for request, audit in requests():
        if not request["id"].startswith("named-"):
            continue
        assert audit["DZ-DRAFT"]
        body = json.loads(request["messages"][1]["content"])
        yield base.message(request["id"], TASK, {
            "prior_released_draft": body["national_drafts"]["DZ-DRAFT"],
            "evidence": official,
            "fields": {name: {"source": source, "question": question}
                       for name, (source, _, question) in FIELDS.items()},
        }, official, [request["seen"][0]], 150)


def locks():
    inputs = (Path(__file__), Path(base.__file__), Path(base.runner.__file__), base.PACK, base.JUDGE,
              Path(render.__code__.co_filename), PARENT / "protected-records.json", PARENT / "transcript.jsonl")
    return {p.name: digest(p) for p in inputs}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(recovery_requests()))}]


def verify_quotes(text, evidence):
    lines = [line for line in text.splitlines() if line.strip()]
    recognized = {}
    if len(lines) != len(FIELDS):
        return recognized
    for line, (field, (source, required, _)) in zip(lines, FIELDS.items(), strict=True):
        label, found, quote = line.partition(":")
        if not found or label.strip() != field:
            continue
        quote = quote.strip().strip('"“”')
        if quote and quote in evidence[source] and required in quote:
            recognized[field] = {"block": source, "quote": quote}
    return recognized


def software_check():
    evidence = base.case()["delegate_evidence"]["Algeria"]
    clean = "\n".join(f"{name}: {expected}" for name, (_, expected, _) in FIELDS.items())
    assert set(verify_quotes(clean, evidence)) == set(FIELDS)
    detached = "Monitoring: argued that MINURSO should have a human-rights monitoring component\n"
    detached += "Penholder: the penholder had disregarded Algeria's views"
    assert set(verify_quotes(detached, evidence)) == {"Monitoring"}
    assert not verify_quotes("Monitoring: invented\nPenholder: invented", evidence)
    planned = list(recovery_requests())
    assert [r["id"] for r in planned] == ["named-independent", "named-peer"]
    for row in planned:
        payload = json.loads(row["messages"][1]["content"])
        assert "only_counterpart" not in payload and set(payload["evidence"]) == {"DZ-A","DZ-B"}
    return len(planned)


def score(directory):
    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    path = directory / "transcript.jsonl"
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == digest(path)
    rows = list(map(json.loads, path.read_text().splitlines()))
    assert len(rows) == 2 == complete["records"]
    outputs = {r["id"]: r["output"] for r in rows}
    finals = directory / "final-records.json"
    assert complete["final_records_sha256"] == digest(finals)
    assert json.loads(finals.read_text()) == {FAMILY: outputs}
    source = historical_sources()
    originals = {r["id"]: r for r, _ in requests()}
    results = {}
    for row, old_request in zip(rows, recovery_requests(), strict=True):
        assert all(row[k] == v for k, v in old_request.items())
        found = verify_quotes(row["output"], source) if row["ended"] else {}
        r = originals[row["id"]]
        draft_view = json.loads(r["messages"][1]["content"])["national_drafts"]
        text, met, _, guard = render(r, draft_view)
        lines = text.splitlines()
        fragments = []
        for field, rubric_id, surface in (
            ("Monitoring", "monitoring-position", "Algeria argued for a human-rights monitoring component in MINURSO"),
            ("Penholder", "penholder", "Algeria said the penholder disregarded its views, explaining its non-participation"),
        ):
            if field not in found:
                continue
            claim = surface + " [DZ-DRAFT]."
            local = found[field]
            fragments.append(claim)
            met[rubric_id] = [claim, [local["block"]], [r["seen"][0], claim]]
        if fragments:
            lines[2] = "Algeria: " + " ".join(fragments)
            draft_view["DZ-DRAFT"] = " ".join(fragments)
        record = {**r, "output": "\n".join(lines), "ended": True, "input_ids": [], "output_ids": []}
        visible = dict(zip(record["seen"], draft_view.values(), strict=True))
        evaluation = grade_final(record, {"met": met, "guard": guard}, visible, [])
        for unused in ("input_tokens", "output_tokens", "finish"):
            evaluation.pop(unused)
        results[row["id"]] = {"retained_quotes": found, "record": record["output"], "review": evaluation,
                               "extra_input_tokens": len(row["input_ids"]),
                               "extra_output_tokens": len(row["output_ids"])}
    return {"scope": "Adaptive closed-field recovery. The source owner has both Algerian primary-source paraphrase blocks. "
                     "Only predeclared exact support-bearing spans can be rendered. The additional call has no peer draft. "
                     "Public wording is fixed from the authored reference. This is a fixture-specific proof compilation experiment.",
            "trace_sha256": complete["transcript_sha256"], "arms": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({"requests": software_check(), "hashes": locks()}, indent=2))
    elif args.mode == "run":
        if args.directory is None or args.model is None:
            cli.error("run requires directory and model")
        software_check()
        with patch.multiple(base.runner, episode=episode, locks=locks):
            base.runner.run(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
