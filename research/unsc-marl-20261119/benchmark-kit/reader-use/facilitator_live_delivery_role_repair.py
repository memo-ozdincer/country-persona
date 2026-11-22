"""Retest the two failed Myanmar role queries with explicit national and procedural capacities."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_live_delivery as prior

FAMILY = "facilitator-live-delivery-role-repair"
ROLE_QUERY = (
    "For India, give the Council President's procedural actions calling and announcing the vote, "
    "the switch to speaking as India's national representative, and the return to the presidency."
)


def requests():
    for row in prior.decode_requests():
        if row["id"].startswith("myanmar-") and row["id"].endswith("/query/3"):
            payload = json.loads(row["messages"][-1]["content"])
            yield prior.prompt(row["id"], row["cap"], prior.DECODER, payload | {"question": ROLE_QUERY})


def pins():
    root = prior.HERE.parents[1]
    paths = (Path(__file__).resolve(), Path(prior.__file__), Path(prior.RUNNER.__file__),
             prior.ACTION_FIT, prior.EVIDENCE / "launch.json", prior.EVIDENCE / "complete.json",
             prior.EVIDENCE / "transcript.jsonl")
    return {str(p.relative_to(root)): prior.RUNNER.digest(p) for p in paths}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def verify(directory):
    runner = prior.common.reused.previous.prior
    with patch.multiple(runner, local=requests, audits=lambda rows: (), syntheses=lambda rows: (),
                        pins=pins, FAMILY=FAMILY):
        return runner.read(directory)


def score(directory):
    updated = verify(directory)
    original = prior.verify(prior.EVIDENCE)
    cases = {}
    for key in updated:
        episode_key = key.split("/")[0]
        cases[episode_key] = {
            "before": original[key]["output"], "before_heard": prior.heard(original, episode_key, 3),
            "after": updated[key]["output"], "after_heard": prior.heard(updated, episode_key, 3),
        }

    # Stress branch discovered after inspecting the failed decode.
    # The existing question menu remains identical because the private
    # inventory and transport state never enter the decoder view.
    learned = prior.policies("myanmar", "correlated_duplicates")["learned"]
    left, right, request, answer = learned
    li, ri = 2, 7
    mask = int(prior.ROUTE.BITS[left[li]])
    assert request[mask] == 3
    assert "myanmar-missing-role" in cases
    trial = {}
    bank, notes = prior.bank("myanmar")
    wire = {2: original["myanmar-missing-role/payload/2"], 3: original["myanmar-available-role/payload/3"]}
    for label in ("before", "after"):
        recovered = cases["myanmar-missing-role"][f"{label}_heard"]
        c = int(answer[ri, right[ri], recovered])
        assert prior.ROUTE.SEND[ri, c]
        delivered = wire[c]
        assert delivered["ended"] and delivered["output"] == notes[c]
        trial[label] = {"sent": c, **bank[int(mask | prior.ROUTE.BITS[c])]}
    return {"scope": "Post hoc wording repair with two actual decoder generations. Replay one additional simulated "
                     "inventory where the decoded wording changes the useful delivery, reusing exact archived payloads.",
            "question": ROLE_QUERY, "changed_queries": cases,
            "stress_branch": {"inventory": [li, ri], "opening_received": mask, "outcomes": trial}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "score"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "score":
        print(json.dumps(score(args.directory), indent=2, ensure_ascii=False))
    else:
        with patch.multiple(prior.RUNNER, episode=episode, locks=pins):
            prior.RUNNER.run(args.model, args.directory)
