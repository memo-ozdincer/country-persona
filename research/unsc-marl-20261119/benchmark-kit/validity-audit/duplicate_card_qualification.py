"""Check whether a closed-evidence checklist preserves the China qualification."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import duplicate_card_modular as modular
import duplicate_card_transfer as transfer
import source_record_run as runner

CHECKLIST = (
    "Write China's position in one or two compact sentences, at most 28 words. Include each documented item: "
    "the vote, the substantive reason, whether the speaker said there was time for more consultation, "
    "the Panel's independence, the proposed sanctions time limit and the periodic reviews. Treat each item "
    "as distinct. If an item is absent, omit it. Cite [CHINA]. Use only the supplied passage."
)
QUALIFICATION = " and consultation time remained"


def suite():
    base, = (row for row in transfer.suite() if row["evidence_ids"] == ["CHINA"])
    payload = json.loads(base["messages"][-1]["content"])
    text = payload["evidence"]["CHINA"]
    first, second = text.split(". ", maxsplit=1)
    assert text.count(QUALIFICATION) == 1
    for variant, passage in (
        ("same_card", text),
        ("reordered_card", f"{second} {first}."),
        ("withheld_qualification", text.replace(QUALIFICATION, "", 1)),
    ):
        item = {"task": CHECKLIST, "evidence": {"CHINA": passage}}
        yield {**base, "id": base["id"].replace("/CHINA/", f"/{variant}/"),
               "messages": [base["messages"][0],
                            {"role": "user", "content": json.dumps(item, ensure_ascii=False)}]}


def episode(generate):
    batch = list(suite())
    return [{"family": batch[0]["id"].split("/")[0], "final": generate(batch)}]


def locks():
    return {**transfer.locks(), f"validity-audit/{Path(__file__).name}": runner.digest(Path(__file__))}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({"suite": list(suite()), "sha256": locks()}, indent=2, ensure_ascii=False))
    elif args.directory is None:
        cli.error("directory is required")
    elif args.mode == "run":
        if args.model is None:
            cli.error("--model is required")
        with patch.multiple(runner, locks=locks, episode=episode):
            runner.run(args.model, args.directory)
    else:
        expected = locks()
        with patch.multiple(modular, suite=suite, locks=lambda: expected):
            print(json.dumps(modular.replay(args.directory), indent=2))
