"""Render an extractive, source-limited comparison for this benchmark packet."""
import json
from pathlib import Path

import numpy as np

import prior_blind
import routing

HERE = routing.HERE
# Labels and glue are docket-specific. The fact-bearing slip sentence and the
# optional backup are copied from the allowed packet.
SLIP = {
    "amendment_775": ("S/2023/775. ", "It fell short of the vote threshold."),
    "amendment_776": ("S/2023/776. ", "It fell short of the vote threshold."),
    "draft_aid": ("Brazil’s proposed aid provisions. ", "The proposed provisions remained draft language because the Security Council vote did not adopt the instrument."),
    "veto_explanation": ("", "Review the explanation of the United States' negative vote on the main draft."),
}


def base(focus):
    title, stop = SLIP[focus["id"]]
    slip = focus["requester_card"]
    assert slip.count(stop) == 1
    if focus["id"].startswith("amendment_"):
        contents = slip.removeprefix(f"Review {focus['id'].replace('amendment_', 'S/2023/')}. ")
        return title + contents[:contents.index(stop) + len(stop)]
    if focus["id"] == "veto_explanation":
        return "Explanation of the United States' negative vote on the main draft."
    return title + stop


def render():
    return {
        f"{focus['id']}/{mode}": " ".join([base(focus), focus["backup"]] if mode == "matched" else [base(focus)])
        for focus in routing.load()["focuses"] for mode in ("slip", "matched")
    }


def decide(prior, tables, points):
    q_loss, r_loss, q_cost, r_cost = routing.config()
    mass = routing.masses(prior, q_loss) * (points[:, 1] - points[:, 0])
    costs = q_cost * (routing.REQUESTS @ prior.sum(axis=1)) + r_cost
    success = np.einsum("eqri,tqri->et", mass, np.eye(4)[tables])
    base = points[:, 0] @ prior.sum(axis=1)
    return base + (1 - r_loss) * success - costs[:, None]


def given(prior, policy, points):
    requester, receiver = map(np.asarray, policy)
    request_row, = np.flatnonzero(np.all(routing.REQUESTS == requester, axis=1))
    return float(decide(prior, receiver.T[None, :, :], points)[request_row, 0])


def evaluate():
    rendered = render()
    review_path = HERE / "compiled-review.json"
    review = json.loads(review_path.read_text())
    focus_ids = [focus["id"] for focus in routing.load()["focuses"]]
    assert rendered.keys() == review["rows"].keys()
    scores = {}
    for focus in routing.load()["focuses"]:
        for mode in ("slip", "matched"):
            name = f"{focus['id']}/{mode}"
            body, label = rendered[name], review["rows"][name]
            assert label["guard"] == "clear" and label["reason"]
            assert len(body.split()) <= 85
            for index, claim in label["met"].items():
                assert claim["record"] and claim["record"] in body
                if index == "0":
                    assert claim["source"] in focus["requester_card"]
                else:
                    assert mode == "matched" and index in "1234" and claim["source"] in focus["backup"]
            scores[name] = 35 + 7 * len(label["met"])
    points = np.asarray([[scores[f"{focus}/{receipt}"] for receipt in ("slip", "matched")] for focus in focus_ids])
    fitted = json.loads((HERE / "routing-fit.json").read_text())
    baseline = json.loads((HERE / "routing-results.json").read_text())["results"]
    compiled = []
    for name, prior in routing.priors():
        script = baseline[fitted["training_prior"]]["policies"]["independent_priority_by_request"]
        reference = (script["sender"], script["receiver"])
        targets = {key: float(decide(prior, table, points).max()) for key, table in prior_blind.menus().items()}
        assert targets["flexible"] >= targets["rank"] - 1e-8
        compiled.append((name, {"learned": given(prior, fitted["learned_policy"], points),
                                "training_rank_script": given(prior, reference, points),
                                "prior_informed_record_ceilings": targets}))
    return {"scope": review["scope"], "task_sha256": routing.digest(HERE / "task.json"),
            "review_sha256": routing.digest(review_path), "compiler_sha256": routing.digest(Path(__file__)),
            "rendered": rendered, "scores_by_focus_and_receipt": points.tolist(), "replays": dict(compiled)}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
