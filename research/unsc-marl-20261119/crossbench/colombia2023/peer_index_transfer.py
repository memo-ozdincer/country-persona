"""Generate peer questions from a source index and test their effect on two other dockets."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import peer_question as base

HERE = base.HERE
runner = base.runner
CASES = {"colombia": HERE / "case.json", "unami": HERE.parent / "unami2023/case.json"}
FAMILY = "peer-index-transfer"
ARMS = ("unindexed", "indexed", "no_question")
# Meeting agenda entries identify subjects and source IDs. No source claim is included.
INDEX = {
    "colombia": {"A3": "Identity, represented delegation, conditions for verification, and Ethnic Chapter."},
    "unami": {"REVIEW": "Review responsibility, status, recipient, and timing.",
              "CONSULT": "Consultation participants and correspondence.",
              "SCOPE": "Review purposes and scope."},
}
LIMITS = {"colombia": 185, "unami": 175}


def read(path):
    return json.loads(path.read_text())


def fixtures():
    for family, path in CASES.items():
        case = read(path)
        first, second = case["roles"].values()
        public = dict(case["public"])
        vote = public.pop("VOTE")
        assert second.keys() == INDEX[family].keys()
        yield family, vote, public, first, second


def open_note(family, vote, evidence):
    prompt = ("Draft the first desk's documentary note in at most 84 words. Preserve the institutional actor, "
              "what was decided or requested, and material conditions. Cite bracketed source IDs from the provided cards.")
    return base.request(family, "common", "open", 132, prompt, "the first archival desk", vote, evidence, ())


def ask(family, arm, vote, opening):
    prompt = ("Write a single precise question for the second desk. Ask it to check a material point it is positioned "
              "to answer using its own evidence, so the final record can preserve the correct actor, scope, or qualification. "
              "The index, if supplied, names topics rather than their answers. Do not propose the answer. End after the question.")
    row = base.request(family, arm, "question", 74, prompt, "the first archival desk", vote, {}, (opening,))
    user = row["messages"][-1]
    content = json.loads(user["content"])
    content["recipient_source_index"] = INDEX[family] if arm == "indexed" else {}
    user["content"] = json.dumps(content, ensure_ascii=False)
    return row


def reply(family, arm, vote, evidence, incoming):
    prompt = ("Draft the second desk's evidence note in at most 82 words. Preserve the actor, scope and qualifications. "
              "If you see a question, answer it using only your own documentary cards and include other material the final record needs. "
              "If your cards cannot answer it, record that limitation and report the relevant information they do establish. Cite bracketed source IDs.")
    return base.request(family, arm, "reply", 128, prompt, "the second archival desk", vote, evidence, incoming)


def chair(family, arm, vote, public, opening, answer):
    prompt = (f"Write a retrospective Security Council record supplement in at most {LIMITS[family]} words. "
              "The vote is already recorded. Use only the sourced working notes and supplied public documentary cards. "
              "Preserve each distinct decision and responsibility, including the authorized scope, material deadlines, "
              "conditions, recipients and institutional or national capacity where supported. Cite source IDs in brackets. "
              "Do not invent unavailable details. Preserve a shared position when the sources support one.")
    return base.request(family, arm, "final", 277, prompt, "the neutral archival chair", vote, public, (opening, answer))


def episode(generate):
    cases = list(fixtures())
    opening = generate([open_note(family, vote, a) for family, vote, _, a, _ in cases])
    questions = generate([ask(family, arm, vote, opening[f"{family}/common/open"])
                          for family, vote, *_ in cases for arm in ARMS[:2]])
    replies = generate([reply(family, arm, vote, b, (questions[f"{family}/{arm}/question"],)
                              if arm != "no_question" else ())
                        for family, vote, _, _, b in cases for arm in ARMS])
    finals = generate([chair(family, arm, vote, public, opening[f"{family}/common/open"],
                             replies[f"{family}/{arm}/reply"])
                       for family, vote, public, *_ in cases for arm in ARMS])
    return [{"family": FAMILY, "opening": opening, "questions": questions, "replies": replies, "final": finals}]


def locks():
    paths = (Path(__file__), Path(base.__file__), Path(runner.__file__), *CASES.values())
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in paths}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = (read(directory / name) for name in ("launch.json", "complete.json"))
    trace, finals = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(trace)
    assert finish["final_records_sha256"] == runner.digest(finals)
    raw = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    used = set()
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")

    def restore(requests):
        for request in requests:
            key = request["id"]
            row = raw[key]
            assert key not in used and all(row[k] == v for k, v in request.items())
            used.add(key)
            assert runner.encode(tok, request) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= request["cap"] and eos not in ids[:-1]
            assert row["ended"] == (ids[-1] == eos) and tok.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return {r["id"]: raw[r["id"]] for r in requests}

    expected, = episode(restore)
    assert set(raw) == used and len(used) == finish["records"] == 18
    assert read(finals) == {FAMILY: {key: row["output"] for key, row in expected["final"].items()}}
    return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        episode(base.mock)
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"exact_transcript_rows": len(replay(args.directory))}, indent=2))
