"""Replay peer-question transcripts and score source fidelity and evidence uptake."""
import argparse
import json
from pathlib import Path
import re

import peer_question as trial


def read(path):
    return json.loads(path.read_text())


def replay(directory):
    from transformers import AutoTokenizer

    launch, end = (read(directory / name) for name in ("launch.json", "complete.json"))
    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    expected = trial.locks()
    original = directory / "launch-source.py"
    if original.is_file():
        expected["peer_question.py"] = trial.runner.digest(original)
    assert launch["sha256"] == expected
    assert end["transcript_sha256"] == trial.runner.digest(trace)
    assert end["final_records_sha256"] == trial.runner.digest(final)
    raw = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    used = set()

    def restore(batch):
        returned = {}
        for wanted in batch:
            key = wanted["id"]
            assert key not in used
            used.add(key)
            row = raw[key]
            assert all(row[k] == v for k, v in wanted.items())
            assert trial.runner.encode(tok, wanted) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= wanted["cap"] and eos not in ids[:-1] and (ids[-1] == eos) == row["ended"]
            assert row["output"] == tok.decode(ids, skip_special_tokens=True).strip()
            returned[key] = row
        return returned

    episode, = trial.episode(restore)
    assert set(raw) == used and len(used) == end["records"] == 18
    assert read(final) == {trial.FAMILY: {k: row["output"] for k, row in episode["final"].items()}}
    return raw


def verified_spans(mapping, text, keys):
    assert mapping.keys() <= keys
    assert all(spans and all(s and s in text for s in spans) for spans in mapping.values())
    return mapping


def score(directory):
    raw = replay(directory)
    reviews = read(directory / "annotations.json")
    assert reviews["transcript_sha256"] == trial.runner.digest(directory / "transcript.jsonl")
    rules = {
        "unifil": {row["id"] for row in read(trial.UNIFIL)["rubric"]},
        "haiti": set(read(trial.HAITI)["rules"]),
    }
    outcomes = {}
    for family, vote, public, national in trial.fixtures():
        authored = {"procedure", "disposition"} if family == "unifil" else {"procedure"}
        review = reviews["families"][family]
        ideas = set(review["idea_descriptions"])
        working = review["working"]
        expected = {r for r in raw if r.startswith(family + "/") and not r.endswith("/final")}
        assert set(working) == expected
        for key, witnesses in working.items():
            verified_spans(witnesses, raw[key]["output"], ideas)
        for turn, issues in review["working_issues"].items():
            assert turn in working and all(span in raw[turn]["output"] and note for span, note in issues)
        supported = {}
        for arm in trial.ARMS:
            final = raw[f"{family}/{arm}/final"]
            observed = review["finals"][arm]
            met = verified_spans(observed["met"], final["output"], rules[family] - authored)
            final_ideas = verified_spans(observed["retained_ideas"], final["output"], ideas)
            assert all(s and s in final["output"] and note for s, note in observed["issues"])
            cite_groups = re.findall(r"\[([A-Za-z0-9, ]+)\]", final["output"])
            cited = {part.strip().casefold() for group in cite_groups for part in group.split(",")}
            expected_ids = {k.casefold() for k in public.keys() | national.keys()}
            missing_ids = expected_ids - cited
            unknown_ids = cited - expected_ids - {"vote"}
            note_ids = final["seen"]
            # Novelty here is relative to the first working note, not a claim of influence.
            reply_novel = sorted(working[note_ids[-1]].keys() - working[note_ids[0]].keys()) if note_ids else []
            rows = [raw[key] for key in note_ids] + [final]
            supported[arm] = {
                "record": vote + "\n\n" + final["output"],
                "points": 7 * (len(met) + len(authored)), "met": met, "fixed_vote_criteria": sorted(authored),
                "issues": observed["issues"], "complete": final["ended"],
                "missing_source_ids": sorted(missing_ids), "unknown_source_ids": sorted(unknown_ids),
                "within_word_budget": len(final["output"].split()) <= 140,
                "strict": (set(met) | authored == rules[family] and not observed["issues"]
                           and final["ended"] and not missing_ids and not unknown_ids and len(final["output"].split()) <= 140),
                "working_turns": len(note_ids), "writer_turns": 1,
                "working_unique_ideas": {key: len(working[key]) for key in note_ids},
                "second_note_new_ideas": reply_novel,
                "retained_ideas": final_ideas, "new_second_note_ideas_retained": sorted(set(reply_novel) & final_ideas.keys()),
                "input_tokens": sum(len(row["input_ids"]) for row in rows),
                "output_tokens": sum(len(row["output_ids"]) for row in rows),
                "first_note_peer_hop_tokens": len(rows[0]["output_ids"]) if arm == "interactive" else 0,
            }

        answer = review["question"]
        assert answer["span"] in raw[f"{family}/shared/open"]["output"]
        asked = set(answer["asks_about"])
        assert asked <= ideas and answer["span"]
        assert answer["answerable_from_second_source"] == bool(asked)
        assert answer["reason"]
        independent = supported["independent"]
        interactive = supported["interactive"]
        both = {arm: set(supported[arm]["new_second_note_ideas_retained"]) for arm in ("independent", "interactive")}
        i = set(interactive["second_note_new_ideas"])
        c = set(independent["second_note_new_ideas"])
        outcomes[family] = {"criteria": supported, "working_witnesses": working,
                            "question": answer, "working_issues": review["working_issues"],
                            "interactive_only_answered_ideas": sorted((i - c) & asked),
                            "interactive_only_answered_and_retained": sorted((i - c) & asked & both["interactive"]),
                            "independent_only_new_ideas_retained": sorted(both["independent"] - both["interactive"]),
                            "jointly_retained_new_ideas": sorted(both["independent"] & both["interactive"]),
                            "interactive_final_points_delta": interactive["points"] - independent["points"]}
    return {"review": reviews["scope"], "families": outcomes}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--check-only", action="store_true")
    a = cli.parse_args()
    print(json.dumps({"exact_transcript_rows": len(replay(a.directory))} if a.check_only else score(a.directory),
                     ensure_ascii=False, indent=2))
