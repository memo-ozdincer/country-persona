"""Matched historical-record episode on the Iraq mandate renewal."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1] / "benchmark-kit" / "validity-audit"
sys.path.insert(0, str(KIT))
import source_record_run as runner
import source_record_sudan as single_replay

PACK = HERE / "case.json"
ARMS = ("pooled_solo", "independent_drafts", "interactive")


def locks():
    files = (PACK, Path(__file__).resolve(), Path(runner.__file__), Path(single_replay.__file__),
             HERE.parent / "references.json")
    return {path.name: runner.digest(path) for path in files}


def episode(generate):
    case = json.loads(PACK.read_text())
    name = case["family"]
    public = case["public"]
    roles = list(case["roles"])
    views = [{**public, **case["roles"][role]} for role in roles]
    pooled = {key: text for view in views for key, text in view.items()}

    def request(label, actor, evidence, history, cap, task):
        prompt = {"task": task, "evidence": evidence, "working_notes": [x["output"] for x in history]}
        return {"id": f"{name}/{label}", "evidence_ids": list(evidence), "seen": [x["id"] for x in history],
                "cap": cap, "messages": [
                    {"role": "system", "content": f"You are {actor}. The supplied evidence is the only factual authority. "
                     "Working notes are provisional and may be factually wrong."},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}]}

    opening = "Record the most important findings in your assigned area. Use two short bullets and bracketed source IDs."
    common = [request(f"common/opening_{j}", f"the {role} analyst", views[j], [], 112, opening)
              for j, role in enumerate(roles)]
    solo = [request(f"pooled_solo/opening_{j}", "a single historical analyst", pooled, [], 112,
                    f"Focus this pass on the {role} area. {opening}") for j, role in enumerate(roles)]
    openings = generate(common + solo)
    revise = ("Revise your focused contribution as two short bullets with bracketed source IDs. "
              "Preserve important qualifications and correct errors. Note a cross-cutting distinction only when source-supported.")
    revisions = []
    for arm in ARMS:
        for j, role in enumerate(roles):
            own, other = solo if arm == "pooled_solo" else common, 1 - j
            history = [openings[own[j]["id"]]]
            if arm != "independent_drafts":
                history.append(openings[own[other]["id"]])
            actor = "a single historical analyst" if arm == "pooled_solo" else f"the {role} analyst"
            revisions.append(request(f"{arm}/revision_{j}", actor, pooled if arm == "pooled_solo" else views[j],
                                     history, 112, f"Focus on the {role} area. {revise}"))
    revised = generate(revisions)
    final_task = (
        "Write the retrospective Council record in no more than 175 words. Cover the disposition, the existing "
        "mission mandate and its qualifications, the independent review (including consultation and assessment scope), "
        "the separate recurring reporting obligation, and what the record says about national explanations of vote. "
        "Cite each factual sentence with bracketed source IDs, and check the working notes against the source packet. "
        "Use only the supplied evidence. Write the record itself."
    )
    finals = generate([request(f"{arm}/chair", "the neutral Council record writer", pooled,
                               [revised[f"{name}/{arm}/revision_{j}"] for j in range(len(roles))],
                               240, final_task) for arm in ARMS])
    return [{"family": name, "openings": openings, "revisions": revised, "final": finals}]


def preflight():
    def generate(batch):
        return {row["id"]: {**row, "output": row["id"]} for row in batch}
    result, = episode(generate)
    name = result["family"]
    revisions = result["revisions"]
    for j in range(2):
        independent = revisions[f"{name}/independent_drafts/revision_{j}"]
        interactive = revisions[f"{name}/interactive/revision_{j}"]
        assert independent["seen"] == interactive["seen"][:1] and len(interactive["seen"]) == 2
        assert independent["evidence_ids"] == interactive["evidence_ids"]
    assert len({tuple(r["evidence_ids"]) for r in result["final"].values()}) == 1
    assert sum(len(rows) for key, rows in result.items() if key != "family") == 13
    references = json.loads((HERE.parent / "references.json").read_text())["families"][name]
    assert set(references["prediction_ref_only"].values()) == {"Y"}
    assert len(references["prediction_ref_only"]) == 15
    assert 4 * 112 + 240 == 688
    return {"unique_calls": 13, "calls_per_arm": 5, "output_ceiling_per_arm": 688}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("preflight", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "preflight":
        print(json.dumps(preflight(), indent=2))
    elif args.mode == "run":
        preflight()
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(args.model, args.directory)
    else:
        with patch.object(single_replay, "episode", episode), patch.object(single_replay, "locks", locks):
            print(json.dumps(single_replay.replay(args.directory), indent=2))
