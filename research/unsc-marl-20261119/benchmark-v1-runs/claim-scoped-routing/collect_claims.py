"""Run the same first-token collector on explicit source-claim questions."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
SOURCE = RUNS / "reform-2553-transfer/text-reply-transfer"
AFGHAN = RUNS / "afghanistan-2721-source-contrast/case.json"
OUT = HERE / "evidence"
sys.path.insert(0, str(SOURCE))
import text_study as prior

collector = prior.collector
HYPOTHESES = {
    "reform": "The first speaker objects that too little time was allowed to negotiate the current draft.",
    "afghanistan": "The first speaker makes its own support for appointing an envoy conditional on agreement from the de facto Afghan authorities.",
}
SYSTEM = (
    "Decide whether the first message supports the exact claim about its speaker. "
    "Check the speaker's own stated position, the specified action or draft, and whether the message "
    "affirms the claim. Reported speech, future proposals, objections to other actions, and mere mention "
    "of relevant terms do not establish the claim. A directly stated paraphrase does establish it. "
    "With insufficient evidence, choose unsupported. Return only the decision letter."
)


def read(path):
    return json.loads(path.read_text())


def fixtures():
    reform = {key: {"family": "reform", "text": row["text"], "supported": row["complements"]}
              for key, row in prior.cases().items()}
    target = {f"afg-{row['id']}": row | {"family": "afghanistan"}
              for row in read(HERE / "afghanistan-controls.json")}
    assert len(reform) == 15 and len(target) == 8
    return reform | target


def plan():
    previous = prior.locked()
    files = (Path(__file__), HERE / "protocol.md", HERE / "afghanistan-controls.json", AFGHAN,
             SOURCE / "plan.json", SOURCE / "results.json", SOURCE / "text_study.py", SOURCE / "readout.py")
    return {
        "pins": {**previous["pins"], **{str(path.relative_to(RUNS.parent)): collector.sha(path) for path in files}},
        "checkpoint_index_sha256": previous["checkpoint_index_sha256"],
        "requests": [
            prior.base.earlier.request(f"{key}/{suffix}", 2, SYSTEM, {
                "first_message": row["text"], "claim": HYPOTHESES[row["family"]],
                "responses": {letter: "supported" if action == "process" else "unsupported"
                              for letter, action in mapping.items()},
            }) for key, row in fixtures().items() for suffix, mapping in prior.MAPPINGS.items()
        ],
    }


def act(mode):
    locked = plan()
    if mode == "plan":
        return locked
    assert locked == read(HERE / "plan.json")
    original_run = collector.run

    def track_run(directory):
        dockets = {"reform-2553": prior.previous.CASE, "afghanistan-2721": read(AFGHAN)}
        with patch.object(collector, "roster", return_value=dockets):
            return original_run(directory)

    with patch.object(prior, "HERE", HERE), patch.object(prior, "OUT", OUT), patch.object(
        prior, "locked", return_value=locked
    ), patch.object(collector, "run", side_effect=track_run):
        return {"run": prior.run, "verify": prior.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    args = parser.parse_args()
    output = act(args.mode)
    if args.mode != "run":
        print(json.dumps(output, ensure_ascii=False, indent=2))
