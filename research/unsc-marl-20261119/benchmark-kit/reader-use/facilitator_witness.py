"""Require an exact documentary witness before using a local relation in routing."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
import sys
from unittest.mock import patch

import facilitator_policy_transfer as transfer

HERE = transfer.HERE
sys.path.insert(0, str(HERE.parent / "validity-audit"))
import source_record_run as runner

FAMILY = "facilitator-witness"
CAP = 105


def cases():
    for family, docs in transfer.packets().items():
        for number, (proposal, acts, truth) in enumerate(transfer.PANELS[family]):
            for i, ((speaker, passage), act) in enumerate(zip(docs, acts, strict=True)):
                yield f"{family}/{number}/{i}", f"{speaker} {act}.", passage, truth[i]
    pack = transfer.protocol.inputs()
    for row, reference in zip(pack["inputs"], pack["keys"], strict=True):
        if row["id"] % 4 != 3:
            continue
        proposals = transfer.protocol.SIDES[row["docket"]][(row["id"]//4) % 3]
        for i, ((sid, passage), claim) in enumerate(zip(row["sources"].items(), proposals, strict=True)):
            yield f"{row['docket']}/{(row['id']//4)%3}/{i}", claim, passage, reference["source_relations"][sid]


def requests():
    task = ("Decide whether the source explicitly supports the exact position in the claim, explicitly contradicts it, "
            "or leaves it unknown. Check the named speaker, the act, and its qualification separately. "
            "A statement about a related issue, narrower claim, or a different delegation cannot supply the missing fact. "
            "Do not infer support from silence. If the source supports or contradicts the claim, return one line "
            "'supports|EXACT SOURCE WORDS' or 'contradicts|EXACT SOURCE WORDS'. "
            "Copy a contiguous passage furnishing the decisive wording, without changing quotation marks or punctuation "
            "and without adding quotes. If the source leaves any essential part open, write just unknown.")
    return [{"id": key, "cap": CAP, "messages": [
        {"role": "system", "content": task},
        {"role": "user", "content": json.dumps({"claim": claim, "source": passage}, ensure_ascii=False)}]}
        for key, claim, passage, _ in cases()]


def episode(generate):
    rows = requests()
    generated = {}
    for start in range(0, len(rows), 14):
        generated.update(generate(rows[start:start+14]))
    return [{"family": FAMILY, "final": generated}]


def hashes():
    files = {Path(__file__), Path(runner.__file__), *(HERE.parents[1] / p for p in transfer.locks()),
             *(HERE.parents[1] / p for p in transfer.protocol.hashes())}
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def replay(directory):
    from transformers import AutoTokenizer

    launch, end = (transfer.protocol.delivery.load(directory / name) for name in ("launch.json", "complete.json"))
    trace, final = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == hashes() and end["transcript_sha256"] == runner.digest(trace)
    assert end["final_records_sha256"] == runner.digest(final)
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    assert len(rows) == end["records"] == 28
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    stop = token.convert_tokens_to_ids("<|im_end|>")
    for req in requests():
        row = rows[req["id"]]
        assert all(row[k] == v for k, v in req.items())
        assert runner.encode(token, req) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= CAP and stop not in ids[:-1] and row["ended"] == (ids[-1] == stop)
        assert row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert transfer.protocol.delivery.load(final) == {FAMILY: {k: v["output"] for k, v in rows.items()}}
    return rows


def read_witness(output, source):
    label, delim, quote = output.partition("|")
    vote = label.strip().casefold()
    quote = quote.strip()
    if vote == "unknown" and not delim:
        return vote, vote, None
    if vote not in ("supports", "contradicts") or not delim:
        return None, "unknown", None
    accepted = vote if quote and quote in source else "unknown"
    return vote, accepted, quote


def score(directory):
    rows = replay(directory)
    cases_by_id = {}
    for key, claim, text, expected in cases():
        output = rows[key]["output"]
        claimed, admitted, excerpt = read_witness(output, text) if rows[key]["ended"] else (None, "unknown", None)
        cases_by_id[key] = {"claim": claim, "expected": expected, "proposed_label": claimed,
                           "admitted": admitted, "witness": excerpt, "raw": output}
    # The model's proposed relation and runtime-admitted relation are both
    # recorded. Authenticated quotes establish text provenance, not entailment.
    panels = []
    for family, proposals in transfer.PANELS.items():
        for j, (proposal, _, truth) in enumerate(proposals):
            panel = [cases_by_id[f"{family}/{j}/{i}"] for i in range(2)]
            got = tuple(r["admitted"] for r in panel)
            expected = transfer.base.decision(truth, transfer.base.TARGETS)
            action = transfer.base.decision(got, transfer.base.TARGETS)
            panels.append({"family": family, "proposal": proposal, "truth": truth, "admitted": got,
                           "full_expected": expected, "full_action": action})
    return {"scope": "Frozen next-text generation with exact-substring witness admission. "
                     "Source excerpts and decomposed subclaims are supplied. "
                     "An admitted witness still needs semantic evaluation against the authored label.",
            "summary": {family: {key: sum(fn(r) for name, r in cases_by_id.items() if name.startswith(family+"/"))
                                 for key, fn in {
                                     "count": lambda r: True,
                                     "correct": lambda r: r["admitted"] == r["expected"],
                                     "false_support": lambda r: r["admitted"] == "supports" and r["expected"] != "supports",
                                     "false_contradiction": lambda r: r["admitted"] == "contradicts" and r["expected"] != "contradicts",
                                     "nonnull_labels_rejected": lambda r: r["proposed_label"] in ("supports", "contradicts") and r["admitted"] == "unknown",
                                 }.items()} for family in ("unifil", "colombia", "haiti", "mali")},
            "full_packet_decisions": panels, "reads": cases_by_id}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=hashes):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
