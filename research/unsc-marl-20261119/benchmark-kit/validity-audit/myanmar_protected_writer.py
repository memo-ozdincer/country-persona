"""Generate source-local components for the frozen Myanmar routing transfer."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import mali_protected_writer as archive

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
TASK = PROJECT / "crossbench/myanmar/historical-task.json"
REFERENCES = TASK.with_name("references.json")
EVIDENCE = HERE.parent / "evidence"
TRAIN = EVIDENCE / "mali-protected-writer/policy-fit.json"
FAMILY = "myanmar-protected-transfer"
CAP = 80
MAX_WORDS = 35
RECORD_WORDS = 200
FIELDS = {
    "uk": "Identify the sponsor and why it welcomed the decision. Preserve who it consulted and what it prioritized.",
    "india": "Explain India's national reason for its vote, including its position on regional concerns and diplomatic approach.",
    "chair": "Describe the sequence of procedural and national roles. Identify the actor in each capacity.",
}
PUBLIC = (
    "On 21 December 2022, the Security Council adopted draft S/2022/980 as resolution 2669 (2022) by 12 votes in "
    "favour, none against and three abstentions. The United Kingdom voted in favour. China, India and Russia "
    "abstained [vote].\n\n"
    "The resolution demanded an immediate end to violence, called for humanitarian access and acknowledged ASEAN's "
    "central role. It requested an oral report to the Council from the Secretary-General or his Special Envoy by "
    "15 March 2023, in coordination with the ASEAN Special Envoy, on UN support for ASEAN's Five-Point Consensus [mandate]."
)
PUBLIC_UNITS = {
    "draft-act": "vote", "vote-count": "vote", "humanitarian": "mandate",
    "asean": "mandate", "reporting": "mandate", "authority": "mandate",
}
RECEIPT_UNITS = {
    "uk": (1, ("vote", "uk")), "india": (2, ("vote", "india")),
    "role": (4, ("chair",)), "overlap": (3, ("vote", "uk", "india")),
}
SYSTEM = (
    "Write one factual sentence for a Security Council record, no more than 35 words. Use only the supplied source. "
    "Attribute statements and actions precisely. Do not write a title, citation, quotation marks, or commentary. "
    "The record system attaches the source ID automatically."
)


def packet():
    return json.loads(TASK.read_text())


def requests():
    sources = {row["id"]: row["text"] for row in packet()["evidence"]}
    for name, prompt in FIELDS.items():
        body = {"task": prompt, "evidence": {name: sources[name]}}
        yield {"id": name, "evidence_ids": [name], "seen": [], "cap": CAP,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def locks():
    dependencies = (Path(__file__).resolve(), TASK, REFERENCES, TRAIN,
                    Path(archive.__file__), Path(archive.runner.__file__))
    return {str(p.relative_to(PROJECT)): archive.runner.digest(p) for p in dependencies}


def check():
    rubric = {r["id"]: r["weight"] for r in packet()["rubric"]}
    assert set(PUBLIC_UNITS) | set(RECEIPT_UNITS) == rubric.keys()
    assert set(PUBLIC_UNITS).isdisjoint(RECEIPT_UNITS)
    assert len(PUBLIC.split()) + MAX_WORDS * len(FIELDS) <= RECORD_WORDS
    refs = json.loads(REFERENCES.read_text())
    assert len(refs["unbench"]["author_test_rows"]) == 15
    assert all(not scan["matches"] for scan in refs["unsc_bench"]["scans"].values())
    return {"calls": len(FIELDS), "public_words": len(PUBLIC.split()),
            "public_points": sum(rubric[unit] for unit in PUBLIC_UNITS), "sha256": locks()}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def replay(directory, verify_tokens=False):
    with patch.multiple(archive, locks=locks, requests=requests, FAMILY=FAMILY, CAP=CAP):
        return archive.replay(directory, verify_tokens)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("--model", type=Path)
    cli.add_argument("--directory", type=Path, default=EVIDENCE / FAMILY)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), indent=2))
    elif args.mode == "run":
        if args.model is None:
            cli.error("run requires --model")
        check()
        with patch.multiple(archive.runner, episode=episode, locks=locks):
            archive.runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory, verify_tokens=True), indent=2, ensure_ascii=False))
