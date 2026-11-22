"""Replay the matched workshop inputs, private-view isolation and final labels."""
import argparse
import hashlib
from pathlib import Path
import json
import re

from transformers import AutoTokenizer

from run import (DIRECT_CAP, FINAL, FINAL_CAP, OPEN_CAP, OPENING, REVISION, REVISION_CAP,
                 ROOT, HERE, FAMILY, make_request, templates)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mechanical(output, target):
    first = output.splitlines()[0] if output.splitlines() else ""
    match = re.fullmatch(r"Workshop decision: (A|B|C|D|IMPASSE|UNRESOLVED)", first)
    label = match.group(1) if match else None
    return {"expected": target, "parsed": label, "exact_label_correct": label == target,
            "words": len(output.split()), "at_most_130_words": len(output.split()) <= 130}


def audit(run):
    launch = json.loads((run / "launch.json").read_text())
    complete = json.loads((run / "complete.json").read_text())
    transcript = run / "transcript.jsonl"
    assert complete["release_sha256"] == digest(transcript)
    assert complete["optimizer_updates"] == launch["optimizer_updates"] == 0
    for path in (HERE / "run.py", ROOT / "packets.py", ROOT / "workshops.json", ROOT / "references.json"):
        assert launch["input_sha256"][path.name] == digest(path)
    rows = [json.loads(line) for line in transcript.read_text().splitlines()]
    records = {r["id"]: r for r in rows}
    assert len(records) == len(rows) == complete["records"] == 16
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    views, names = templates()
    refs = json.loads((ROOT / "references.json").read_text())["families"][FAMILY]["workshop_refs_only"]
    visited = set()

    def check(key, cap, view, task, prior=()):
        row = records[key]
        assert set(row["dependencies"]) <= visited
        expected = make_request(key, cap, view, task, [(rel, records[id_]) for rel, id_ in prior])
        assert all(row[k] == v for k, v in expected.items())
        rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False,
                                               add_generation_prompt=True, enable_thinking=False)
        assert tokenizer.encode(rendered, add_special_tokens=False) == row["input_ids"]
        tokens = row["output_ids"]
        assert tokenizer.decode(tokens, skip_special_tokens=True).strip() == row["output"]
        assert 0 < len(tokens) <= cap and eos not in tokens[:-1]
        assert (tokens[-1] == eos and row["stop"] == "eos") or (
            tokens[-1] != eos and len(tokens) == cap and row["stop"] == "cap")
        visited.add(key)

    check("open-1-shared", OPEN_CAP, views[0]["role-1"], OPENING)
    for v, view in zip(names, views, strict=True):
        check(f"open-2-{v}", OPEN_CAP, view["role-2"], OPENING)
    solo_task = REVISION + " Revise independently. No peer turn is supplied."
    check("solo-1-shared", REVISION_CAP, views[0]["role-1"], solo_task, [("your opening", "open-1-shared")])
    for v, view in zip(names, views, strict=True):
        right = f"open-2-{v}"
        check(f"solo-2-{v}", REVISION_CAP, view["role-2"], solo_task, [("your opening", right)])
        check(f"peer-1-{v}", REVISION_CAP, view["role-1"], REVISION,
              [("your opening", "open-1-shared"), ("other delegate's opening", right)])
        check(f"peer-2-{v}", REVISION_CAP, view["role-2"], REVISION,
              [("your opening", right), ("other delegate's opening", "open-1-shared")])
    report = {}
    for v, view in zip(names, views, strict=True):
        report[v] = {}
        joint = refs[v]["joint_packages"]
        target = joint[0] if joint else "IMPASSE"
        for arm in ("solo", "peer", "analyst"):
            writer = f"final-{arm}-{v}"
            if arm == "analyst":
                check(writer, DIRECT_CAP, view["analyst"], FINAL)
                ids = [writer]
            else:
                left = "solo-1-shared" if arm == "solo" else f"peer-1-{v}"
                right = f"{arm}-2-{v}"
                check(writer, FINAL_CAP, view["writer"], FINAL,
                      [("first role's revised submission", left), ("second role's revised submission", right)])
                ids = ["open-1-shared", f"open-2-{v}", left, right, writer]
            arm_rows = [records[key] for key in ids]
            ceiling = sum(row["cap"] for row in arm_rows)
            assert ceiling == DIRECT_CAP
            report[v][arm] = {
                **mechanical(records[writer]["output"], target),
                "input_tokens": sum(len(row["input_ids"]) for row in arm_rows),
                "generated_tokens": sum(len(row["output_ids"]) for row in arm_rows),
                "ceiling": ceiling, "cap_hits": [row["id"] for row in arm_rows if row["stop"] == "cap"],
            }
    assert visited == records.keys()
    return {"transcript_sha256": digest(transcript), "records": len(records), "family": FAMILY,
            "optimizer_updates": 0, "arms": report}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("run", type=Path)
    print(json.dumps(audit(args.parse_args().run), indent=2))


if __name__ == "__main__":
    main()
